import requests
from bs4 import BeautifulSoup

from flask import Flask, request,abort
from linebot.v3.messaging import (Configuration,ApiClient,MessagingApi,ReplyMessageRequest,TextMessage,ApiException)

import json
import os
# Load configuration from config.json
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
CHANNEL_ACCESS_TOKEN = config.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = config.get("CHANNEL_SECRET")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 初始化 Flask 應用程式
app = Flask(__name__)
port = "3001"

import hmac
import hashlib
import base64
# LINE linebot 入口
@app.route("/", methods=["POST"])
def linebot():
    """
    LINE Bot Webhook 主入口函數
    處理來自 LINE 官方伺服器的訊息事件

    主要功能：
    1. 驗證訊息來源安全性 (HMAC 簽章驗證)
    2. 解析使用者訊息內容
    3. 根據訊息內容路由到不同的處理分支
    4. 回傳適當的回應訊息

    Returns:
        tuple: (response_message, status_code)
    """
    # 採用 HMAC SHA256 手動驗證 X-Line-Signature 簽章
    # 確保訊息確實來自 LINE 官方伺服器，而非偽造請求
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash_ = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash_).decode():
        abort(400)  # 簽章驗證失敗，回傳 HTTP 400 錯誤

    # 將 JSON 格式的請求內容解析為 Python 字典
    data = request.get_json()
    print(data)  # 除錯用：輸出完整的請求資料

    # 資料驗證：確保請求包含有效的事件，且事件類型為文字訊息
    # LINE Webhook 可能包含多個事件，此處只處理第一個文字訊息事件
    if 'events' in data and data['events'] and \
       data['events'][0].get('type') == 'message' and \
       data['events'][0]['message'].get('type') == 'text':
        reply_token = data['events'][0]['replyToken']
        message = data['events'][0]['message']['text']

        # ===== 訊息處理主邏輯 =====
        try:
            result_text = 計算股價(message)
            # 設定訊息物件
            mes_return = {"type": "text", "text": result_text}
        except Exception as e:
            # 捕捉所有未預期的程式錯誤
            print(f"發生未預期錯誤: {e}")  # 輸出錯誤資訊到伺服器日誌
            # 設定錯誤訊息物件
            mes_return = {"type": "text", "text": f"發生未預期錯誤: {e}"}

        # ===== 訊息發送處理 =====
        # 使用統一的訊息發送邏輯，處理可能的 API 錯誤
        try:
            # 建立 API 客戶端連線
            with ApiClient(configuration) as api_client:
                api_instance = MessagingApi(api_client)
                # 提取訊息內容，如果沒有 "text" 鍵，使用預設錯誤訊息
                text_message = TextMessage(text=mes_return.get("text", "發生錯誤，無法取得訊息內容"))
                # 建立回覆訊息請求，包含 reply_token 和訊息內容
                reply_message_request = ReplyMessageRequest(reply_token=reply_token,messages=[text_message])
                # 發送訊息給 LINE 官方伺服器
                api_instance.reply_message(reply_message_request)
            # 成功發送訊息，回傳 HTTP 200 狀態碼
            return "OK", 200
        except ApiException as e:
            # LINE Bot API 發送失敗的異常處理
            print(f"發送訊息失敗: {e}")  # 輸出錯誤資訊到伺服器日誌
            # 回傳 HTTP 400 錯誤狀態碼
            return "Error", 400
    return "OK", 200

