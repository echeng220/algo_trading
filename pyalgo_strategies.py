from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.technical import ma, bollinger, highlow, rsi, cross
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
    def __init__(self, feed, instrument, cash=10000):
        super(Double7Strategy, self).__init__(feed, cash)
        self.instrument = instrument
        self.position = None
        self.setUseAdjustedValues(True)

        self.ma = ma.SMA(feed[instrument].getAdjCloseDataSeries(), 200)
        self.instrument_high = highlow.High(feed[instrument].getAdjCloseDataSeries(), 7)
        self.instrument_low = highlow.Low(feed[instrument].getAdjCloseDataSeries(), 7)

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
        if self.ma[-1] is None:
            return

        shares = self.getBroker().getShares(self.instrument)
        bar = bars[self.instrument]
        close = bar.getAdjClose()

        if close > self.ma[-1]:
            if shares == 0 and close <= self.instrument_low[-1]:
                quantity = int(self.getBroker().getCash(False) / close)
                self.position = self.enterLong(self.instrument, quantity)
            elif shares > 0 and close >= self.instrument_high[-1]:
                self.position.exitMarket()

class VIX10Strategy(strategy.BacktestingStrategy):
    """
    Buy if VIX is >5% above 10-day moving average.
    """
    def __init__(self, feed, vix, instrument, cash=10000):
        super(VIX10Strategy, self).__init__(feed, cash)
        self.instrument = instrument
        self.vix = vix
        self.position = None
        self.setUseAdjustedValues(True)
        # Calculate 200-day moving average (all at once)
        self.ma = ma.SMA(feed[self.instrument].getAdjCloseDataSeries(), 200)
        self.vix_ma = ma.SMA(feed[self.vix].getAdjCloseDataSeries(), 10)

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
        if self.vix_ma[-1] is None or self.ma[-1] is None:
            return

        vix_bar = bars.getBar(self.vix)
        vix_close = vix_bar.getAdjClose()
        
        bar = bars.getBar(self.instrument)
        close = bar.getAdjClose()
        date = bar.getDateTime().date().isoformat()

        if date in last_days_of_month:

        # Ensure closing price is greater than 200-day MA
            if close > self.ma[-1]:
                # Set broker
                broker = self.getBroker()
                # Apply buffer factor (0.95) to cash to ensure sufficient cash to fill positions
                cash = broker.getCash() * 0.95

                # Enter long position if VIX > 5% of 10-day MA
                if vix_close > self.vix_ma[-1] * 1.05 and cash > close:
                    quantity = 0.5 * cash / close
                    self.info(f'Buying at ${close}, which is above ${self.ma[-1]}')
                    self.position = self.enterLong(self.instrument, quantity)
                elif vix_close < self.vix_ma[-1] * 1.05 and self.position is not None:
                        self.info(f'Selling at ${close}, which is below ${self.ma[-1]}')
                        self.position.exitMarket()
                        self.position = None

            # Sell if price is below 200-day MA
            else:
                if self.position is not None:
                    # Exit long position if closing price less than 10-day MA
                    if vix_close < self.vix_ma[-1] * 1.05 and self.position is not None:
                        self.info(f'Selling at ${close}, which is below ${self.ma[-1]}')
                        self.position.exitMarket()
                        self.position = None

class RSI2Strategy(strategy.BacktestingStrategy):
    def __init__(
            self, feed, instrument,
            entry_ma_interval=200, exit_ma_interval=5,
            rsi_period=2, overbought_threshold=90, oversold_threshold=10, 
            cash=10000):
        super(RSI2Strategy, self).__init__(feed, cash)
        self.instrument = instrument
        self.index = index
        self.position = None
        self.setUseAdjustedValues(True)

        self.instrument_price = feed[self.instrument].getPriceDataSeries()
        self.entry_ma = ma.SMA(self.instrument_price, entry_ma_interval)
        self.exit_ma = ma.SMA(self.instrument_price, exit_ma_interval)
        self.rsi = rsi.RSI(self.instrument_price, rsi_period)

        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

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

    def enterLongSignal(self, bar):
        signal = bar.getPrice() > self.entry_ma[-1] and self.rsi[-1] <= self.oversold_threshold
        return signal

    def exitLongSignal(self):
        signal = cross.cross_above(self.instrument_price, self.exit_ma)
        return signal

    def onBars(self, bars):
        ''''''
        # Take no action if no moving average
        if self.entry_ma[-1] is None or self.exit_ma[-1] is None or self.rsi[-1] is None:
            return

        bar = bars[self.instrument]
        price = bar.getPrice()
        shares = self.getBroker().getShares(self.instrument)
        close = bar.getAdjClose()

        if self.position is not None:
            if self.exitLongSignal():
                self.position.exitMarket()
                self.position = None
        else:
            if self.enterLongSignal(bar):
                cash = self.getBroker().getCash() * 0.9
                quantity = int(cash / price)
                self.position = self.enterLong(self.instrument, quantity)

if __name__ == '__main__':
    index = 'spy'
    ticker = 'spy'
    start_date = '2019-01-01'
    end_date = '2022-03-17'
    event = 'covid-19'

    if event in MAJOR_EVENTS:
        start_date = MAJOR_EVENTS[event]['start_date']
        end_date = MAJOR_EVENTS[event]['end_date']

    # Define feed
    # feed = create_feed([ticker], start_date, end_date)
    feed = create_feed([ticker, '^VIX'], start_date, end_date)

    # Instantiate strategy
    #* Buy & Hold
    # strategy = BuyAndHoldStrategy(feed, ticker)
    #* 200 Day Moving Average
    # strategy = SMA200Strategy(feed, ticker)
    #* Bollinger Bands
    # strategy = BollingerStrategy(feed, ticker)
    #* Double 7's
    # strategy = Double7Strategy(feed, ticker)
    #* VIX 10 Day Moving Average
    # strategy = VIX10Strategy(feed, '^VIX', ticker)
    #* 2-Day RSI Strategy
    strategy = RSI2Strategy(feed, ticker)

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
    # plt.getInstrumentSubplot(ticker).addDataSeries('200-day market MA', strategy.ma)
    # plt.getInstrumentSubplot(ticker).addDataSeries(f'7-day high ({ticker})', strategy.instrument_high)
    # plt.getInstrumentSubplot(ticker).addDataSeries(f'7-day low ({ticker})', strategy.instrument_low)
    #* VIX 10 Day Moving Average
    # plt.getOrCreateSubplot('^VIX').addDataSeries('VIX', feed[strategy.vix].getAdjCloseDataSeries())
    # plt.getOrCreateSubplot('^VIX').addDataSeries('10-day VIX MA', strategy.vix_ma)
    #* 2-Day RSI Strategy
    plt.getInstrumentSubplot(ticker).addDataSeries("Entry SMA", strategy.entry_ma)
    plt.getInstrumentSubplot(ticker).addDataSeries("Exit SMA", strategy.exit_ma)
    plt.getOrCreateSubplot("rsi").addDataSeries("RSI", strategy.rsi)
    plt.getOrCreateSubplot("rsi").addLine("Overbought", strategy.overbought_threshold)
    plt.getOrCreateSubplot("rsi").addLine("Oversold", strategy.oversold_threshold)

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
