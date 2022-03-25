import yfinance as yf

def get_ticker_data(ticker, start_date, end_date, interval='1d'):
    '''Get historical data from Yahoo Finance.'''
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

    data.to_csv(f'data\\{ticker.upper().replace(".", "-")}_({interval})_({start_date}-{end_date}).csv')

if __name__ == '__main__':
    get_ticker_data('^VIX', '2022-03-10', '2022-03-17', '1h')