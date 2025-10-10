# 匯入必要的模組
import time  # 用於時間戳記處理
import requests  # 用於HTTP請求台灣證券交易所API
import pandas as pd  # 用於資料處理和分析
from datetime import datetime, timedelta  # 用於日期處理和計算
from flask import Flask, request, abort  # Flask框架用於建立Web應用程式及處理HTTP請求
from linebot.v3.messaging import (Configuration, ApiClient, MessagingApi,ReplyMessageRequest, TextMessage, ApiException)  # LINE Bot SDK v3 用於訊息處理
import requests
from bs4 import BeautifulSoup
# 載入設定檔案 (config.json)注意：config.json 需包含 CHANNEL_ACCESS_TOKEN 和 CHANNEL_SECRET
import json
import os
config_path = os.path.join(os.path.dirname(__file__), 'config.json')
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = config.get("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = config.get("CHANNEL_SECRET")
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# 初始化 Flask 應用程式
app = Flask(__name__)
port = "3001"

# LINE Webhook 入口函數
# 註冊路由規則：處理 POST 請求到根路徑 "/"
# 此函數負責接收 LINE 官方推送的訊息事件並進行處理
import hmac
import hashlib
import base64

@app.route("/", methods=['POST'])
def linebot():
    """
    LINE Bot Webhook 主入口函數
    處理來自 LINE 官方伺服器的訊息事件

    主要功能：
    1. 驗證訊息來源安全性 (HMAC 簽章驗證)
    2. 解析使用者訊息內容
    3. 根據訊息內容路由到不同的處理分支
    4. 回傳適當的回應訊息

    Returns:
        tuple: (response_message, status_code)
    """
    # 採用 HMAC SHA256 手動驗證 X-Line-Signature 簽章
    # 確保訊息確實來自 LINE 官方伺服器，而非偽造請求
    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(CHANNEL_SECRET.encode(), body.encode(), hashlib.sha256).digest()
    if signature != base64.b64encode(hash).decode():
        abort(400)  # 簽章驗證失敗，回傳 HTTP 400 錯誤

    # 將 JSON 格式的請求內容解析為 Python 字典
    data = request.get_json()
    print(data)  # 除錯用：輸出完整的請求資料

    # 資料驗證：確保請求包含有效的事件，且事件類型為文字訊息
    # LINE Webhook 可能包含多個事件，此處只處理第一個文字訊息事件
    if 'events' in data and data['events'] and \
       data['events'][0].get('type') == 'message' and \
       data['events'][0].get('message', {}).get('type') == 'text':

        # 提取訊息回覆權杖 (replyToken)
        # LINE 要求在 30 秒內使用此權杖回覆訊息，否則權杖會失效
        reply_token = data['events'][0]['replyToken']

        # 提取使用者實際傳送的文字訊息內容
        message = data['events'][0]['message']['text']

        # ===== 訊息處理主邏輯 =====
        # 根據使用者輸入的訊息內容進行分支處理
        # 支援的指令：
        # 1: 顯示功能說明
        # 2: 高股息殖利率股票排行 (前10名)
        # 3: 低本益比股票排行 (前10名)
        # 4: 比較兩個日期的本益比變化
        # 5: 查詢特定日期單一股票資訊
        # 直接輸入4碼數字: 查詢今日單一股票資訊
        # 特定格式訊息: 進階查詢功能
        try:
            # 設定預設查詢日期為今天（格式：YYYYMMDD）
            # 用於沒有指定日期的查詢需求
            today = datetime.today()
            target_date = today.strftime('%Y%m%d')

            # ===== 分支 1: 顯示查詢提示訊息 =====
            if message == '1':
                meg = mes1_1
            # ===== 分支 2: 高股息殖利率股票排行 =====
            elif message == '2':
                print(message)  # 除錯輸出接收到的訊息
                # 初始化 TaiwanStockData 類別，設定查詢今天的股票資料
                stock_data = TaiwanStockData(target_date)
                # 從台灣證券交易所API取得最新的股票基本面資料
                stock_df = stock_data.get_stock_data()
                if stock_df is not None:
                    # 成功取得資料，使用 analyze_stock_data_2 分析並取得高股息殖利率前10名
                    mes_return = {"type": "text","text": stock_data.analyze_stock_data_2()}
                else:
                    # 無法取得股票資料，回傳錯誤訊息
                    mes_return = {"type": "text","text": "無法取得股票資料，請稍後再試"}
                meg = mes_return
            # ===== 分支 3: 低本益比股票排行 =====
            elif message == '3':
                # 初始化 TaiwanStockData 類別，設定查詢今天的股票資料
                stock_data = TaiwanStockData(target_date)
                # 從台灣證券交易所API取得最新的股票基本面資料
                stock_df = stock_data.get_stock_data()
                if stock_df is not None:
                    # 成功取得資料，使用 analyze_stock_data_3 分析並取得低本益比前10名
                    mes_return = {"type": "text","text": stock_data.analyze_stock_data_3()}
                else:
                    # 無法取得股票資料，回傳錯誤訊息
                    mes_return = {"type": "text","text": "無法取得股票資料，請稍後再試"}
                meg = mes_return
            # ===== 分支 4: 比較兩個日期的本益比變化 =====
            elif message == '4':
                # 顯示輸入格式提示訊息，要求用戶輸入兩個日期進行比較
                meg = mes4
            # ===== 分支 5: 查詢特定日期單一股票資訊 =====
            elif message == '5':
                # 顯示輸入格式提示訊息，要求用戶輸入股票代碼和日期
                meg = mes5
            # ===== 特殊格式訊息處理 =====
            else:
                # ===== 直接輸入4碼股票代碼 =====
                # 檢查訊息是否為4位數字（台灣股票代碼格式）
                if len(message) == 4 and message.isdigit():
                    # 長度為4且全為數字，視為股票代碼，直接查詢今日資訊
                    print(f"查詢股票代碼: {message}, 日期: {target_date}")
                    # 初始化 TaiwanStockData 類別，設定查詢今天的股票資料
                    stock_data = TaiwanStockData(target_date)
                    # 從台灣證券交易所API取得最新的股票基本面資料
                    stock_df = stock_data.get_stock_data()
                    if stock_df is not None:
                        # 成功取得資料，使用 get_specific_stock_info 取得特定股票資訊
                        mes_return = {"type": "text","text": stock_data.get_specific_stock_info(message)}
                    else:
                        # 無法取得股票資料，回傳錯誤訊息
                        mes_return = {"type": "text","text": "無法取得股票資料，請稍後再試"}
                    meg = mes_return
                else:
                    # ===== 多行格式訊息處理 =====
                    # 解析包含特定關鍵字的複雜訊息格式（支援多行輸入）

                    # ===== 處理特定日期單一股票查詢 =====
                    # 訊息格式範例：
                    # 股票代碼:2330
                    # 日期:20250731
                    stock_code = ""
                    date = ""
                    if ("股票代碼" in message and "日期" in message):
                        # 檢測到股票代碼和日期關鍵字，解析多行訊息
                        lines = message.split('\n')  # 按行分割訊息
                        for line in lines:
                            if "股票代碼" in line:
                                # 提取冒號後面的股票代碼並去除空白
                                stock_code = line.split(':')[1].strip()
                            if "日期" in line:
                                # 提取冒號後面的日期並去除空白
                                date = line.split(':')[1].strip()

                        # 驗證日期格式是否正確 (YYYYMMDD)
                        if is_valid_date(date):
                            target_date = date
                            # 初始化 TaiwanStockData 類別，設定查詢指定日期的股票資料
                            stock_data = TaiwanStockData(target_date)
                            # 從台灣證券交易所API取得指定日期的股票基本面資料
                            stock_df = stock_data.get_stock_data()
                            if stock_df is not None:
                                # 成功取得資料，使用 get_specific_stock_info 取得特定股票資訊
                                mes_return = {"type": "text","text": stock_data.get_specific_stock_info(stock_code)}
                            else:
                                # 無法取得股票資料，回傳錯誤訊息
                                mes_return = {"type": "text","text": "無法取得股票資料，請稍後再試"}
                        else:
                            # 日期格式錯誤，回傳格式提示訊息
                            mes_return = {"type": "text","text": "日期格式錯誤，請使用 YYYYMMDD 格式"}
                        meg = mes_return

                    # ===== 處理兩個日期比較 =====
                    # 訊息格式範例：
                    # 日期1:20250730
                    # 日期2:20250731
                    elif ("日期1" in message and "日期2" in message):
                        # 檢測到日期比較關鍵字，解析多行訊息
                        lines = message.split('\n')  # 按行分割訊息
                        date1 = ""
                        date2 = ""
                        for line in lines:
                            if "日期1" in line:
                                # 提取第一個日期
                                date1 = line.split(':')[1].strip()
                            if "日期2" in line:
                                # 提取第二個日期
                                date2 = line.split(':')[1].strip()

                        # 驗證兩個日期格式是否都正確
                        if is_valid_date(date1) and is_valid_date(date2):
                            # 呼叫類別方法比較兩個日期的本益比變化
                            mes_return = {"type": "text","text": TaiwanStockData.compare_dates(date1, date2)}
                        else:
                            # 日期格式錯誤，回傳格式提示訊息
                            mes_return = {"type": "text","text": "日期格式錯誤，請使用 YYYYMMDD 格式"}
                        meg = mes_return
                    else:
                        # ===== 無法辨識的訊息處理 =====
                        # 訊息不符合任何支援的格式，回傳錯誤提示和功能說明
                        meg = {"type": "text","text": mes_err["text"] + "\n" + mes1["text"]}
        # ===== 異常處理 =====
        except Exception as e:
            # 捕捉所有未預期的程式錯誤
            print(f"發生未預期錯誤: {e}")  # 輸出錯誤資訊到伺服器日誌
            # 回傳錯誤訊息給用戶，讓用戶知道發生了問題
            mes_return = {"type": "text","text": f"發生未預期錯誤: {e}"}
            meg = mes_return

        # ===== 訊息回傳處理 =====
        # 使用 LINE Bot SDK v3 將處理結果回傳給使用者
        try:
            # 建立 API 客戶端連線
            with ApiClient(configuration) as api_client:
                api_instance = MessagingApi(api_client)
                # meg 是一個字典物件，從中提取 text 內容
                # 如果 meg 沒有 "text" 鍵，則使用預設錯誤訊息
                text_message = TextMessage(text=meg.get("text", "發生錯誤，無法取得訊息內容"))
                # 建立回覆訊息請求，包含 reply_token 和訊息內容
                reply_message_request = ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[text_message]
                )
                # 發送訊息給 LINE 官方伺服器
                api_instance.reply_message(reply_message_request)
            # 成功發送訊息，回傳 HTTP 200 狀態碼
            return "OK", 200
        except ApiException as e:
            # LINE Bot API 發送失敗的異常處理
            print(f"發送訊息失敗: {e}")  # 輸出錯誤資訊到伺服器日誌
            # 回傳 HTTP 400 錯誤狀態碼
            return "Error", 400

