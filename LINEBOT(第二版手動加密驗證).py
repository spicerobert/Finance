"""第二版，用手動加密
LINE Bot Webhook 簡易 Flask 實作（含簡易簽章驗證）

本程式為使用 Flask 製作的 LINE Bot webhook 接收端範例，
採用手動方式進行 X-Line-Signature 簽章驗證，確保訊息來源為 LINE 官方伺服器。

功能簡介：
- 接收來自 LINE 的 POST 請求（Webhook）
- 使用 Channel Secret 搭配 HMAC-SHA256 演算法驗證簽章
- 若驗證成功，印出 webhook 資料；失敗則回傳 400 錯誤

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
# 這表示只有當 LINE 向Flask發送POST 請求時，callback 函數才會被觸發
@app.route("/", methods=["POST"])
def webhook():
    import hmac, hashlib, base64
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)
    else:
        print(body)
    return "OK"

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=3001)
