import streamlit as st
import pandas as pd
import sqlite3
jp = df[df["code"] == "JP_GOLD"]
global_gold = df[df["code"] == "GOLD"]

if not jp.empty and not global_gold.empty:
    jp_price = jp.iloc[-1]["close"]
    gl_price = global_gold.iloc[-1]["close"]

    diff = (jp_price / gl_price) - 1

    st.metric("国内金", jp_price)
    st.metric("乖離率", f"{diff*100:.2f}%")

st.set_page_config(layout="wide")
st.title("📊 投資ダッシュボード")

conn = sqlite3.connect("data.db")
df = pd.read_sql("SELECT * FROM market", conn)

names = df["name"].unique()
selected = st.selectbox("銘柄選択", names)
filtered = df[df["name"] == selected]

latest = filtered.iloc[-1]
st.metric("現在価格", round(latest["close"],2), f"{round(latest['change'],2)}%")

st.line_chart(filtered.set_index("date")["close"])
st.dataframe(filtered.sort_values("date", ascending=False))

conn.close()