# 從Yahoo股市 url 取得股票股利資料
def stock_div(stock_code):
    """
    從Yahoo股市取得股票股利資料

    Args:
        stock_code: 股票代碼

    Returns:
        dict: 包含股價、殖利率等資料的字典，取得失敗則返回 None
    """
    url = f"https://tw.stock.yahoo.com/quote/{stock_code}/dividend"
    # 發送 GET 請求獲取網頁內容
    response = requests.get(url)
    # Http Status Code 200 OK
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # 提取股價，根據 Yahoo 股市網頁結構，上漲、下跌、平盤股價在不同的 class 中
        stock_price_up = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-up)'})
        stock_price_down = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c) C($c-trend-down)'})
        stock_price_flat = soup.find('span', {'class' : 'Fz(32px) Fw(b) Lh(1) Mend(16px) D(f) Ai(c)'})
        # 根據不同的狀態來抓取股價
        if stock_price_up:
            stock_price = float(stock_price_up.text.strip().replace(',', ''))  # 上漲
        elif stock_price_down:
            stock_price = float(stock_price_down.text.strip().replace(',', ''))  # 下跌
        elif stock_price_flat:
            stock_price = float(stock_price_flat.text.strip().replace(',', ''))  # 平盤
        else:
            print(f"{stock_code}未找到股價")
            return None
        # 找到包含股利資料的 <p> 標籤
        dividend_section = soup.find('p', {'class' : 'Mb(20px) Mb(12px)--mobile Fz(16px) Fz(18px)--mobile C($c-primary-text)'})
        if dividend_section:
            # 提取股利資料
            # 找到所有 <span class="Fw(b)"> 標籤，這些標籤包含我們需要的數據
            data_spans = dividend_section.find_all('span', {'class' : 'Fw(b)'})
            # 檢查是否找到足夠的數據
            if len(data_spans) >= 4:
                # 連續發放股利年數
                years_of_dividend = data_spans[0].text.strip()
                # 合計發放股利金額
                total_dividend = data_spans[1].text.strip()
                # 近 5 年平均現金殖利率
                average_dividend_yield = float(data_spans[3].text.strip().replace('%', '')) / 100  # 轉換為小數
                # 顯示抓取到的資料
                # print(f"股票代號: {stock_code}", f"股價: {stock_price}")
                # print(f"連續發放股利年數: {years_of_dividend}")
                # print(f"合計發放股利金額: {total_dividend} 元")
                # print(f"近 5 年平均現金殖利率: {average_dividend_yield}")
                return {
                    "股票代號": stock_code,
                    "股價": stock_price,
                    "連續發放股利年數": years_of_dividend,
                    "合計發放股利金額": total_dividend,
                    "近5年平均現金殖利率": average_dividend_yield
                }
            else:
                print(f"{stock_code}未能找到完整的股利資料")
                return None
        else:
            print(f"{stock_code}未找到股利資料區域")
            return None
    else:
        print(f"{stock_code}無法獲取網頁內容，請檢查網站連接")
        return None

