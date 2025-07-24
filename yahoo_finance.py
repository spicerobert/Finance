import yfinance as yf
import matplotlib.pyplot as plt

stock_symbol = '0050.tw'
start_date = '2025-01-01'
end_date = '2025-12-31'

data = yf.download(
    tickers=["2332.tw"],
    start="2025-01-01",
    end="2025-12-31",
    interval="1d",
    group_by="ticker",
)
data = yf.download(stock_symbol, start=start_date, end=end_date)

# 顯示數據的前幾行
print(data.head())
plt.figure(figsize=(10, 5))
plt.plot(data['Close'], label='Close Price')
plt.title(f'{stock_symbol} Stock Price')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.show()