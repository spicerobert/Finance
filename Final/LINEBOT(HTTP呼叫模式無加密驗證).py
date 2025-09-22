msg1="無加密"
msg2="測試回覆訊息"
"""
HTTP呼叫模式
參考Message API資料，以request呼叫
https://developers.line.biz/en/reference/messaging-api/#send-reply-message
"""
import requests
from flask import Flask, request
# Load configuration from config.json
import json
import os
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
CHANNEL_ACCESS_TOKEN = config.get("CHANNEL_ACCESS_TOKEN")

# 傳送訊息函數
def send_text_message(reply_token):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + CHANNEL_ACCESS_TOKEN
    }
    payload = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": msg1
            },
            {
                "type": "text",
                "text": msg2
            }
        ]
    }
    # 發送 POST 請求至 LINE Messaging API
    response = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=payload
    )
    return response

# 初始化 Flask 應用程式
app = Flask(__name__)
# LINE Webhook 入口
@app.route("/", methods=['POST'])
def linebot():
    # 取得使用者傳來的資料
    data = request.get_json()
    # print(data)
    
    # 提取 replyToken
    reply_token = data['events'][0]['replyToken']
    # 回傳文字訊息
    response = send_text_message(reply_token,"Python訊息測試")
    
    if response.status_code == 200:
        return "OK", 200
    else:
        print("發送訊息失敗:", response.status_code, response.text)
        return "Error", 400

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)