# 計算便宜價、合理價、昂貴價
def calculate_prices(dividend_per_share, target_yield=0.06, market_average_yield=0.038, low_target_yield=0.03):
    """
    基於股息殖利率計算股票的三種價格區間

    Args:
        dividend_per_share (float): 每股股息
        target_yield (float): 目標殖利率，預設 6% (保守型投資者)
        market_average_yield (float): 市場平均殖利率，預設 3.8% (合理價)
        low_target_yield (float): 最低目標殖利率，預設 3% (積極型投資者)

    Returns:
        tuple: (便宜價, 合理價, 昂貴價)
    """
    cheap_price = dividend_per_share / target_yield
    fair_price = dividend_per_share / market_average_yield
    expensive_price = dividend_per_share / low_target_yield
    return cheap_price, fair_price, expensive_price

# 個人設定的目標殖利率
# 根據證交所統計, 台股整體殖利率自 2014 年至 2023 年 7 月近十年的平均為 3.94%, 而自 2018 年至 2023 年 7 月近五年的台股平均殖利率約 3.83%
# 用台灣銀行數位存款利率當最低標準
def 計算股價(stock_code, target_yield=0.06, market_average_yield=0.038, low_target_yield=0.03):
    """
    計算指定股票的三種價格區間（便宜價、合理價、昂貴價）

    Args:
        stock_code (str): 股票代號
        target_yield (float): 目標殖利率，預設 6% (保守型投資者)
        market_average_yield (float): 市場平均殖利率，預設 3.8% (合理價)
        low_target_yield (float): 最低目標殖利率，預設 3% (積極型投資者)

    Returns:
        str: 格式化的價格信息，包含成功或失敗訊息
    """
    stock_data = stock_div(stock_code)
    if stock_data:
        # 計算平均股利
        average_dividend = stock_data["股價"] * stock_data["近5年平均現金殖利率"]
        # calculate_prices(average_dividend, target_yield, market_average_yield, low_target_yield)：

        # 計算便宜價、合理價、昂貴價
        cheap, fair, expensive = calculate_prices(average_dividend, target_yield, market_average_yield, low_target_yield)
        # 顯示價格
        # print(f"股票代號 {stock_code} 的便宜價 : {cheap :.2f} 元")
        # print(f"股票代號 {stock_code} 的合理價 : {fair :.2f} 元")
        # print(f"股票代號 {stock_code} 的昂貴價 : {expensive :.2f} 元")
        return f"股票代號 {stock_code} 的便宜價 : {cheap :.2f} 元, 合理價 : {fair :.2f} 元, 昂貴價 : {expensive :.2f} 元"

    else:
        msg = f"{stock_code}無法獲取股利資料，請檢查股票代號或網路連接"
        print(msg)
        return msg

