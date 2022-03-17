import yfinance as yf

def get_ticker_data(ticker, start_date, end_date):
    '''Get historical data from Yahoo Finance.'''
    data = yf.download(ticker, start=start_date, end=end_date)

    data.to_csv(f'data\\{ticker.upper().replace(".", "-")}_({start_date}-{end_date}).csv')