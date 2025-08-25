""" 第一版，官方版SDK加密
使用 Flask 與 LINE Bot SDK v3 建立的 LINE 聊天機器人後端範例。
功能：
- 接收來自 LINE 的 webhook 訊息（如文字、圖片等）
- 驗證 LINE 簽章（X-Line-Signature）確保安全性
- 當收到訊息時，自動回覆一段固定文字

架構說明：
- 使用 Flask 架設 HTTP 伺服器，並在 "/" 路徑處理 POST 請求
- 使用 LINE 的 WebhookHandler 驗證簽章與分派事件
- 使用 MessagingApi 發送回覆訊息

使用者需要填入正確的 Channel access token 與 Channel secret 才能運作
"""
from flask import Flask, request, abort
# WebhookHandler 驗證簽章
from linebot.v3 import (WebhookHandler)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent
)
from linebot.v3.exceptions import (InvalidSignatureError)

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
handler = WebhookHandler(CHANNEL_SECRET)

# 初始化 Flask 應用程式
app = Flask(__name__)
# 這表示只有當 LINE 向Flask發送POST 請求時，callback 函數才會被觸發
@app.route("/", methods=['POST'])
def callback():
    # 取得 LINE 簽章（X-Line-Signature）
    signature = request.headers['X-Line-Signature']
    # 取得 文字版訊息內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # 使用handler.handle驗證
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent)
def handle_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="這是完整版機器人回覆")]
            )
        )

if __name__ == "__main__":
    app.run(port=3001)
    # app.run(host='0.0.0.0', port=3001) #加入 host='0.0.0.0'，會讓您的 Flask 伺服器監聽來自任何 IP 位址的連線，而不僅僅是本機的 127.0.0.1。
