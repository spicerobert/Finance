from flask import Flask, request,abort
import time
import requests
from linebot.v3.messaging import (Configuration,ApiClient,MessagingApi,ReplyMessageRequest,TextMessage,ApiException)
# Load configuration from config.json
import json
import os
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
CHANNEL_ACCESS_TOKEN = config.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = config.get("CHANNEL_SECRET")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 初始化 Flask 應用程式
app = Flask(__name__)
port = "3001"
# LINE Webhook 入口
@app.route("/", methods=['POST'])
def linebot():
    # 採用手動方式進行 X-Line-Signature 簽章驗證，確保訊息來源為 LINE 官方伺服器
    import hmac, hashlib, base64
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)
    else:
        # 取得使用者傳來的資料
        data = request.get_json()
        print(data)
        # 確保有事件，且事件類型是訊息，且訊息類型是文字
        if 'events' in data and data['events'] and \
           data['events'][0].get('type') == 'message' and \
           data['events'][0].get('message', {}).get('type') == 'text':        
            # 提取 replyToken
            reply_token = data['events'][0]['replyToken']
            # 提取 text(使用者輸入的股票代號)
            stock_codes = data["events"][0]["message"]["text"]
            # 執行查詢股價函式            
            retext = stockprice(stock_codes)
            # 建立一個與LINE API溝通的客戶端的臨時連線
            try:
                with ApiClient(configuration) as api_client:
                    # 建立一個專門用來處理「訊息」相關操作的物件
                    messaging_api = MessagingApi(api_client)
                    # 呼叫messaging_api物件的reply_message_with_http_info方法來發送訊息。這個方法需要一個ReplyMessageRequest物件作為參數
                    messaging_api.reply_message_with_http_info(
                        ReplyMessageRequest(reply_token=reply_token, messages=[TextMessage(text=retext)])
                    )
                return "OK", 200
            except ApiException as e:
                print(f"錯誤訊息: {e}\n")
                return "Error", 400

# 查詢股價進入點
def stockprice(stock_codes):
    codeno = f'tse_{stock_codes}.tw'
    timestamp = int(time.time() * 1000)
    api_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={codeno}&_={timestamp}"
    rate = requests.get(api_url)
    req = rate.json()
    stock_data = req['msgArray']

    # --- 取值邏輯 ---
    code = stock_data[0].get('c')
    name = stock_data[0].get('n')
    price = stock_data[0].get('z', '-')
    bid_price = stock_data[0].get('b', '_').split('_')[0]
    yesterday_price = stock_data[0].get('y', '-')
    source = ""
    vol = stock_data[0].get('v', 'N/A')
    # --- 價格取值邏輯 ---
    if price == '-':
        if bid_price and bid_price != '-':
            price = bid_price
            source = "(委買)"
        elif yesterday_price and yesterday_price != '-':
            price = yesterday_price
            source = "(昨收)"
    price_int = price[0:-2]                 #prince值為字串，所以取到倒數兩位數
    # --- 漲跌計算邏輯 ---
    change = "N/A"
    percentage = "N/A"
    updown = "N/A"
    if yesterday_price != '-' and price != '-':
        change_val = float(price) - float(yesterday_price)
        if change_val > 0:
            updown = "▲"
        elif change_val < 0:
            updown = "▼"
        elif change_val == 0:
            updown = "--"

        percentage_val = (change_val / float(yesterday_price)) * 100
        change = f"{change_val:+.2f}"
        percentage = f"{percentage_val:+.2f}%"

    quotes = {}
    quotes = {
        '股票代碼': code,
        '公司簡稱': stock_data[0].get('n', 'N/A'),
        '成交價': price,
        '來源': source,
        '成交量': stock_data[0].get('v', 'N/A'),
            }
    text = f"{name}\n最新成交價:{price_int}{source}\n{updown}漲跌:{change}＊漲跌幅:{percentage}\n成交量:{vol}"
    return text

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=port)
