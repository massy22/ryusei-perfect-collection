import os
import json
import datetime
import hashlib
import requests
import frontmatter
import re
from google import genai
from google.genai import types
from pathlib import Path

# 設定 (Configuration)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

DEFAULT_QUERIES = [
    "流星のロックマン パーフェクトコレクション 公式サイト 更新",
    "流星のロックマン パーフェクトコレクション カプコン プレスリリース",
    "流星のロックマン パーフェクトコレクション メンテナンスのお知らせ",
    "流星のロックマン パーフェクトコレクション アップデート パッチノート"
]

MOCK_SEARCH_RESULTS = {
    "items": [
        {
            "title": "流星のロックマン パーフェクトコレクション 発売決定！",
            "snippet": "2025年12月25日発売。予約特典としてオリジナルサウンドトラックが付属。",
            "link": "https://example.com/news/1"
        },
        {
            "title": "DS版との違いまとめ",
            "snippet": "画質が向上し、通信対戦のラグが解消されています。新シナリオも追加。",
            "link": "https://example.com/system/diff"
        }
    ]
}

def search_google(query):
    if not GOOGLE_SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        print(f"モックモードで確認中: {query}")
        return MOCK_SEARCH_RESULTS

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_SEARCH_API_KEY,
        "cx": SEARCH_ENGINE_ID,
        "q": f"{query} AND (site:capcom.co.jp OR site:twitter.com OR site:youtube.com OR site:prtimes.jp)",
        "num": 5
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"検索APIエラー: {e}")
        return {}

def clean_text_from_markdown(text):
    """
    Strips markdown code blocks (e.g. ```json ... ```) from the text.
    """
    pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()

def generate_content(search_data):
    if not GEMINI_API_KEY:
        print("Gemini APIキーが見つかりません。モック記事を使用します。")
        # モックコンテンツを返す
        return [
            {
                "title": "【予約特典】オリジナルサウンドトラック情報",
                "category": "product",
                "tags": ["特典", "OST"],
                "body": "予約特典として豪華サウンドトラックが付属します。\n\n※本記事はAIによって自動収集された情報です。正確な情報は公式サイトをご確認ください。",
                "source": "https://example.com/news/1"
            }
        ]

    # Optimize input tokens: Keep only essential fields
    minified_items = []
    if 'items' in search_data:
        for item in search_data['items']:
            minified_items.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", "")
            })
    
    # Use minified data for prompt
    prompt_data = {"items": minified_items}

    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Internal Database: {json.dumps(prompt_data, ensure_ascii=False)}

    Analyze the search results above and extract distinct OFFICIAL ANNOUNCEMENTS about "Ryusei no Rockman Perfect Collection".
    For each distinct topic, create a JSON object with:
    - title: A specific, factual title (e.g., "【公式】2025年12月25日 更新情報").
    - category: One of "news", "product", "system".
    - tags: A list of relevant technical tags (no subjective tags).
    - body: A concise, factual summary in Japanese. 
      - Use bullet points for readability.
      - REMOVE all emotional language (e.g., "嬉しい", "待望の", "なんと"). 
      - Focus ONLY on facts: dates, version numbers, items, prices.
    - source: The URL of the official source.

    Rule:
    - IGNORE speculation, rumors, and third-party blogs.
    - If the info is about pre-order bonuses, goods, price, release date -> "product"
    - If the info is about game differences, new features, specs -> "system"
    - Otherwise -> "news"
    - Must include the disclaimer at the end of body: "\n\n※本記事はAIによって自動収集された情報です。正確な情報は公式サイトをご確認ください。"

    Output a JSON list of objects.
    """
    
    try:
        # Using gemma-3-27b-it for significantly higher daily quota (14.4K RPD)
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt
            # Note: JSON mode is not fully supported on gemma-3-27b-it via API yet,
            # so we rely on the prompt to generate valid JSON.
        )
        text = clean_text_from_markdown(response.text)
        return json.loads(text)
    except Exception as e:
        print(f"Gemini生成エラー: {e}")
        return []

def is_duplicate_title(slug):
    """
    Checks if a file with the same slug exists in the content directory,
    ignoring the date prefix.
    """
    content_dir = Path("content")
    if not content_dir.exists():
        return False
        
    # Recursive search for any file ending with "-{slug}.md"
    for path in content_dir.rglob(f"*-{slug}.md"):
        return True
    return False

def save_article(article, date_obj=None):
    if date_obj is None:
        date_obj = datetime.date.today()
        
    slug = hashlib.md5(article['title'].encode()).hexdigest()[:10]
    
    # Check for duplicates (same title hash)
    if is_duplicate_title(slug):
        print(f"重複記事をスキップしました (Title: {article['title']})")
        return

    date_str = date_obj.isoformat()
    filename = f"{date_str}-{slug}.md"
    
    category = article.get('category', 'news').lower()
    if category not in ['news', 'product', 'system']:
        category = 'news'
        
    directory = Path(f"content/{category}")
    directory.mkdir(parents=True, exist_ok=True)
    
    filepath = directory / filename
    
    if filepath.exists():
        print(f"既存ファイルをスキップしました: {filepath}")
        return
    
    # Check if a file with the same slug exists (even if date is different)
    # Double check logic (redundant but safe)
    if is_duplicate_title(slug):
         print(f"重複アセットをスキップ: {slug}")
         return

    # タイムゾーン等の調整のため datetime オブジェクトに変換
    if isinstance(date_obj, datetime.date) and not isinstance(date_obj, datetime.datetime):
         date_val = datetime.datetime.combine(date_obj, datetime.datetime.min.time())
    else:
         date_val = date_obj

    content = frontmatter.Post(
        article['body'] + f"\n\n[情報元]({article.get('source', '#')})",
        title=article['title'],
        date=date_val,
        categories=[category],
        tags=article.get('tags', [])
    )
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(content))
    print(f"作成完了: {filepath}")

def run_collection(target_date=None, queries=None):
    if queries is None:
        queries = DEFAULT_QUERIES
        
    print(f"収集開始: 日付={target_date}, クエリ数={len(queries)}")
    all_results = {"items": []}
    
    for q in queries:
        res = search_google(q)
        if res and 'items' in res:
            all_results['items'].extend(res['items'])
            
    if not all_results['items']:
        print("検索結果がありませんでした。")
        return

    articles = generate_content(all_results)
    
    if not isinstance(articles, list):
       articles = [articles] if articles else []

    for article in articles:
        save_article(article, date_obj=target_date)
    
    print("完了しました。")

if __name__ == "__main__":
    # 直接実行時は今日の日付でデフォルトクエリを実行
    run_collection()
