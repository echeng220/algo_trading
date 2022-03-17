from datetime import datetime
from tracemalloc import start
import pandas as pd
import pandas_market_calendars as market_calendar

from pyalgotrade.barfeed import yahoofeed
from pyalgotrade import plotter

from import_data import get_ticker_data

def create_feed(ticker, start_date, end_date):
    '''Check for .csv data for given ticker and date range.
    Retrieve data from Yahoo Finance if not available.
    Add bars from .csv to feed.'''
    feed = yahoofeed.Feed()
    try:
        feed.addBarsFromCSV(ticker, f'data\\{ticker.upper()}_({start_date}-{end_date}).csv')
        return feed
    except FileNotFoundError:
        get_ticker_data(ticker, start_date, end_date)
        feed.addBarsFromCSV(ticker, f'data\\{ticker.upper()}_({start_date}-{end_date}).csv')
        return feed

def log_backtest(strategy, return_analyzer, sharpe_analyzer, drawdown_analyzer, trade_analyzer, start_date, end_date):
    '''Write results of backtest to .txt file.'''

    # Backtest metadata
    strategy_name = type(strategy).__name__
    instrument = strategy._instrument.upper()
    test_date = datetime.today().strftime('%Y-%m-%d')

    summary_logs = [
        "******* BACKTEST RUN DATA *******",
        f"Strategy: {strategy_name}\nInstrument: {instrument}",
        f"Start Date: {start_date}\nEnd Date: {end_date}\n",
        f"Backtest ran on {test_date}\n",
        "---SUMMARY---",
        f"Final portfolio value: ${round(strategy.getResult(), 2)}",
        f"Cumulative returns: ${round(return_analyzer.getCumulativeReturns()[-1] * 100)} %",
        f"Sharpe ratio: {round(sharpe_analyzer.getSharpeRatio(0.05))}",
        f"Max. drawdown: {round(drawdown_analyzer.getMaxDrawDown() * 100, 2)} %",
        f"Longest drawdown duration: {drawdown_analyzer.getLongestDrawDownDuration()}\n"
    ]

    trade_logs = [
        "---TRADE ANALYSIS---",
        f"Total trades: {trade_analyzer.getCount()}",
    ]

    if trade_analyzer.getCount() > 0:
        profits = trade_analyzer.getAll()
        profit_logs = [
            "-PROFIT-",
            f"Avg. profit: ${round(profits.mean(), 2)}",
            f"Profits std. dev.: ${round(profits.std(), 2)}",
            f"Max. profit: ${round(profits.max(), 2)}",
            f"Min. profit: ${round(profits.min(), 2)}\n"
        ]
        trade_logs += profit_logs
        
        returns = trade_analyzer.getAllReturns()
        returns_logs = [
            "-RETURNS-",
            f"Avg. return: {round(returns.mean() * 100, 2)} %",
            f"Returns std. dev.: {round(returns.std() * 100, 2)} %",
            f"Max. return: {round(returns.max() * 100, 2)} %",
            f"Min. return: {round(returns.min() * 100, 2)} %\n"
        ]
        trade_logs += returns_logs


    if trade_analyzer.getProfitableCount() > 0:
        profits = trade_analyzer.getProfits()
        returns = trade_analyzer.getPositiveReturns()

        profitable_logs = [
            "---PROFITABLE TRADES---",
            f"Profitable trades: {trade_analyzer.getProfitableCount()}",
            f"Avg. profit: ${round(profits.mean(), 2)}",
            f"Profits std. dev.: ${round(profits.std(), 2)}",
            f"Max. profit: ${round(profits.max(), 2)}",
            f"Min. profit: ${round(profits.min(), 2)}",
            "---",
            f"Avg. return: {round(returns.mean() * 100, 2)} %",
            f"Returns std. dev.: {round(returns.std() * 100, 2)} %",
            f"Max. return: {round(returns.max() * 100, 2)} %",
            f"Min. return: {round(returns.min() * 100, 2)} %\n"
        ]

    if trade_analyzer.getUnprofitableCount() > 0:
        losses = trade_analyzer.getLosses()
        returns = trade_analyzer.getNegativeReturns()

        unprofitable_logs = [
            "---UNPROFITABLE TRADES---",
            f"Unprofitable trades: {trade_analyzer.getUnprofitableCount()}",
            f"Avg. loss: ${round(losses.mean(), 2)}",
            f"Losses std. dev.: ${round(losses.std(), 2)}",
            f"Max. loss: ${round(losses.min(), 2)}",
            f"Min. loss: ${round(losses.max(), 2)}",
            "---",
            f"Avg. return: {round(returns.mean() * 100, 2)} %",
            f"Returns std. dev.: {round(returns.std() * 100, 2)} %",
            f"Max. return: {round(returns.max() * 100, 2)} %",
            f"Min. return: {round(returns.min() * 100, 2)} %\n"
        ]

    logs = summary_logs + trade_logs + profit_logs + profitable_logs + unprofitable_logs

    with open(f'backtests\\{strategy_name}_{instrument}_({start_date}-{end_date}).txt', 'w') as f:
        for line in logs:
            f.write(line)
            f.write('\n')

def get_last_days_of_month(exchange, start_date, end_date):
    '''Retrieve last day of month over specified period using market calendar.'''
    exchange = market_calendar.get_calendar(exchange)
    df = exchange.schedule(start_date=start_date, end_date=end_date)
    
    # Get last day of each month
    df = df.groupby(df.index.strftime('%Y-%m')).tail(1)

    df['date'] = pd.to_datetime(df['market_open']).dt.date
    last_days_of_month = [date.isoformat() for date in df['date'].tolist()]
    return last_days_of_month