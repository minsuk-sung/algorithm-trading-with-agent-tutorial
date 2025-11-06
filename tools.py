"""
Cryptocurrency Trading Tools for Binance Futures
"""

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
from typing import Optional
from dotenv import load_dotenv
import pandas as pd
import ccxt
import os
import json

# Load environment variables
load_dotenv()

# Initialize Binance exchange
binance_exchange = ccxt.binance(config={
    'apiKey': os.getenv('BINANCE_API_KEY'),
    'secret': os.getenv('BINANCE_SECRET_KEY'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

# Initialize Tavily search
_tavily_search = TavilySearchResults(
    max_results=5,
    include_answer=True,
    include_raw_content=False,
)

################################################################################################################
# Helper Functions
################################################################################################################

def _fetch_ohlcv_dataframe(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Internal helper to fetch OHLCV data and convert to DataFrame"""
    ohlcv_data = binance_exchange.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    pd_ts = pd.to_datetime(df['datetime'], utc=True, unit='ms')
    pd_ts = pd_ts.dt.tz_convert("Asia/Seoul")
    pd_ts = pd_ts.dt.tz_localize(None)
    df.set_index(pd_ts, inplace=True)
    return df[['open', 'high', 'low', 'close', 'volume']]

################################################################################################################
# News and Search Tools
################################################################################################################

@tool
def search_crypto_news_tool(query: str):
    """
    Search for the latest cryptocurrency news and information using Tavily search.
    
    Args:
        query: Search query (e.g., 'BTC/USDT news', 'Bitcoin price analysis')
    
    Returns:
        JSON string with search results including title, url, content, and score
    """
    try:
        results = _tavily_search.invoke({"query": query})
        
        formatted_results = {
            "query": query,
            "results": []
        }
        
        if isinstance(results, list):
            for item in results:
                formatted_results["results"].append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:500],
                    "score": item.get("score", 0)
                })
        
        return json.dumps(formatted_results, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

################################################################################################################
# Market Data Tools
################################################################################################################

@tool
def fetch_crypto_candle_chart_tool(symbol: str, timeframe: str, limit: int = 100):
    """
    Fetch crypto candle chart (OHLCV) from Binance exchange.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe for candles (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        limit: Number of candles to fetch (default: 100, max: 1000)
    
    Returns:
        DataFrame with columns: open, high, low, close, volume (indexed by datetime)
    """
    df = _fetch_ohlcv_dataframe(symbol, timeframe, limit)
    data_dict = {str(k): v for k, v in df.to_dict('index').items()}
    return json.dumps(data_dict, ensure_ascii=False, indent=2)

@tool
def get_current_price_tool(symbol: str):
    """
    Get the current price of a trading pair.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
    
    Returns:
        Current price as float
    """
    ticker = binance_exchange.fetch_ticker(symbol)
    result = {
        'symbol': symbol,
        'last_price': ticker['last'],
        'bid': ticker['bid'],
        'ask': ticker['ask'],
        'volume_24h': ticker['quoteVolume']
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

################################################################################################################
# Technical Indicator Tools
################################################################################################################

@tool
def calculate_rsi_tool(symbol: str, timeframe: str = '1h', period: int = 14, limit: int = 100):
    """
    Calculate Relative Strength Index (RSI) technical indicator.
    RSI above 70 suggests overbought, below 30 suggests oversold.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe for candles (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        period: RSI period (default: 14)
        limit: Number of candles to fetch (default: 100)
    
    Returns:
        Dictionary with RSI values
    """
    df = _fetch_ohlcv_dataframe(symbol, timeframe, limit)
    
    if len(df) < period + 1:
        return json.dumps({"error": f"Not enough data. Need at least {period + 1} candles, got {len(df)}"}, ensure_ascii=False, indent=2)
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'current_rsi': float(rsi.iloc[-1]),
        'latest_values': {str(k): float(v) for k, v in rsi.tail(5).to_dict().items()}
    }
    if rsi.iloc[-1] > 70:
        result['signal'] = 'overbought'
    elif rsi.iloc[-1] < 30:
        result['signal'] = 'oversold'
    else:
        result['signal'] = 'neutral'
    
    return json.dumps(result, ensure_ascii=False, indent=2)

@tool
def calculate_moving_averages_tool(symbol: str, timeframe: str = '1h', short_period: int = 20, long_period: int = 50, limit: int = 100):
    """
    Calculate Simple Moving Averages (SMA) for short and long periods.
    Golden cross (short MA crosses above long MA) suggests bullish signal.
    Death cross (short MA crosses below long MA) suggests bearish signal.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe for candles (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        short_period: Short MA period (default: 20)
        long_period: Long MA period (default: 50)
        limit: Number of candles to fetch (default: 100)
    
    Returns:
        Dictionary with MA values and signals
    """
    df = _fetch_ohlcv_dataframe(symbol, timeframe, limit)
    
    if len(df) < long_period:
        return json.dumps({"error": f"Not enough data. Need at least {long_period} candles, got {len(df)}"}, ensure_ascii=False, indent=2)
    
    df['sma_short'] = df['close'].rolling(window=short_period).mean()
    df['sma_long'] = df['close'].rolling(window=long_period).mean()
    
    current_price = df['close'].iloc[-1]
    sma_short_current = df['sma_short'].iloc[-1]
    sma_long_current = df['sma_long'].iloc[-1]
    
    # Determine signal
    if sma_short_current > sma_long_current and df['sma_short'].iloc[-2] <= df['sma_long'].iloc[-2]:
        signal = 'golden_cross_bullish'
    elif sma_short_current < sma_long_current and df['sma_short'].iloc[-2] >= df['sma_long'].iloc[-2]:
        signal = 'death_cross_bearish'
    elif sma_short_current > sma_long_current:
        signal = 'bullish'
    else:
        signal = 'bearish'
    
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'current_price': float(current_price),
        'sma_short': float(sma_short_current),
        'sma_long': float(sma_long_current),
        'signal': signal,
        'price_vs_short_ma': 'above' if current_price > sma_short_current else 'below',
        'price_vs_long_ma': 'above' if current_price > sma_long_current else 'below'
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

@tool
def calculate_macd_tool(symbol: str, timeframe: str = '1h', fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, limit: int = 100):
    """
    Calculate MACD (Moving Average Convergence Divergence) indicator.
    MACD line above signal line suggests bullish momentum.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        timeframe: Timeframe for candles (e.g., '1m', '5m', '15m', '1h', '4h', '1d')
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line period (default: 9)
        limit: Number of candles to fetch (default: 100)
    
    Returns:
        Dictionary with MACD values and signals
    """
    df = _fetch_ohlcv_dataframe(symbol, timeframe, limit)
    
    if len(df) < slow_period + signal_period:
        return json.dumps({"error": f"Not enough data. Need at least {slow_period + signal_period} candles"}, ensure_ascii=False, indent=2)
    
    ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_histogram = histogram.iloc[-1]
    
    # Determine signal
    if current_macd > current_signal and macd_line.iloc[-2] <= signal_line.iloc[-2]:
        signal = 'bullish_crossover'
    elif current_macd < current_signal and macd_line.iloc[-2] >= signal_line.iloc[-2]:
        signal = 'bearish_crossover'
    elif current_macd > current_signal:
        signal = 'bullish'
    else:
        signal = 'bearish'
    
    result = {
        'symbol': symbol,
        'timeframe': timeframe,
        'macd': float(current_macd),
        'signal': float(current_signal),
        'histogram': float(current_histogram),
        'macd_signal': signal
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

################################################################################################################
# Account and Position Tools
################################################################################################################

@tool
def get_balance_tool():
    """
    Get current account balance (USDT for futures trading).
    
    Returns:
        Dictionary with balance information
    """
    balance = binance_exchange.fetch_balance()
    usdt_balance = balance.get('USDT', {})
    result = {
        'total_balance': float(usdt_balance.get('total', 0)),
        'free_balance': float(usdt_balance.get('free', 0)),
        'used_balance': float(usdt_balance.get('used', 0)),
        'currency': 'USDT'
    }
    return json.dumps(result, ensure_ascii=False, indent=2)

@tool
def get_positions_tool(symbol: Optional[str] = None):
    """
    Get current open positions.
    
    Args:
        symbol: Optional symbol to filter (e.g., 'BTC/USDT'). If None, returns all positions.
    
    Returns:
        List of open positions with details
    """
    positions = binance_exchange.fetch_positions(symbols=[symbol] if symbol else None)
    open_positions = [pos for pos in positions if float(pos['contracts']) != 0]
    
    position_list = []
    for pos in open_positions:
        position_list.append({
            'symbol': pos['symbol'],
            'side': pos['side'],
            'size': float(pos['contracts']),
            'entry_price': float(pos['entryPrice']),
            'mark_price': float(pos['markPrice']),
            'unrealized_pnl': float(pos['unrealizedPnl']),
            'percentage': float(pos['percentage'])
        })
    
    result = {'positions': position_list, 'count': len(position_list)}
    return json.dumps(result, ensure_ascii=False, indent=2)

################################################################################################################
# Trading Execution Tools
################################################################################################################

@tool
def place_buy_order_tool(symbol: str, amount: float, order_type: str = 'market'):
    """
    Place a buy (long) order. Use this when analysis suggests bullish trend.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        amount: Order size in USDT
        order_type: 'market' for market order, 'limit' for limit order (default: 'market')
    
    Returns:
        Order details
    """
    try:
        if order_type == 'market':
            order = binance_exchange.create_market_buy_order(symbol, amount)
        else:
            return json.dumps({"error": "Limit orders not implemented yet. Use 'market' order_type."}, ensure_ascii=False, indent=2)
        
        result = {
            'status': 'success',
            'order_id': order['id'],
            'symbol': order['symbol'],
            'side': 'buy',
            'amount': order['amount'],
            'price': order.get('price', 'market'),
            'order_status': order['status']
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

@tool
def place_sell_order_tool(symbol: str, amount: float, order_type: str = 'market'):
    """
    Place a sell (short) order. Use this when analysis suggests bearish trend.
    Or use to close a long position.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
        amount: Order size in USDT
        order_type: 'market' for market order, 'limit' for limit order (default: 'market')
    
    Returns:
        Order details
    """
    try:
        if order_type == 'market':
            order = binance_exchange.create_market_sell_order(symbol, amount)
        else:
            return json.dumps({"error": "Limit orders not implemented yet. Use 'market' order_type."}, ensure_ascii=False, indent=2)
        
        result = {
            'status': 'success',
            'order_id': order['id'],
            'symbol': order['symbol'],
            'side': 'sell',
            'amount': order['amount'],
            'price': order.get('price', 'market'),
            'order_status': order['status']
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

@tool
def close_position_tool(symbol: str):
    """
    Close an existing position completely.
    
    Args:
        symbol: Trading pair symbol (e.g., 'BTC/USDT')
    
    Returns:
        Close position result
    """
    try:
        positions = binance_exchange.fetch_positions(symbols=[symbol])
        position = next((p for p in positions if float(p['contracts']) != 0), None)
        
        if not position:
            return json.dumps({"error": f"No open position found for {symbol}"}, ensure_ascii=False, indent=2)
        
        side = 'sell' if position['side'] == 'long' else 'buy'
        size = abs(float(position['contracts']))
        
        order = binance_exchange.create_market_order(symbol, side, size)
        
        result = {
            'status': 'success',
            'symbol': symbol,
            'closed_position': position['side'],
            'size': size,
            'order_id': order['id']
        }
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)

################################################################################################################
# Tool Collections
################################################################################################################

# Analysis tools only (safe for testing)
ANALYSIS_TOOLS = [
    search_crypto_news_tool,
    fetch_crypto_candle_chart_tool,
    get_current_price_tool,
    calculate_rsi_tool,
    calculate_moving_averages_tool,
    calculate_macd_tool,
]

# Account tools (read-only)
ACCOUNT_TOOLS = [
    get_balance_tool,
    get_positions_tool,
]

# Trading tools (use with caution!)
TRADING_TOOLS = [
    place_buy_order_tool,
    place_sell_order_tool,
    close_position_tool,
]

# All tools combined
ALL_TOOLS = ANALYSIS_TOOLS + ACCOUNT_TOOLS + TRADING_TOOLS

