import pandas as pd
import yfinance as yf
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup  # ←これも必要

# ✅ ✅ ここに関数を置く（超重要）
def get_japan_gold():
    url = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    tds = soup.find_all("td")

    for td in tds:
        text = td.text.replace(",", "").strip()
        if text.endswith("円") and text[:-1].isdigit():
            return float(text.replace("円", ""))

    return None


today = datetime.today().strftime("%Y-%m-%d")

df = pd.read_excel("tickers.xlsx")
conn = sqlite3.connect("data.db")

records = []

# --- 株取得 ---
for _, row in df.iterrows():
    ticker = row["code"]
    name = row["name"]

    stock = yf.Ticker(ticker)
    hist = stock.history(period="2d")

    if len(hist) >= 2:
        close = hist["Close"].iloc[-1]

        records.append({
            "date": today,
            "code": ticker,
            "name": name,
            "close": float(close),
            "change": 0
        })


# --- 世界金 ---
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


# ✅ ✅ ここで使う（関数より下）
jp_gold = get_japan_gold()

if jp_gold:
    records.append({
        "date": today,
        "code": "JP_GOLD",
        "name": "Gold_JP",
        "close": jp_gold,
        "change": 0
    })


# --- 保存 ---
pd.DataFrame(records).to_sql("market", conn, if_exists="append", index=False)

conn.close()
print("done")
