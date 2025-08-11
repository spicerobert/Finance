import yfinance as yf
import datetime as dt # Use alias for clarity
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import os
import threading
from matplotlib import gridspec
from queue import Queue

import json
import time
import requests
# 暗色模式配色
DARK_BG = '#121212'
from flask import Flask, request

GRID_COLOR = '#333333'
TEXT_COLOR = 'white'
MA5_COLOR = 'red'    # 5MA線顏色（紅色）
MA10_COLOR = 'orange' # 10MA線顏色（橙色）
MA20_COLOR = 'green'  # 20MA線顏色（綠色）

# 初始化 Flask 應用程式
app = Flask(__name__)

# 設定 LINE BOT Token
BOT_TOKEN = "lBunjLa9oETPP9SRai3fnpXqY4s/6qFWCCabpQxRqRgGCqIx0jMo/SNMZe3w17lwSqeyzs8HvmdzVbuA6dKNsGRzxyFfL2HY+CiuYOYGM3mZhRt+Eb8gkaKpcoJTHlc6RWDJ7ihK3xuaKz2E+F9AegdB04t89/1O/w1cDnyilFU="

# 傳送文字訊息函數
def send_text_message(reply_token, text, image_path):    
    image_url = request.host_url +"/static/" +image_path  # 像 http://127.0.0.1:5000/static/2330_kd.png
    image_url = image_url.replace('//static', '/static')
    image_url = image_url.replace('http://', 'https://')
    print(f"image_url : {image_url}")
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + BOT_TOKEN
    }
    
    payload = {
        "replyToken": reply_token,
        "messages": [{
            "type": "text",
            "text": text
        },
        {
        "type": "image",
        "originalContentUrl": image_url,
        "previewImageUrl": image_url
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

# LINE Webhook 入口
#@app.route("/<file>'")
#def test(file): 
#    print(f"Entering : {file}")
#    return open(f"stock_charts/xxx.png")
@app.route("/", methods=['POST','GET'])
def linebot():
    # 取得使用者傳來的資料
    data = request.get_json()
    if not data or 'events' not in data or not data['events']:
        return "Invalid payload", 400

    reply_token = data['events'][0]['replyToken']

    #取得輸入進來的股票代要碼資料
    message = data["events"][0]["message"]['text']
    # Convert datetime to string (ISO format is common)
    #date_string = now.isoformat()

    # Create a dictionary to include in JSON

    # Convert to JSON string
    #json_output = json.dumps(date_string)
    #mes1["contents"]["footer"]["contents"][0]["action"]["text"] = json_output
    #print("\n台灣股票技術分析圖 (含5MA/10MA/20MA)")
    #print("請輸入股票代號 (多個請用逗號分隔，如: 2330.TW,2454.TWO)")

    # 預設抓取近一年的資料
    start_date = dt.datetime.now() - dt.timedelta(days=365)

    user_input = message

    stock_data = get_stock_data(user_input, start_date)
    if stock_data is None or stock_data.empty:
        send_text_message(reply_token, f"找不到股票代號 {user_input} 的資料，請確認後再試一次。", "")
        return "OK", 200

    symbols = [s.strip().upper() for s in user_input.split(',')]
    processed_symbols = []
    figures = []

    for symbol in symbols:
        processed_symbols.append(symbol)

        if symbol in stock_data.columns.get_level_values(0):
            fig = plot_stock_with_indicators(stock_data, symbol)
            figures.append(fig)
        else:
            figures.append(None)
            print(f"警告: {symbol} 無有效資料")
    
    image_path =  save_figures_to_png(figures, processed_symbols)
    
    response = send_text_message(reply_token, f"前5筆資料:{stock_data.head()}, \n\n最近5筆資料 : {stock_data.tail()}", image_path)

    if response.status_code == 200:
        return "OK", 200
    else:
        print("發送訊息失敗:", response.status_code, response.text)
        return "Error", 400

def get_stock_data(stock_symbols, start_date):
    # 處理多個股票代號
    symbols_list = [s.strip().upper() for s in stock_symbols.split(',')]
    processed_symbols = []
    valid_symbols = []

    for symbol in symbols_list:
        # 檢查股票代號是否已有後綴
        if not (symbol.endswith('.TW') or symbol.endswith('.TWO')):
            # 先嘗試上市股票
            processed_symbols.append(symbol + '.TW')
        else:
            processed_symbols.append(symbol)

    try:
        df = yf.download(processed_symbols, start=start_date, group_by='ticker')

        # 檢查哪些股票成功取得資料
        for symbol in processed_symbols:
            if symbol in df.columns.get_level_values(0):
                valid_symbols.append(symbol)

        if not valid_symbols:
            print("所有股票代號均無法取得資料，請確認代號是否正確")
            return None

        print(f"成功取得 {', '.join(valid_symbols)} 的股票資料")

        # 找出失敗的代號
        failed_symbols = [s for s in processed_symbols if s not in valid_symbols]
        if failed_symbols:
            print(f"以下代號無法取得資料: {', '.join(failed_symbols)} (可能已下市或代號錯誤)")

        return df
    except Exception as e:
        print(f"取得股票資料時發生錯誤: {e}")
        return None

def get_valid_date(prompt, default_date):
    while True:
        date_input = input(prompt).strip()
        if not date_input:
            return default_date
        try:
            return dt.datetime.strptime(date_input, "%Y-%m-%d")
        except ValueError:
            print("日期格式不正確，請使用 YYYY-MM-DD 格式")

def calculate_technical_indicators(df):
    """計算所有技術指標"""
    # 計算MACD
    df['EMA_Fast'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['Histogram'] = df['MACD'] - df['Signal']

    # 計算移動平均線
    df['MA5'] = df['Close'].rolling(window=5).mean()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA20'] = df['Close'].rolling(window=20).mean()

    return df

def input_with_timeout(prompt, timeout=30):
    """帶超時的輸入函數（30秒）"""
    print(prompt, end='', flush=True)
    q = Queue()

    def input_thread():
        q.put(input())

    thread = threading.Thread(target=input_thread)
    thread.daemon = True
    thread.start()

    try:
        return q.get(timeout=timeout)
    except:
        print("\n輸入超時，自動取消儲存")
        return 'n'

def plot_stock_with_indicators(stock_data, symbol):
    try:
        # 準備K線圖資料並計算指標
        df = stock_data[symbol].copy()
        df = calculate_technical_indicators(df)

        # 創建暗色背景圖表
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(24, 12), facecolor=DARK_BG)
        gs = gridspec.GridSpec(3, 1, height_ratios=[3, 1, 1])

        # 1. K線圖區域
        ax1 = plt.subplot(gs[0])
        ax1.set_facecolor(DARK_BG)

        # 繪製K線圖
        dates = mdates.date2num(df.index.to_pydatetime())
        for i in range(len(df)):
            color = 'r' if df['Close'][i] >= df['Open'][i] else 'g'
            ax1.plot([dates[i], dates[i]], [df['Low'][i], df['High'][i]],
                    color=color, linewidth=1)
            ax1.plot([dates[i], dates[i]],
                    [min(df['Open'][i], df['Close'][i]), max(df['Open'][i], df['Close'][i])],
                    color=color, linewidth=6, alpha=0.75)

        # 繪製移動平均線
        ax1.plot(dates, df['MA5'], color=MA5_COLOR, label='5MA', linewidth=1.5)
        ax1.plot(dates, df['MA10'], color=MA10_COLOR, label='10MA', linewidth=1.5)
        ax1.plot(dates, df['MA20'], color=MA20_COLOR, label='20MA', linewidth=1.5)

        # 2. MACD指標區域
        ax2 = plt.subplot(gs[1])
        ax2.set_facecolor(DARK_BG)

        # 繪製MACD指標
        ax2.plot(dates, df['MACD'], color='cyan', label='MACD', linewidth=1.5)
        ax2.plot(dates, df['Signal'], color='magenta', label='Signal', linewidth=1.5)
        for i in range(len(df)):
            color = 'r' if df['Histogram'][i] >= 0 else 'g'
            ax2.bar(dates[i], df['Histogram'][i], width=0.6, color=color, alpha=0.6)

        # 3. 成交量區域
        ax3 = plt.subplot(gs[2])
        ax3.set_facecolor(DARK_BG)

        # 繪製成交量
        for i in range(len(df)):
            color = 'r' if df['Close'][i] >= df['Open'][i] else 'g'
            ax3.bar(dates[i], df['Volume'][i], width=0.6, color=color, alpha=0.6)

        # 設置圖表格式
        for ax in [ax1, ax2, ax3]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.grid(True, linestyle='--', linewidth=0.5, color=GRID_COLOR)
            ax.tick_params(colors=TEXT_COLOR)
            for spine in ax.spines.values():
                spine.set_color(GRID_COLOR)
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

        ax1.set_title(f'{symbol} 技術分析圖 (含5MA/10MA/20MA)', fontsize=16, color=TEXT_COLOR)
        ax1.legend(facecolor=DARK_BG, edgecolor=TEXT_COLOR)
        ax2.set_ylabel('MACD', fontsize=12, color=TEXT_COLOR)
        ax2.legend(facecolor=DARK_BG, edgecolor=TEXT_COLOR)
        ax3.set_ylabel('成交量', fontsize=12, color=TEXT_COLOR)

        plt.tight_layout()
        plt.show()

        return fig

    except Exception as e:
        print(f"繪製K線圖時發生錯誤: {e}")
        return None

def save_figures_to_png(figures, symbols):
    """儲存圖表為PNG檔案"""

    # 獲取當前工作目錄
    current_dir = os.getcwd()
    chart_dir = os.path.join(current_dir, 'static')

    if not os.path.exists(chart_dir):
        os.makedirs(chart_dir)
        print(f"已建立圖表儲存目錄: {chart_dir}")

    saved_files = []
    for fig, symbol in zip(figures, symbols):
        if fig:
            filename = f"{symbol.replace('.TW', '').replace('.TWO', '')}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(chart_dir, filename)

            fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor=DARK_BG)
            saved_files.append(filepath)
            plt.close(fig)

    if saved_files:
        print("\n圖表已儲存至以下路徑:")
        for file in saved_files:
            print(f"- {file}")

        # 顯示目錄路徑
        print(f"\n圖表儲存目錄: {chart_dir}")
        print(f"file name is {filename}")
        return filename

if __name__ == "__main__":
    # 確保 static 資料夾存在
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(port=3000, debug=True)