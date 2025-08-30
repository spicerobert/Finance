"""
第四版，最簡易，無驗證簽章
LINE Bot簡易Flask後端範例(不驗證簽章)
這是一個簡化版本的LINE Bot後端實作，使用Flask接收 webhook，
並透過LINE Messaging API回覆固定文字訊息。
適用場景：
- 本機開發、測試階段
- 快速體驗 LINE Bot 架構與回應流程
注意事項(Warning)：
- 此版本**未實作X-Line-Signature驗證**，無法確認webhook是否來自LINE Server，
  在正式上線或處理敏感資料時**極不安全**。
- 建議正式上線時改用WebhookHandler或手動HMAC驗證方式處理簽章。
"""
from flask import Flask, request
from linebot.v3.messaging import (Configuration,ApiClient,MessagingApi,ReplyMessageRequest,TextMessage)
# Load configuration from config.json
import json
import os
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)
CHANNEL_ACCESS_TOKEN = config.get("CHANNEL_ACCESS_TOKEN")
# CHANNEL_SECRET = config.get("CHANNEL_SECRET")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 初始化 Flask 應用程式
app = Flask(__name__)
# 這表示只有當 LINE 向Flask發送POST 請求時，webhook 函數才會被觸發
@app.route("/", methods=['POST'])
def linebot():
    # 取得使用者傳來的資料
    data = request.get_json()
    print(data)    
    # 提取 replyToken
    reply_token = data["events"][0]["replyToken"]    
    # 回傳文字訊息
    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message_with_http_info(
        ReplyMessageRequest(
            reply_token=reply_token,
            messages=[TextMessage(text="這是無驗證版機器人回覆")]
        )
    )    
    return "OK", 200

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)