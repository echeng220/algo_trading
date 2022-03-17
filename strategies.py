from tkinter import N
from matplotlib.pyplot import plot
from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.technical import ma
from pyalgotrade.stratanalyzer import returns, drawdown, trades, sharpe

from utils import *

last_days_of_month = get_last_days_of_month('NYSE', '2000-01-01', '2022-03-11')

class BuyAndHoldStrategy(strategy.BacktestingStrategy):
    """
    Buy and hold a given instrument for duration of backtest.
    """
    def __init__(self, feed, instrument, cash=10000):
        super(BuyAndHoldStrategy, self).__init__(feed, cash)
        self._instrument = instrument
        self.position = None
        self.setUseAdjustedValues(True)

    def onEnterOk(self, position):
        '''Get notified when position was filled.'''
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f'----- BUY at {exec_info.getPrice()} ({exec_info.getQuantity()} shares)')
        return super().onEnterOk(position)

    def onExitOk(self, position):
        '''Get notified when position was closed.'''
        exec_info = position.getExitOrder().getExecutionInfo()
        self.info(f'----- SELL at {exec_info.getPrice()}')
        return super().onExitOk(position)

    def onBars(self, bars):
        '''Buy if no position is currently held.'''
        # Exit function if moving average is not available
        if self.ma[-1] is None:
            return

        bar = bars[self._instrument]
        close = bar.getAdjClose()

        if self.position is None:
            # Set broker
            broker = self.getBroker()
            # Apply buffer factor (0.95) to cash to ensure sufficient cash to fill positions
            cash = broker.getCash() * 0.95

            # Enter long position if not already in one
            quantity = cash / close
            self.info(f'Buying at ${close}')
            self.position = self.enterLong(self._instrument, quantity)
    

class SMA200_Strategy(strategy.BacktestingStrategy):
    """
    200 day moving average trading strategy. Buy if price is greater than
    moving average at end of month, sell if price is lower than moving
    average at end of month.
    """
    def __init__(self, feed, instrument, cash=10000):
        super(SMA200_Strategy, self).__init__(feed, cash)
        self._instrument = instrument
        self.position = None
        self.setUseAdjustedValues(True)
        # Calculate 200-day moving average (all at once)
        self.ma = ma.SMA(feed[instrument].getAdjCloseDataSeries(), 200)

    def onEnterOk(self, position):
        '''Get notified when position was filled.'''
        exec_info = position.getEntryOrder().getExecutionInfo()
        self.info(f'----- BUY at {exec_info.getPrice()} ({exec_info.getQuantity()} shares)')
        return super().onEnterOk(position)

    def onExitOk(self, position):
        '''Get notified when position was closed.'''
        exec_info = position.getExitOrder().getExecutionInfo()
        self.info(f'----- SELL at {exec_info.getPrice()}')
        return super().onExitOk(position)

    def onBars(self, bars):
        '''Check if trade should be executed on a given bar (day) of data.'''
        # Exit function if moving average is not available
        if self.ma[-1] is None:
            return

        bar = bars[self._instrument]
        close = bar.getAdjClose()
        date = bar.getDateTime().date().isoformat()

        if date in last_days_of_month:
            if self.position is None:
                # Set broker
                broker = self.getBroker()
                # Apply buffer factor (0.95) to cash to ensure sufficient cash to fill positions
                cash = broker.getCash() * 0.95

                # Enter long position if closing price greater than 200-day MA
                if close > self.ma[-1]:
                    quantity = cash / close
                    self.info(f'Buying at ${close}, which is above ${self.ma[-1]}')
                    self.position = self.enterLong(self._instrument, quantity)

            # Exit long position if closing price less than 200-day MA
            elif close < self.ma[-1] and self.position is not None:
                self.info(f'Selling at ${close}, which is below ${self.ma[-1]}')
                self.position.exitMarket()
                self.position = None

if __name__ == '__main__':
    ticker = 'spy'
    start_date = '2000-01-01'
    end_date = '2022-03-01'

    # Define feed
    feed = create_feed(ticker, start_date, end_date)

    # Instantiate strategy
    strategy = SMA200_Strategy(feed, ticker)

    # Instantiate and attach analyzers to strategy
    return_analyzer = returns.Returns()
    sharpe_analyzer = sharpe.SharpeRatio()
    drawdown_analyzer = drawdown.DrawDown()
    trade_analyzer = trades.Trades()

    strategy.attachAnalyzer(return_analyzer)
    strategy.attachAnalyzer(sharpe_analyzer)
    strategy.attachAnalyzer(drawdown_analyzer)
    strategy.attachAnalyzer(trade_analyzer)

    # Instantiate plotter
    plt = plotter.StrategyPlotter(strategy)
    plt.getInstrumentSubplot(ticker).addDataSeries('200-day MA', strategy.ma)

    # Run strategy and plot results
    strategy.run()
    plt.plot()
    plt.savePlot(f'backtests\\{type(strategy).__name__}_{strategy._instrument.upper()}_({start_date}-{end_date}).png')

    # Log results
    log_backtest(
        strategy,
        return_analyzer,
        sharpe_analyzer,
        drawdown_analyzer,
        trade_analyzer,
        start_date,
        end_date
    )
