import datetime
import time
from collector import run_collection

# 開始日と終了日 (2025-09-12 〜 2025-12-25)
START_DATE = datetime.date(2025, 9, 12)
END_DATE = datetime.date(2025, 12, 25)
INTERVAL_DAYS = 7

# クエリのバリエーション（公式情報を狙うキーワード）
QUERIES_ROTATION = [
    ["流星のロックマン パーフェクトコレクション 制作決定"],
    ["流星のロックマン パーフェクトコレクション 公式サイト公開"],
    ["流星のロックマン パーフェクトコレクション イーカプコン 限定版"],
    ["流星のロックマン パーフェクトコレクション 登場キャラクター"],
    ["流星のロックマン パーフェクトコレクション オンライン機能"],
    ["流星のロックマン パーフェクトコレクション サウンドトラック"],
    ["流星のロックマン パーフェクトコレクション 開発レター"],
    ["流星のロックマン パーフェクトコレクション PV公開"],
    ["流星のロックマン パーフェクトコレクション 画質比較"],
    ["流星のロックマン パーフェクトコレクション 発売日決定"]
]

def main():
    print(f"=== Backfill Start: {START_DATE} -> {END_DATE} (Every {INTERVAL_DAYS} days) ===")
    
    current_date = START_DATE
    idx = 0
    
    while current_date <= END_DATE:
        # APIレート制限対策 (TPM/RPM制限があるため60秒待機)
        if idx > 0:
           print("Waiting 60 seconds to respect API rate limits...")
           time.sleep(60)
            
        # クエリを選択（ローテーション）
        queries = QUERIES_ROTATION[idx % len(QUERIES_ROTATION)]
        
        print(f"Processing [{idx+1}]: {current_date} (Queries: {queries})")
        run_collection(target_date=current_date, queries=queries)
        
        # 次の日付へ
        current_date += datetime.timedelta(days=INTERVAL_DAYS)
        idx += 1
        
    print(f"=== Backfill Completed (Total {idx} runs) ===")

if __name__ == "__main__":
    main()
