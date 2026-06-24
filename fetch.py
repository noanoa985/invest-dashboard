import pandas as pd
import yfinance as yf
import sqlite3
from datetime import datetime
import requests
import os
import requests
from bs4 import BeautifulSoup

# 国内金
jp_gold = get_japan_gold()

if jp_gold:
    records.append({
        "date": today,
        "code": "JP_GOLD",
        "name": "Gold_JP",
        "close": jp_gold,
        "change": 0
    })

def get_japan_gold():
    url = "https://gold.tanaka.co.jp/commodity/souba/d-gold.php"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    prices = soup.find_all("td")

    for i, p in enumerate(prices):
        if "金" in p.text:
            try:
                price = prices[i+1].text.replace(",", "").replace("円","").strip()
                return float(price)
            except:
                return None

    return None

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK")

today = datetime.today().strftime("%Y-%m-%d")

df = pd.read_excel("tickers.xlsx")
conn = sqlite3.connect("data.db")
records = []

for _, row in df.iterrows():
    ticker = row["code"]
    name = row["name"]

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

        if abs(change) >= 3 and WEBHOOK_URL:
            requests.post(WEBHOOK_URL, json={"text": f"{name} {change:.2f}%"})

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

pd.DataFrame(records).to_sql("market", conn, if_exists="append", index=False)
conn.close()
print("done")
