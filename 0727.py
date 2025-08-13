msg1={
  "type": "text",
  "text": "您好！我是聊天機器人\n\n"
}

"""
HTTP呼叫模式
參考Message API資料，以request呼叫
https://developers.line.biz/en/reference/messaging-api/#send-replmsg1={
  "type": "text",
  "text": "您好！我是聊天機器人\n\n"
}y-message
"""
'''
from pyngrok import ngrok
# Terminate open tunnels if any exist
ngrok.kill()
# Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
NGROK_AUTH_TOKEN = "307S2PVheQuY6a2KVXIVsJr7Jky_rvpitHzLNesTFyKSyYeS"  #@param {type:"string"}
ngrok.set_auth_token(NGROK_AUTH_TOKEN)
# Open a http tunnel on port 5000
public_url = ngrok.connect(5000)
print(f"Ngrok tunnel is active at: {public_url}")
'''

import requests
from flask import Flask, request

# 初始化 Flask 應用程式
app = Flask(__name__)

# 設定 LINE BOT Token
BOT_TOKEN = "d1Ft6RdG29yn5O235dbj3l0ZAPxiOAMBKO8w5HxkCXcrEUIMxe3WV6mz2ic199qYUrf7eiKFKkpCgDdD4FnqKbmMiG5emaPRyNq0ZEkUQWaBpEvZCvUrkb1XA7EanLIMu4cXUABxMlRPMDcR+1S8qQdB04t89/1O/w1cDnyilFU="

# 傳送文字訊息函數
def send_text_message(reply_token):   #, text):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + BOT_TOKEN
    }
    
    payload = {
        "replyToken": reply_token,
    #     "messages": [{
    #         "type": "text",
    #         "text": text
    #     }
    #  ]
        "messages": [msg1]
    }
    
    # 發送 POST 請求至 LINE Messaging API
    response = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers=headers,
        json=payload
    )
    return response

# LINE Webhook 入口
@app.route("/", methods=['POST'])
def linebot():
    # 取得使用者傳來的資料
    data = request.get_json()
    print(data)
    
    # 提取 replyToken
    reply_token = data['events'][0]['replyToken']
    
    # 回傳文字訊息
    response = send_text_message(reply_token)
    
    if response.status_code == 200:
        return "OK", 200
    else:
        print("發送訊息失敗:", response.status_code, response.text)
        return "Error", 400

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=5000)

