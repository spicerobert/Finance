import time
import requests
import re
import pandas as pd
from datetime import datetime

from flask import Flask, request, abort
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage, ApiException)

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
import hmac
import hashlib
import base64
@app.route("/", methods=['POST'])
def linebot():
    # 採用手動方式進行 X-Line-Signature 簽章驗證，確保訊息來源為 LINE 官方伺服器
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)
    
    # 取得使用者傳來的資料
    data = request.get_json()
    print(data)
    
    # 確保有事件，且事件類型是訊息，且訊息類型是文字
    if 'events' in data and data['events'] and \
       data['events'][0].get('type') == 'message' and \
       data['events'][0].get('message', {}).get('type') == 'text':
        
        # 提取 replyToken
        reply_token = data['events'][0]['replyToken']
        # 提取使用者輸入的訊息
        message = data['events'][0]['message']['text']
        
        try:
            # 設定預設日期為今天（西元年格式）
            today = datetime.today()
            target_date = today.strftime('%Y%m%d')
            
            if message == '1':
                meg = mes1_1
            elif message == '2':
                print(message)
                # 初始化 TaiwanStockData 類別，傳入日期參數
                stock_data = TaiwanStockData(target_date)
                # 取得股票資料
                stock_df = stock_data.get_stock_data()
                if stock_df is not None:
                    mes_return = {
                        "type": "text",
                        "text": stock_data.analyze_stock_data_2()
                    }
                else:
                    mes_return = {
                        "type": "text",
                        "text": "無法取得股票資料，請稍後再試"
                    }
                meg = mes_return
            elif message == '3':
                # 初始化 TaiwanStockData 類別，傳入日期參數
                stock_data = TaiwanStockData(target_date)
                # 取得股票資料
                stock_df = stock_data.get_stock_data()
                if stock_df is not None:
                    mes_return = {
                        "type": "text",
                        "text": stock_data.analyze_stock_data_3()
                    }
                else:
                    mes_return = {
                        "type": "text",
                        "text": "無法取得股票資料，請稍後再試"
                    }
                meg = mes_return
            elif message == '5':
                meg = mes5
            else:
                if len(message) == 4 and message.isdigit():
                    # 設定要取得的股票資料日期
                    print(f"查詢股票代碼: {message}, 日期: {target_date}")
                    # 初始化 TaiwanStockData 類別，傳入日期參數
                    stock_data = TaiwanStockData(target_date)
                    # 取得股票資料
                    stock_df = stock_data.get_stock_data()
                    if stock_df is not None:
                        mes_return = {
                            "type": "text",
                            "text": stock_data.get_specific_stock_info(message)
                        }
                    else:
                        mes_return = {
                            "type": "text",
                            "text": "無法取得股票資料，請稍後再試"
                        }
                    meg = mes_return
                else:
                    # 檢查是否為股票代碼查詢格式
                    stock_code = ""
                    date = ""
                    if ("股票代碼" in message and "日期" in message):
                        lines = message.split('\n')
                        for x in lines:
                            if "股票代碼" in x:
                                stock_code = x.split(':')[1].strip()
                            if "日期" in x:
                                date = x.split(':')[1].strip()

                        if is_valid_date(date):
                            target_date = date
                            # 初始化 TaiwanStockData 類別，傳入日期參數
                            stock_data = TaiwanStockData(target_date)
                            # 取得股票資料
                            stock_df = stock_data.get_stock_data()
                            if stock_df is not None:
                                mes_return = {
                                    "type": "text",
                                    "text": stock_data.get_specific_stock_info(stock_code)
                                }
                            else:
                                mes_return = {
                                    "type": "text",
                                    "text": "無法取得股票資料，請稍後再試"
                                }
                        else:
                            mes_return = {
                                "type": "text",
                                "text": "日期格式錯誤，請使用 YYYYMMDD 格式"
                            }
                        meg = mes_return
                    else:
                        # 無法辨識的訊息，回傳錯誤訊息
                        meg = mes_err
        except Exception as e:
            print(f"發生未預期錯誤: {e}")
            mes_return = {
                "type": "text",
                "text": f"發生未預期錯誤: {e}"
            }
            meg = mes_return
        
        # 使用 LINE Bot SDK v3 回傳文字訊息
        try:
            with ApiClient(configuration) as api_client:
                api_instance = MessagingApi(api_client)
                # meg 是一個字典，我們需要提取 text 內容
                text_message = TextMessage(text=meg.get("text", "發生錯誤，無法取得訊息內容"))
                reply_message_request = ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[text_message]
                )
                api_instance.reply_message(reply_message_request)
            return "OK", 200
        except ApiException as e:
            print(f"發送訊息失敗: {e}")
            return "Error", 400

