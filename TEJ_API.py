import pandas as pd
import tejapi
import os

def get_tej_data(stock_id, start_date, end_date):
    """
    使用 TEJ API 獲取指定股票的歷史股價資料
    Args:
        stock_id (str): 股票代碼，例如 '0050'
        start_date (str): 開始日期，格式為 'YYYY-MM-DD'
        end_date (str): 結束日期，格式為 'YYYY-MM-DD'
    Returns:
        pandas.DataFrame: 包含股價資料的 DataFrame，如果失敗則返回 None。
    """
    try:
        # 使用 tejapi.get 獲取資料
        df = tejapi.get('TRAIL/TAPRCD',
                        coid=stock_id,
                        mdate={'gte': start_date, 'lte': end_date},
                        paginate=True) # 移除 opts.columns 參數，嘗試獲取所有預設欄位

        if df is not None and not df.empty:
            # 將 mdate 轉換為日期格式
            df['mdate'] = pd.to_datetime(df['mdate'])
            return df
        else:
            print("錯誤：未從 TEJ API 獲取到資料。")
            return None

    except Exception as e:
        print(f"TEJ API 請求失敗: {e}")
        return None

if __name__ == '__main__':
    # 請將 "YOUR_API_KEY" 替換成您在 TEJ 申請的 API 金鑰
    TEJ_API_KEY = "eOmUaVtwjybkD04br68SiyoJC2QMRu"
    if TEJ_API_KEY == "YOUR_API_KEY":
        print("請記得將 'YOUR_API_KEY' 替換成您在 TEJ 申請的 API 金鑰！")
    else:
        tejapi.ApiConfig.api_key = TEJ_API_KEY
        info = tejapi.ApiConfig.info()
        print("TEJ API 金鑰資訊:")
        print(info)

        # 嘗試使用 coid 篩選條件獲取資料
        try:
            # 使用 'TRAIL/TAPRCD' 並篩選 'Y9999' (台灣加權股價指數)
            stock_data = tejapi.get('TRAIL/TAPRCD', coid='Y9999', paginate=True)
            if stock_data is not None and not stock_data.empty:
                print("成功抓取 TRAIL/TAPRCD 中 'Y9999' 的資料：")
                print(stock_data.head())
                print("\n資料欄位:")
                print(stock_data.columns.tolist())
            else:
                print("錯誤：未從 TEJ API 獲取到 'Y9999' 的資料。")
        except Exception as e:
            print(f"TEJ API 請求失敗 (coid='Y9999'): {e}")
