import os
import json
from datetime import datetime
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
    '''Write results of backtest to .json file.'''

    # Backtest metadata
    strategy_name = type(strategy).__name__
    instrument = strategy.instrument.upper()
    test_date = datetime.today().strftime('%Y-%m-%d')

    log_dict = {
            'strategy': str(strategy_name),
            'instrument': instrument,
            'start_date': start_date,
            'end_date': end_date,
            'run_date': test_date,
            'final_portfolio_value_$': strategy.getResult(),
            'cumulative_returns_%': return_analyzer.getCumulativeReturns()[-1] * 100,
            'sharpe_ratio': sharpe_analyzer.getSharpeRatio(0.05),
            'max_drawdown_%': drawdown_analyzer.getMaxDrawDown() * 100,
            'longest_drawdown_duration': str(drawdown_analyzer.getLongestDrawDownDuration()),
            'total_trades': trade_analyzer.getCount()
    }

    if trade_analyzer.getCount() > 0:
        profits = trade_analyzer.getAll()
        log_dict.update(
            {
                'avg_profit_$': profits.mean(),
                'profit_std_$': profits.std(),
                'max_profit_$': profits.max(),
                'min_profit_$': profits.min()
            }
        )
        
        returns = trade_analyzer.getAllReturns()
        log_dict.update(
            {
                'avg_return_%': returns.mean() * 100,
                'return_std_%': returns.std() * 100,
                'max_return_%': returns.max() * 100,
                'min_return_%': returns.min() * 100
            }
        )

    if trade_analyzer.getProfitableCount() > 0:
        profits = trade_analyzer.getProfits()
        returns = trade_analyzer.getPositiveReturns()

        log_dict.update(
            {
                'profitable_trades': {
                    'number_of_trades': trade_analyzer.getProfitableCount(),
                    'avg_profit_$': profits.mean(),
                    'profit_std_$': profits.std(),
                    'max_profit_$': profits.max(),
                    'min_profit_$': profits.min(),
                    'avg_return_%': returns.mean() * 100,
                    'return_std_%': returns.std() * 100,
                    'max_return_%': returns.max() * 100,
                    'min_return_%': returns.min() * 100
                }
            }
        )

    if trade_analyzer.getUnprofitableCount() > 0:
        losses = trade_analyzer.getLosses()
        returns = trade_analyzer.getNegativeReturns()

        log_dict.update(
            {
                'unprofitable_trades': {
                    'number_of_trades': trade_analyzer.getUnprofitableCount(),
                    'avg_profit_$': losses.mean(),
                    'profit_std_$': losses.std(),
                    'max_profit_$': losses.max(),
                    'min_profit_$': losses.min(),
                    'avg_return_%': returns.mean() * 100,
                    'return_std_%': returns.std() * 100,
                    'max_return_%': returns.max() * 100,
                    'min_return_%': returns.min() * 100
                }
            }
        )

    with open(f'backtests\\{strategy_name}_{instrument}_({start_date}-{end_date}).json', 'w') as f:
        json.dump(log_dict, f, indent=4)

def flatten_dict(d, parent_key='', sep='.'):
    '''Recursively flatten nested dictionary.'''
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        try:
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        except:
            items.append((new_key, v))
    return dict(items)

def compare_backtests(list_of_logs, sheet_name):
    '''Combine logs into dataframe.'''
    logs = []

    for log in list_of_logs:
        with open(log) as f:
            log_data = json.load(f)
            flattened_log = flatten_dict(log_data)
        logs.append(flattened_log)

    # Convert backtest logs to dataframe with multiindex
    df = pd.DataFrame(logs).transpose()
    df.index = pd.MultiIndex.from_tuples([tuple(k.split('.')) if '.' in k else ('summary', k) for k,v in df.iterrows()])

    df.to_excel(f'backtests\\{sheet_name}BacktestComparison.xlsx')

    return df

def get_last_days_of_month(exchange, start_date, end_date):
    '''Retrieve last day of month over specified period using market calendar.'''
    exchange = market_calendar.get_calendar(exchange)
    df = exchange.schedule(start_date=start_date, end_date=end_date)
    
    # Get last day of each month
    df = df.groupby(df.index.strftime('%Y-%m')).tail(1)

    df['date'] = pd.to_datetime(df['market_open']).dt.date
    last_days_of_month = [date.isoformat() for date in df['date'].tolist()]
    return last_days_of_month

if __name__ == '__main__':
    dir_path = r'C:\Users\Evan\Desktop\projects\algo_trading\backtests'

    json_logs = [f'{dir_path}\\{file}' for file in os.listdir(dir_path) if file.endswith('.json')]

    df = compare_backtests(json_logs, 'SPYStrategy')
    print(df)