def is_valid_date(date_str, date_format="%Y%m%d"):
    """
    日期格式驗證函數

    檢查輸入的日期字串是否符合指定格式，預設為台灣常用的 YYYYMMDD 格式

    Args:
        date_str (str): 要驗證的日期字串
        date_format (str): 日期格式，預設為 "%Y%m%d" (西元年月日，無分隔符號)

    Returns:
        bool: 日期格式正確回傳 True，否則回傳 False

    範例:
        is_valid_date("20250731")     # True
        is_valid_date("2025-07-31")   # False (格式不符)
        is_valid_date("20251331")     # False (無效日期)
    """
    try:
        # 嘗試將字串按照指定格式轉換為 datetime 物件
        # 如果轉換成功，表示格式正確；失敗則拋出 ValueError 異常
        datetime.strptime(date_str, date_format)
        return True
    except ValueError:
        # 日期格式錯誤或無效日期時，回傳 False
        return False

# ===== 台灣股票資料處理類別 =====
# 此類別專門處理台灣證券交易所的股票資訊，包含資料取得、處理和分析功能
class TaiwanStockData:
    """
    台灣股票資料處理類別

    負責從台灣證券交易所 API 取得盤後資訊，包含：
    - 個股基本面資料 (本益比、殖利率、股價淨值比等)
    - 資料清理和格式化
    - 股票篩選和排行分析
    - 多日期比較功能

    Attributes:
        date_str (str): 查詢日期字串，格式為 YYYYMMDD
        df (pd.DataFrame): 儲存取得的股票資料

    主要特色：
    - 自動重試機制：若指定日期無資料，會自動往前查找最多10天
    - 資料清理：自動處理千分位逗號和錯誤值
    - 多種分析功能：支援篩選排名、比較變化等
    """

    def __init__(self, date_str):
        """
        建構台灣股票資料處理實例

        初始化時不會自動取得資料，需要額外呼叫 get_stock_data() 方法

        Args:
            date_str (str): 查詢日期字串，格式為西元年月日8碼數字 (例: '20250731')
                           如果日期無資料，系統會自動往前查找最長10天

        Example:
            stock_data = TaiwanStockData('20250731')  # 查詢2025/07/31資料
        """
        self.date_str = date_str  # 儲存查詢日期
        self.df = None  # 初始化為 None，直到呼叫 get_stock_data() 才會設定

    def get_stock_data(self):
        """
        取得台灣股票基本面資訊
        """
        target_date = datetime.strptime(self.date_str, "%Y%m%d")
        max_retries = 10  # 最多往前找10天

        for i in range(max_retries):
            date_str = target_date.strftime("%Y%m%d")
            timestamp = int(time.time() * 1000)
            url = f"https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?date={date_str}&selectType=ALL&response=json&_={timestamp}"
            headers = {'User-Agent': 'Mozilla/5.0'}

            try:
                print(f"正在取得 {date_str} 的台灣股票資訊...")
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # 檢查HTTP錯誤

                # 解析JSON資料
                data = response.json()

                if data.get("stat") == "很抱歉，沒有符合條件的資料!":
                    print(f"{date_str} 沒有資料，嘗試前一天...")
                    target_date -= timedelta(days=1)
                    continue

                if not data or "data" not in data:
                    print(f"{date_str} 未取得任何資料，嘗試前一天...")
                    target_date -= timedelta(days=1)
                    continue

                # 轉換為DataFrame
                self.df = pd.DataFrame(data["data"], columns=data["fields"])
                date = data["date"]
                print(f"成功取得 {date} 的資料")
                
                # 資料清理和轉換
                self.df["收盤價"] = pd.to_numeric(self.df["收盤價"].str.replace(",", ""), errors="coerce")
                self.df['殖利率(%)'] = pd.to_numeric(self.df['殖利率(%)'], errors='coerce')
                self.df['本益比'] = pd.to_numeric(self.df['本益比'], errors='coerce')
                self.df['股價淨值比'] = pd.to_numeric(self.df['股價淨值比'], errors='coerce')

                # 添加資料取得時間
                self.df['DataDate'] = date

                print(f"成功取得 {len(self.df)} 筆股票資料")
                return self.df

            except requests.exceptions.RequestException as e:
                print(f"網路請求錯誤: {e}")
                break # 網路有問題，直接中斷
            except json.JSONDecodeError as e:
                print(f"JSON解析錯誤: {e}")
                # JSON錯誤也可能是查無資料的回應格式不同，嘗試前一天
                target_date -= timedelta(days=1)
            except Exception as e:
                print(f"發生未預期錯誤: {e}")
                break # 其他未預期錯誤，直接中斷
        
        print(f"在過去 {max_retries} 天內都找不到資料。")
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
    
    # 顯示高股息殖利率股票 (前10名)
    def analyze_stock_data_2(self):
        if self.df is None or self.df.empty:
            print("無資料可分析")
            return

        high_dividend = self.df[self.df['殖利率(%)'].notna()].nlargest(10, '殖利率(%)')
        print("\n=== 高股息殖利率股票 (前10名) ===")
        print(high_dividend[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False))

        # 建立結果字串 - 保留原本的表格格式
        result_text = high_dividend[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False)
        result_text += "\n\n=== 價格建議分析 ===\n"

        # 為每只股票計算價格建議
        for idx, stock in high_dividend.iterrows():
            stock_code = stock['證券代號']
            stock_name = stock['證券名稱']
            current_price = stock['收盤價']

            print(f"正在計算股票 {stock_code} {stock_name} 的價格建議...")

            # 計算建議價格
            price_result = 計算股價(stock_code)
            result_text += f"{stock_code} {stock_name} (現價: {current_price:.1f})\n"
            result_text += f"{price_result}\n\n"

        return result_text
    
    # 顯示低P/E比股票 (前10名，排除負值和異常值)    
    def analyze_stock_data_3(self):
        if self.df is None or self.df.empty:
            print("無資料可分析")
            return
        low_pe = self.df[(self.df['本益比'] > 0) & (self.df['本益比'] < 100)].nsmallest(10, '本益比')
        print("\n=== 低P/E比股票 (前10名) ===")
        print(low_pe[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False))
        return low_pe[['證券代號', '證券名稱', '殖利率(%)', '本益比', '股價淨值比']].to_string(index=False)
    
    # def save_to_excel(self, filename):
    #     """
    #     將資料儲存為Excel檔案
    #     Args:
    #         filename: 檔案名稱
    #     """
    #     if self.df is None or self.df.empty:
    #         print("無資料可儲存")
    #         return

    #     try:
    #         self.df.to_excel(filename, index=False, engine='openpyxl')
    #         print(f"\n資料已儲存至: {filename}")
    #     except Exception as e:
    #         print(f"儲存檔案時發生錯誤: {e}")

    # def search_stock(self, code_or_name):
    #     """
    #     搜尋特定股票
    #     Args:
    #         code_or_name: 股票代碼或名稱
    #     """
    #     if self.df is None:
    #         print("尚未取得資料")
    #         return None

    #     result = self.df[
    #         (self.df['證券代號'].str.contains(str(code_or_name), na=False)) |
    #         (self.df['證券名稱'].str.contains(str(code_or_name), na=False))
    #     ]
    #     return result

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

    # @staticmethod
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

            result_text = f"可比較的股票數量: {len(comparison)}\n"

            # 顯示P/E比變化最大的股票
            pe_changes = comparison.dropna(subset=['PE_Change']).nlargest(5, 'PE_Change')
            result_text += "\nP/E比增加最多的股票:\n"
            result_text += pe_changes[['證券代號', '證券名稱', '本益比_1', '本益比_2', 'PE_Change']].to_string(index=False)
            return result_text
        return f"無法取得 {date1} 或 {date2} 的資料進行比較"

