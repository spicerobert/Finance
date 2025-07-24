"""
使用twse API抓取上市個股日成交資訊並計算夏普指數
https://openapi.twse.com.tw/#/%E8%AD%89%E5%88%B8%E4%BA%A4%E6%98%93/get_exchangeReport_STOCK_DAY_ALL
"""
import requests
import pandas as pd
import time

def 下載股價資訊(月份列表,股票代碼):
    all_data = []
    for date_str in 月份列表:
        url = f"https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date_str}&stockNo={股票代碼}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        data = response.json()

        if data["stat"] != "OK":
            print(f"{date_str[0:6]}抓取失敗")
            continue

        df = pd.DataFrame(data["data"], columns=data["fields"])

        # 處理收盤價
        df["收盤價"] = pd.to_numeric(df["收盤價"].str.replace(",", ""), errors="coerce")

        all_data.append(df[["日期", "收盤價"]])
        time.sleep(1)  # 避免請求過快

    return pd.concat(all_data).dropna().sort_values("日期").reset_index(drop=True)
    
def 民國轉西元(date_str):
    parts = date_str.split('/')
    parts[0] = str(int(parts[0]) + 1911)
    return '/'.join(parts)

df["日期"] = df["日期"].apply(民國轉西元)
df["日期"] = pd.to_datetime(df["日期"], format="%Y/%m/%d")

df




