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
            user_input = data["events"][0]["message"]["text"]
            # 將使用者輸入的字串用空格、逗號或換行符分割成股票代碼列表
            import re
            stock_codes_list = re.split(r'[\s,，\n]+', user_input)
            # 執行查詢股價函式            
            retext = stockprice(stock_codes_list)
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
def stockprice(stock_codes_list):
    # 過濾掉空字串，避免 API 查詢錯誤
    valid_codes = [code for code in stock_codes_list if code.strip()]
    if not valid_codes:
        return "請輸入有效的股票代碼。"

    # 將股票代碼列表組合成 API 需要的格式，例如 'tse_2330.tw|tse_2317.tw'
    formatted_codes = [f'tse_{code}.tw' for code in valid_codes]
    codeno = '|'.join(formatted_codes)

    timestamp = int(time.time() * 1000)
    api_url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch={codeno}&_={timestamp}"
    
    try:
        rate = requests.get(api_url)
        rate.raise_for_status()  # 如果請求失敗 (e.g., 404, 500)，會拋出例外
        req = rate.json()
    except requests.exceptions.RequestException as e:
        print(f"API 請求失敗: {e}")
        return "查詢失敗，請稍後再試。"
    except json.JSONDecodeError:
        return "無法解析伺服器回應，可能是查詢的股票代碼有誤。"

    if 'msgArray' not in req or not req['msgArray']:
        return "查無此股票代碼或相關資料。"

    results = []
    # 迴圈處理 msgArray 中的每一筆股票資料
    for stock_data in req['msgArray']:
        # --- 取值邏輯 ---
        name = stock_data.get('n', 'N/A')
        price = stock_data.get('z', '-')
        bid_price = stock_data.get('b', '_').split('_')[0]
        yesterday_price = stock_data.get('y', '-')
        high = stock_data.get('h', '—')
        low = stock_data.get('l', '—')
        open_price = stock_data.get('o', '—')
        source = ""
        vol = stock_data.get('v', 'N/A')

        # --- 價格取值邏輯 ---
        if price == '-':
            if bid_price and bid_price != '-':
                price = bid_price
                source = "(委買)"
            elif yesterday_price and yesterday_price != '-':
                price = yesterday_price
                source = "(昨收)"
        
        # 修正價格顯示邏輯
        try:
            if float(price).is_integer():
                price_display = f"{int(float(price))}"
            else:
                price_display = f"{float(price):.2f}"
        except (ValueError, TypeError):
            price_display = price

        # --- 漲跌計算邏輯 ---
        change = "N/A"
        percentage = "N/A"
        updown = "N/A"
        if yesterday_price != '-' and price != '-':
            try:
                change_val = float(price) - float(yesterday_price)
                percentage_val = (change_val / float(yesterday_price)) * 100
                
                updown = "▲" if change_val > 0 else "▼" if change_val < 0 else "--"
                change = f"{change_val:+.2f}"
                percentage = f"{percentage_val:+.2f}%"
            except (ValueError, ZeroDivisionError):
                # 如果轉換失敗或昨收價為0，則維持預設值
                pass

        # 組合單支股票的結果
        result_text = (
            f"{name}\n"
            f"最新成交價:{price_display}{source}\n"
            f"開盤:{open_price}｜最高:{high}｜最低:{low}\n"
            f"{updown}漲跌:{change}＊漲跌幅:{percentage}\n"
            f"成交量:{vol}"
        )
        results.append(result_text)

    # 將所有結果用分隔線串接起來
    return "\n\n==========\n\n".join(results)

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=port)
