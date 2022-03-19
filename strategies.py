from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.technical import ma, bollinger, highlow
from pyalgotrade.stratanalyzer import returns, drawdown, trades, sharpe

from utils import *

last_days_of_month = get_last_days_of_month('NYSE', '2000-01-01', '2022-03-11')

class BuyAndHoldStrategy(strategy.BacktestingStrategy):
    """
    Buy and hold a given instrument for duration of backtest.
    """
    def __init__(self, feed, instrument, cash=10000):
        super(BuyAndHoldStrategy, self).__init__(feed, cash)
        self.instrument = instrument
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
        bar = bars[self.instrument]
        close = bar.getAdjClose()

        if self.position is None:
            # Set broker
            broker = self.getBroker()
            # Apply buffer factor (0.95) to cash to ensure sufficient cash to fill positions
            cash = broker.getCash() * 0.95

            # Enter long position if not already in one
            quantity = cash / close
            self.info(f'Buying at ${close}')
            self.position = self.enterLong(self.instrument, quantity)
    

class SMA200Strategy(strategy.BacktestingStrategy):
    """
    200 day moving average trading strategy. Buy if price is greater than
    moving average at end of month, sell if price is lower than moving
    average at end of month.
    """
    def __init__(self, feed, instrument, cash=10000):
        super(SMA200Strategy, self).__init__(feed, cash)
        self.instrument = instrument
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

        bar = bars[self.instrument]
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
                    self.position = self.enterLong(self.instrument, quantity)

            # Exit long position if closing price less than 200-day MA
            elif close < self.ma[-1] and self.position is not None:
                self.info(f'Selling at ${close}, which is below ${self.ma[-1]}')
                self.position.exitMarket()
                self.position = None

class BollingerStrategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, bBandsPeriod=40, cash=10000):
        super(BollingerStrategy, self).__init__(feed, cash)
        self.instrument = instrument
        self.position = None
        self.setUseAdjustedValues(True)
        self.bbands = bollinger.BollingerBands(feed[instrument].getAdjCloseDataSeries(), bBandsPeriod, 2)

    def getBollingerBands(self):
        return self.bbands

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
        '''Buy on the break of the lower Bollinger Band.'''
        lower = self.bbands.getLowerBand()[-1]
        upper = self.bbands.getUpperBand()[-1]

        # Take no action if no lower Bollinger Band
        if lower is None:
            return

        shares = self.getBroker().getShares(self.instrument)
        bar = bars[self.instrument]
        close = bar.getAdjClose()

        # Enter long position if stock closes below lower band
        if shares == 0 and close < lower:
            quantity = int(self.getBroker().getCash(False) / close)
            self.position = self.enterLong(self.instrument, quantity)
        # Close long position if stock closes above upper band
        elif shares > 0 and close > upper:
            self.position.exitMarket()

class Double7Strategy(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, index, cash=10000):
        super(Double7Strategy, self).__init__(feed, cash)
        self.instrument = instrument
        self.index = index
        self.position = None
        self.setUseAdjustedValues(True)

        self.index_ma = ma.SMA(feed[index].getAdjCloseDataSeries(), 200)
        self.instrument_high = highlow.High(feed[instrument].getAdjCloseDataSeries(), 7)
        self.instrument_low = highlow.Low(feed[instrument].getAdjCloseDataSeries(), 7)

        # TODO: Add stop loss?

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
        ''''''
        # Take no action if no moving average
        if self.index_ma[-1] is None:
            return

        shares = self.getBroker().getShares(self.instrument)
        bar = bars[self.instrument]
        close = bar.getAdjClose()

        if close > self.index_ma[-1]:
            if shares == 0 and close <= self.instrument_low[-1]:
                quantity = int(self.getBroker().getCash(False) / close)
                self.position = self.enterLong(self.instrument, quantity)
            elif shares > 0 and close >= self.instrument_high[-1]:
                self.position.exitMarket()


if __name__ == '__main__':
    index = 'spy'
    ticker = 'spy'
    start_date = '2000-01-01'
    end_date = '2022-03-17'

    # Define feed
    feed = create_feed(ticker, start_date, end_date)

    # Instantiate strategy
    #* Buy & Hold
    # strategy = BuyAndHoldStrategy(feed, ticker)
    #* 200-Day Moving Average
    # strategy = SMA200Strategy(feed, ticker)
    #* Bollinger Bands
    # strategy = BollingerStrategy(feed, ticker)
    #* Double 7's
    strategy = Double7Strategy(feed, ticker, index)

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
    #* 200 Day Moving Average
    # plt.getInstrumentSubplot(ticker).addDataSeries('200-day MA', strategy.ma)
    #* Bollinger Bands
    # plt.getInstrumentSubplot(ticker).addDataSeries("Upper", strategy.getBollingerBands().getUpperBand())
    # plt.getInstrumentSubplot(ticker).addDataSeries("Middle", strategy.getBollingerBands().getMiddleBand())
    # plt.getInstrumentSubplot(ticker).addDataSeries("Lower", strategy.getBollingerBands().getLowerBand())
    #* Double 7's
    plt.getInstrumentSubplot(index).addDataSeries('200-day market MA', strategy.index_ma)
    plt.getInstrumentSubplot(ticker).addDataSeries(f'7-day high ({ticker})', strategy.instrument_high)
    plt.getInstrumentSubplot(ticker).addDataSeries(f'7-day low ({ticker})', strategy.instrument_low)

    # Run strategy and plot results
    strategy.run()
    plt.plot()
    plt.savePlot(f'backtests\\{type(strategy).__name__}_{strategy.instrument.upper()}_({start_date}-{end_date}).png')

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