# ===== 預定義訊息模板 =====
# 根據不同用戶輸入情境，準備對應的回應訊息

# 主選單說明訊息 (當用戶輸入 '1' 或無法辨識訊息時使用)
mes1 = {
    "type": "text",
    "text": "您好！\n我是股票資訊查詢小幫手,請輸入您欲查詢的代碼[1]或[2]或[3]或[4]或[5]\n1: 個股日本益比、殖利率及股價淨值比\n2. 高股息殖利率股票 (前10名)\n3. 低本益比股票 (前10名)\n4. 比較兩個不同日期的股票資料\n5. 查詢特定日期的股票資料"
}

# 延伸說明訊息 (輸入 '1' 時顯示更多選項)
mes1_1 = {
    "type": "text",
    "text": "查詢單一股票,請回覆4碼股票代碼\n欲查詢特定日期的股票資訊請輸入[5]"
}

# 特定日期查詢格式提示訊息 (輸入 '5' 時顯示)
mes5 = {
    "type": "text",
    "text": "請依格式輸入:\n股票代碼:XXXX\n日期:20250731"
}

# 雙日期比較格式提示訊息 (輸入 '4' 時顯示)
mes4 = {
    "type": "text",
    "text": "請依格式輸入兩個日期:\n日期1:YYYYMMDD\n日期2:YYYYMMDD"
}

# 錯誤訊息模板 (無法辨識用戶輸入時使用)
mes_err = {
    "type": "text",
    "text": "無法辨識您的代碼,請重新輸入"
}

# ===== 主程式入口 =====
# 啟動 Flask Web 伺服器，提供 LINE Bot webhook 服務
if __name__ == "__main__":
    app.run(port=port)
