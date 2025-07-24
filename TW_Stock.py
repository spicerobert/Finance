import twstock as tw
import pandas as pd

stock=tw.realtime.get('1605')
result=pd.DataFrame(stock).T.iloc[1:3]
#result.columns = ['股票代碼', '地區', '股票名稱', '公司全名','現在時間', '最新成交價', '成交量', '累計成交量', '最佳5檔委買價', '最佳5檔委買量', '最佳5檔委賣價', '最佳5檔委賣量', '開盤價', '最高價', '最低價']
print(result)






