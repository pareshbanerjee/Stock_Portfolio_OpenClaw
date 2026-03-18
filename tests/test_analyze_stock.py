import builtins
from unittest.mock import patch
import pandas as pd

from main import analyze_stock


def make_hist(close_values):
    # create a pandas DataFrame with Close column and index
    return pd.DataFrame({'Close': close_values})


@patch('yfinance.Ticker')
def test_analyze_stock_buy(mock_ticker):
    # trending up low volatility -> buy
    hist = make_hist([100, 102, 103, 105, 108])
    instance = mock_ticker.return_value
    instance.history.return_value = hist

    res = analyze_stock('FAKE')
    assert res['ticker'] == 'FAKE'
    assert 'last_price' in res
    assert res['recommendation'] in ('buy', 'hold')


@patch('yfinance.Ticker')
def test_analyze_stock_sell(mock_ticker):
    # trending down high volatility -> sell
    hist = make_hist([200, 180, 160, 140, 120])
    instance = mock_ticker.return_value
    instance.history.return_value = hist

    res = analyze_stock('FAKE')
    assert res['ticker'] == 'FAKE'
    assert 'last_price' in res
    assert res['recommendation'] in ('sell', 'hold')


@patch('yfinance.Ticker')
def test_analyze_stock_fallback(mock_ticker):
    # simulate yfinance throwing an exception
    instance = mock_ticker.return_value
    instance.history.side_effect = Exception('no data')

    res = analyze_stock('FAKE')
    assert res.get('ticker') == 'FAKE'
    assert res.get('recommendation') == 'hold'
