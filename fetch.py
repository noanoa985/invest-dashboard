import pandas as pd
import yfinance as yf
import sqlite3
from datetime import datetime
import requests
import os
from bs4 import BeautifulSoup
import re

# ------------------------------
# 国内金取得（安定版）
# ------------------------------
def get_japan_gold():
    url = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        rows = soup.find_all("tr")

        for row in rows:
            text = row.get_text()

            if "金" in text and "円" in text:
                match = re.search(r"([0-9,]+)円", text)
                if match:
                    return float(match.group(1).replace(",", ""))

    except:
        return None

    return None


# ------------------------------
# メイン処理
# ------------------------------
WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")
today = datetime.today().strftime("%Y-%m-%d")

df = pd.read_excel("tickers.xlsx")
conn = sqlite3.connect("data.db")

records = []

# ------------------------------
# 株価取得
# ------------------------------
for _, row in df.iterrows():
    ticker = row["code"]
    name = row["name"]

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")

        if len(hist) >= 2:
            close = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2]
            change = (close - prev) / prev * 100

            records.append({
                "date": today,
                "code": ticker,
                "name": name,
                "close": float(close),
                "change": float(change)
            })

            # 通知（±3%）
            if abs(change) >= 3 and WEBHOOK_URL:
                requests.post(WEBHOOK_URL, json={"text": f"{name} {change:.2f}%"})

    except:
        continue


# ------------------------------
# 世界金
# ------------------------------
try:
    gold = yf.Ticker("GC=F")
    gold_hist = gold.history(period="1d")

    if not gold_hist.empty:
        records.append({
            "date": today,
            "code": "GOLD",
            "name": "Gold",
            "close": float(gold_hist["Close"].iloc[-1]),
            "change": 0
        })
except:
    pass


# ------------------------------
# ✅ 国内金（ここが重要）
# ------------------------------
jp_gold = get_japan_gold()
print("JP_GOLD:", jp_gold)

if jp_gold:
    records.append({
        "date": today,
        "code": "JP_GOLD",
        "name": "Gold_JP",
        "close": jp_gold,
        "change": 0
    })


# ------------------------------
# 保存
# ------------------------------
if records:
    pd.DataFrame(records).to_sql("market", conn, if_exists="append", index=False)

conn.close()

print("done")
