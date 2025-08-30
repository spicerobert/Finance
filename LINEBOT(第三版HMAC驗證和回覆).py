"""
第三版，簡易可手動無驗證簽章
LINE Bot簡易Flask後端範例（含簡易驗證簽章）
這是一個簡化版本的LINE Bot後端實作，使用Flask接收 webhook，
並透過LINE Messaging API回覆固定文字訊息。
適用場景：
- 本機開發、測試階段
- 快速體驗LINE Bot架構與回應流程
注意事項(Warning):
- 此版本使用HMAC驗證方式處理簽章，未實作X-Line-Signature驗證，無法確認webhook是否來自LINE Server
- 建議正式上線時改用 WebhookHandler
"""
from flask import Flask, request,abort
from linebot.v3.messaging import (Configuration,ApiClient,MessagingApi,ReplyMessageRequest,TextMessage)
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
# 這表示只有當 LINE 向Flask發送POST 請求時，webhook 函數才會被觸發
@app.route("/", methods=["POST"])
def webhook():
    # 驗證簽章
    import hmac, hashlib, base64
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)
    else:
        data = request.get_json()
        # 確保有事件，且事件類型是訊息，且訊息類型是文字
        if 'events' in data and data['events'] and \
           data['events'][0].get('type') == 'message' and \
           data['events'][0].get('message', {}).get('type') == 'text':
            # 提取文字訊息和 replyToken
            user_text = data['events'][0]['message']['text']
            reply_token = data['events'][0]['replyToken']
            # 建立一個與LINE API溝通的客戶端的臨時連線
            with ApiClient(configuration) as api_client:
                # 建立一個專門用來處理「訊息」相關操作的物件
                messaging_api = MessagingApi(api_client)
                # 呼叫messaging_api物件的reply_message_with_http_info方法來發送訊息。這個方法需要一個ReplyMessageRequest物件作為參數
                messaging_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=f"第三版手動驗證和回覆: {user_text}")]
                    )
                )
    return "OK",200

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)
