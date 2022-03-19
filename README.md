# Introduction
This repo is a collection of algorithmic trading strategies, along with functions to backtest them, log results of the backtests, visualize the backtests, and compare backtests.

This repo will focus on mean reversion algorithms.

# Modules
## import_data.py
Uses yfinance to retrieve historical stock information.
## utils.py
Support functions to create data feeds, run strategy backtests, log results, visualize results, etc.
## strategies.py
Strategy definitions and logic for various mean reversion strategies.

# Algorithms
The algorithms I am currently testing and playing with are listed below.
## Buy & Hold
This is not a trading strategy, but a benchmark to compare strategies to.

## 200-Day Moving Average
This algorithm was borrowed from Part Time Larry, who runs an awesome algorithmic trading channel on [YouTube](https://www.youtube.com/c/parttimelarry). Part Time Larry got the idea from Steve Burns, who wrote a cool [article](https://www.newtraderu.com/2021/06/30/200-day-moving-average-vs-buy-and-hold/) on how he used this strategy to beat the S&P 500.

## Bollinger Bands
The *pyalgotrade* documentation has this trading strategy. It uses a low Bollinger Band as a buying signal.

## Double 7's
This algorithm was taken from David Fiancan's YouTube [video](https://www.youtube.com/watch?v=_9Bmxylp63Y), which gets the algorithm from Larry Connor's book *Short Term Trading Strategies That Work*.

# Interesting Reads & Resources
## Alpaca List of Ultimate Trading Strategies:
The following articles are great overviews of the broad categories of algorithmic trading strategies.
- [Part 1](https://medium.com/automation-generation/ultimate-list-of-automated-trading-strategies-you-should-know-part-1-c9a333f58930)
- [Part 2](https://medium.com/p/88184b27cd60)
- [Part 3](https://medium.com/p/25d580ccab0c)

## Basics of Mean Reversion (Dr. Ernest Chan)
This [video](https://www.youtube.com/watch?v=5G7YdjnRvVI) is a really well-presented introduction to the concept of mean reversion.