# 個人設定的目標殖利率
# 根據證交所統計, 台股整體殖利率自 2014 年至 2023 年 7 月近十年的平均為 3.94%, 而自 2018 年至 2023 年 7 月近五年的台股平均殖利率約 3.83%
# 用台灣銀行數位存款利率當最低標準
def 計算股價(stock_code, target_yield = 0.06, market_average_yield = 0.038, low_target_yield = 0.03):
    stock_data = stock_dividend(stock_code)
    if stock_data:
        # 計算平均股利
        average_dividend = stock_data["股價"] * stock_data["近5年平均現金殖利率"]
        # print(f"股票代號 {stock_code} 平均股利: {average_dividend:.2f} 元")
        
        # 計算便宜價、合理價、昂貴價
        cheap, fair, expensive = calculate_prices(average_dividend, target_yield, market_average_yield, low_target_yield)
        # 顯示價格
        # print(f"股票代號 {stock_code} 的便宜價 : {cheap :.2f} 元")
        # print(f"股票代號 {stock_code} 的合理價 : {fair :.2f} 元")
        # print(f"股票代號 {stock_code} 的昂貴價 : {expensive :.2f} 元")
        return f"股票代號 {stock_code} 的便宜價 : {cheap :.2f} 元, 合理價 : {fair :.2f} 元, 昂貴價 : {expensive :.2f} 元"    
    else:
        msg = f"{stock_code}無法獲取股利資料，請檢查股票代號或網站連接"
        print(msg)

# 從Yahoo股市 url 取得股票股利資料
def stock_dividend(stock_code):
    url = f"https://tw.stock.yahoo.com/quote/{stock_code}/dividend"
    # 發送 GET 請求獲取網頁內容
    response = requests.get(url)
    # Http Status Code 200 OK
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')        
        # 提取股價，根據 Yahoo 股市網頁結構，上漲、下跌、平盤股價在不同的 class 中
        stock_price_up = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-up)'})
        stock_price_down = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-down)'})
        stock_price_flat = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c)'})        
        # 根據不同的狀態來抓取股價
        if stock_price_up:
            stock_price = float(stock_price_up.text.strip().replace(',', ''))  # 上漲
        elif stock_price_down:
            stock_price = float(stock_price_down.text.strip().replace(',', ''))  # 下跌
        elif stock_price_flat:
            stock_price = float(stock_price_flat.text.strip().replace(',', ''))  # 平盤
        else:
            print(f"{stock_code}未找到股價")
            return None        
        # 找到包含股利資料的 <p> 標籤
        dividend_section = soup.find('p', {'class' : 'Mb(20px) Mb(12px)--mobile Fz(16px) Fz(18px)--mobile C($c-primary-text)'})        
        if dividend_section:
            # 提取股利資料
            # 找到所有 <span class="Fw(b)"> 標籤，這些標籤包含我們需要的數據
            data_spans = dividend_section.find_all('span', {'class' : 'Fw(b)'})            
            # 檢查是否找到足夠的數據
            if len(data_spans) >= 4:
                # 連續發放股利年數
                years_of_dividend = data_spans[0].text.strip()
                # 合計發放股利金額
                total_dividend = data_spans[1].text.strip()
                # 近 5 年平均現金殖利率
                average_dividend_yield = float(data_spans[3].text.strip().replace('%', '')) / 100  # 轉換為小數                
                # 顯示抓取到的資料
                print(f"股票代號: {stock_code}", f"股價: {stock_price}")
                print(f"連續發放股利年數: {years_of_dividend}")
                print(f"合計發放股利金額: {total_dividend} 元")
                print(f"近 5 年平均現金殖利率: {average_dividend_yield}")
                return {
                    "股票代號": stock_code,
                    "股價": stock_price,
                    "連續發放股利年數": years_of_dividend,
                    "合計發放股利金額": total_dividend,
                    "近5年平均現金殖利率": average_dividend_yield
                }
            else:
                print(f"{stock_code}未能找到完整的股利資料")
                return None
        else:
            print(f"{stock_code}未找到股利資料區域")
            return None
    else:
        print(f"{stock_code}無法獲取網頁內容，請檢查網站連接")
        return None

# 計算便宜價、合理價、昂貴價
def calculate_prices(dividend_per_share, target_yield, market_average_yield, low_target_yield):
    
    cheap_price = dividend_per_share / target_yield
    fair_price = dividend_per_share / market_average_yield
    expensive_price = dividend_per_share / low_target_yield    
    return cheap_price, fair_price, expensive_price

# print(計算股價("2881"))  # 台積電
# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)
