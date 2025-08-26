"""
第三版，最簡易，可手動無驗證簽章
LINE Bot 簡易 Flask 後端範例（含簡易驗證簽章）

這是一個簡化版本的 LINE Bot 後端實作，使用 Flask 接收 webhook，
並透過 LINE Messaging API 回覆固定文字訊息。

適用場景：
- 本機開發、測試階段
- 快速體驗 LINE Bot 架構與回應流程

注意事項（Warning）：
- 此版本**未實作 X-Line-Signature 驗證**，無法確認 webhook 是否來自 LINE Server，
  在正式上線或處理敏感資料時**極不安全**。
- 建議正式上線時改用 WebhookHandler 或手動 HMAC 驗證方式處理簽章。

使用者需要填入正確的 Channel access token 與 Channel secret 才能運作
"""
from flask import Flask, request,abort

from linebot.v3.messaging import (
    Configuration,
    ApiClient,    
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
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
def webhook(): #驗證簽章
    import hmac, hashlib, base64
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)
    else:
        data = request.get_json()
        print(data["events"][0]["text"])
        # 提取 replyToken
        reply_token = data["events"][0]["replyToken"]
        #建立一個與 LINE API 溝通的客戶端，回傳文字訊息
        with ApiClient(configuration) as api_client: #這是LINE SDK中負責處理底層HTTP請求、驗證和連線的類別。
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text="這是簡易驗證版機器人回覆")]
            )
        )
    return "OK"

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)