def is_valid_date(date_str, date_format="%Y%m%d"):
    try:
        datetime.strptime(date_str, date_format)
        return True
    except ValueError:
        return False

class TaiwanStockData:
    def __init__(self, date_str):
        """
        初始化股票資料對象

        Args:
            date_str: 日期字串，格式為西元年月日 (例如: '20250731')
        """
        self.date_str = date_str
        self.df = None

    def get_stock_data(self):
        """
        取得台灣股票基本面資訊
        """
        timestamp = int(time.time() * 1000)
        url = f"https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?date={self.date_str}&selectType=ALL&response=json&_={timestamp}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            print(f"正在取得 {self.date_str} 的台灣股票資訊...")
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # 檢查HTTP錯誤

            # 解析JSON資料
            data = response.json()

            if not data:
                print("未取得任何資料")
                return None

            # 轉換為DataFrame
            self.df = pd.DataFrame(data["data"], columns=data["fields"])
            date = data["date"]
            print(date)
            # 資料清理和轉換
            self.df["收盤價"] = pd.to_numeric(self.df["收盤價"].str.replace(",", ""), errors="coerce")
            self.df['殖利率(%)'] = pd.to_numeric(self.df['殖利率(%)'], errors='coerce')
            self.df['本益比'] = pd.to_numeric(self.df['本益比'], errors='coerce')
            self.df['股價淨值比'] = pd.to_numeric(self.df['股價淨值比'], errors='coerce')

            # 添加資料取得時間
            self.df['DataDate'] = date

            print(f"成功取得 {len(self.df)} 筆股票資料")
            print(self.df)
            return self.df

        except requests.exceptions.RequestException as e:
            print(f"網路請求錯誤: {e}")
        except json.JSONDecodeError as e:
            print(f"JSON解析錯誤: {e}")
        except Exception as e:
            print(f"發生未預期錯誤: {e}")
        return None

    def analyze_stock_data(self):
        """
        分析股票資料並顯示統計資訊
        """
        if self.df is None or self.df.empty:
            print("無資料可分析")
            return

        print("\n=== 股票資料統計分析 ===")
        print(f"總股票數量: {len(self.df)}")
        print(f"有P/E比資料的股票: {self.df['本益比'].notna().sum()}")
        print(f"有股息殖利率資料的股票: {self.df['殖利率(%)'].notna().sum()}")
        print(f"有P/B比資料的股票: {self.df['股價淨值比'].notna().sum()}")

        # 顯示基本統計殖利率(%)
        print("\n=== 數值欄位統計 ===")
        numeric_stats = self.df[['本益比', '殖利率(%)', '股價淨值比']].describe()
        print(numeric_stats)
    def analyze_stock_data_2(self):
        if self.df is None or self.df.empty:
            print("無資料可分析")
            return

        # 顯示高股息殖利率股票 (前10名)
        high_dividend = self.df[self.df['殖利率(%)'].notna()].nlargest(10, '殖利率(%)')
        print("\n=== 高股息殖利率股票 (前10名) ===")
        print(high_dividend[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False))
        return high_dividend[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False)
    def analyze_stock_data_3(self):
        if self.df is None or self.df.empty:
            print("無資料可分析")
            return
        # 顯示低P/E比股票 (前10名，排除負值和異常值)
        low_pe = self.df[(self.df['本益比'] > 0) & (self.df['本益比'] < 100)].nsmallest(10, '本益比')
        print("\n=== 低P/E比股票 (前10名) ===")
        print(low_pe[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False))
        return low_pe[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False)
    def save_to_excel(self, filename):
        """
        將資料儲存為Excel檔案

        Args:
            filename: 檔案名稱
        """
        if self.df is None or self.df.empty:
            print("無資料可儲存")
            return

        try:
            self.df.to_excel(filename, index=False, engine='openpyxl')
            print(f"\n資料已儲存至: {filename}")
        except Exception as e:
            print(f"儲存檔案時發生錯誤: {e}")

    def search_stock(self, code_or_name):
        """
        搜尋特定股票

        Args:
            code_or_name: 股票代碼或名稱
        """
        if self.df is None:
            print("尚未取得資料")
            return None

        result = self.df[
            (self.df['證券代號'].str.contains(str(code_or_name), na=False)) |
            (self.df['證券名稱'].str.contains(str(code_or_name), na=False))
        ]
        return result

    def get_specific_stock_info(self, stock_code):
        """
        顯示特定股票資訊 (例如台積電)

        Args:
            stock_code: 股票代碼
        """
        text=""
        if self.df is None:
            print("尚未取得資料")
            return None

        stock = self.df[self.df['證券代號'] == stock_code]
        if not stock.empty:
            text = f"\n=== 股票代碼 {stock_code} 資訊 ===\n" + \
               f"公司名稱: {stock.iloc[0]['證券名稱']}\n" + \
               f"收盤價: {stock.iloc[0]['收盤價']}\n" + \
               f"股息殖利率: {stock.iloc[0]['殖利率(%)']}%\n"+ \
               f"本益比: {stock.iloc[0]['本益比']}\n" + \
               f"股價淨值比: {stock.iloc[0]['股價淨值比']}\n" + \
               f"資料日期: {stock.iloc[0]['DataDate']}"

            print(f"\n=== 股票代碼 {stock_code} 資訊 ===")
            print(f"股票代碼: {stock.iloc[0]['證券代號']}")
            print(f"公司名稱: {stock.iloc[0]['證券名稱']}")
            print(f"P/E比: {stock.iloc[0]['本益比']}")
            print(f"股息殖利率: {stock.iloc[0]['殖利率(%)']}%")
            print(f"P/B比: {stock.iloc[0]['股價淨值比']}")
        else:
            text =f"無法找到股票代碼 {stock_code} 的資料"
            print(f"無法找到股票代碼 {stock_code} 的資料")

        return text
    @staticmethod
    def compare_dates(date1, date2):
        """
        比較兩個不同日期的股票資料

        Args:
            date1, date2: 日期字串
        """
        print(f"\n=== 比較 {date1} 與 {date2} 的資料 ===")

        stock_data1 = TaiwanStockData(date1)
        stock_data2 = TaiwanStockData(date2)

        df1 = stock_data1.get_stock_data()
        df2 = stock_data2.get_stock_data()

        if df1 is not None and df2 is not None:
            # 合併資料進行比較
            comparison = df1.merge(df2, on=['證券代號', '證券名稱'], suffixes=('_1', '_2'))

            # 計算變化
            comparison['PE_Change'] = comparison['本益比_2'] - comparison['本益比_1']
            comparison['Dividend_Change'] = comparison['殖利率(%)_2'] - comparison['殖利率(%)_1']

            print(f"可比較的股票數量: {len(comparison)}")

            # 顯示P/E比變化最大的股票
            pe_changes = comparison.dropna(subset=['PE_Change']).nlargest(5, 'PE_Change')
            print("\nP/E比增加最多的股票:")
            print(pe_changes[['證券代號', '證券名稱', '本益比_1', '本益比_2', 'PE_Change']].to_string(index=False))

# 訊息定義
mes1 = {
    "type": "text",
    "text": "您好！\n我是股票資訊查詢小幫手,請輸入您欲查詢的代碼[1]或[2]或[3]\n1: 個股日本益比、殖利率及股價淨值比\n2. 高股息殖利率股票 (前10名)\n3. 低本益比股票 (前10名)\n"
}
mes1_1 = {
    "type": "text",
    "text": "查詢單一股票,請回覆4碼股票代碼\n欲查詢特定日期的股票資訊請輸入[5]"
}
mes5 = {
    "type": "text",
    "text": "請依格式輸入:\n股票代碼:XXXX\n日期:20250731"
}
mes_err = {
    "type": "text",
    "text": "無法辨識您的代碼,請重新輸入"
}

# 啟動 Flask 伺服器
if __name__ == "__main__":
    app.run(port=port)
