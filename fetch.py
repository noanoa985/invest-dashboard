import pandas as pd
import yfinance as yf
import sqlite3
from datetime import datetime
import requests
import os

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
