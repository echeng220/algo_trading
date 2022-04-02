import backtrader as bt

from utils import *
from strategies import *

def orchestrate_test(strategy, tickers, start_date, end_date, cash=10000.0, commission=0.001):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy)

    cerebro.broker.setcash(cash)
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission)
    cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, _name='rolling_returns')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')

    # Create feed
    bt_create_feed(cerebro, tickers, start_date, end_date)

    # Run backtest
    results = cerebro.run()

    # Plot backtest results
    fig = cerebro.plot()
    plot_name = f'backtests\\{results[0].params.name}_({start_date}-{end_date}).png'
    fig[0][0].savefig(plot_name)

    # Save backtest results
    bt_log_backtest(results, start_date, end_date)

if __name__ == '__main__':
    tickers = ['SPY']
    start_date = '2001-01-01'
    end_date =  '2022-03-31'

    orchestrate_test(SMA200Strategy, tickers, start_date, end_date)
