# 🤖 Algorithm Trading with Agent Tutorial

AI 에이전트를 활용한 암호화폐 알고리즘 트레이딩 튜토리얼입니다. LangChain과 Binance Futures API를 사용하여 자동으로 시장을 분석하고 거래 추천을 제공합니다.

## 📋 목차

- [특징](#-특징)
- [프로젝트 구조](#-프로젝트-구조)
- [설치 및 환경 설정](#-설치-및-환경-설정)
- [사용 방법](#-사용-방법)
- [도구 설명](#-도구-설명)
- [예제 코드](#-예제-코드)

## ✨ 특징

- 🔍 **시장 데이터 분석**: 실시간 가격, 캔들 차트, 거래량 데이터 조회
- 📊 **기술적 지표**: RSI, MACD, 이동평균선(MA) 자동 계산
- 📰 **뉴스 검색**: Tavily API를 통한 최신 암호화폐 뉴스 검색
- 🤖 **AI 기반 분석**: GPT-4를 활용한 종합적인 시장 분석 및 거래 추천
- 🔒 **안전한 테스트**: 분석 전용 모드로 실제 거래 없이 테스트 가능

## 📁 프로젝트 구조

```
algorithm-trading-with-agent-tutorial/
├── main.py              # 메인 실행 파일 (Agent 설정 및 실행)
├── tools.py             # 트레이딩 도구 모음 (API 호출, 지표 계산 등)
├── requirements.txt     # Python 패키지 의존성
├── .env.sample         # 환경 변수 템플릿
└── README.md           # 프로젝트 문서
```

### 파일 설명

#### `tools.py`
모든 트레이딩 도구들을 포함하는 모듈입니다:

- **뉴스 검색 도구**: `search_crypto_news_tool`
- **시장 데이터 도구**: `fetch_crypto_candle_chart_tool`, `get_current_price_tool`
- **기술적 지표 도구**: `calculate_rsi_tool`, `calculate_moving_averages_tool`, `calculate_macd_tool`
- **계좌 관리 도구**: `get_balance_tool`, `get_positions_tool`
- **거래 실행 도구**: `place_buy_order_tool`, `place_sell_order_tool`, `close_position_tool`

도구는 용도에 따라 3가지 그룹으로 분류됩니다:
```python
ANALYSIS_TOOLS  # 분석 전용 (안전)
ACCOUNT_TOOLS   # 계좌 조회 (읽기 전용)
TRADING_TOOLS   # 거래 실행 (주의 필요)
```
기본적으로는 분석 전용 툴만 쓸 수 있도록 선택되어 있습니다. 실매매까지 연결시키기 위해선 `TRADING_TOOLS`를 활성화 하세요. 

#### `main.py`
Agent 설정 및 실행 로직을 포함합니다:

- **`create_trading_agent()`**: 설정 가능한 trading agent 생성
- **`analyze_ticker()`**: 특정 코인 분석 수행
- **`parse_agent_output()`**: Agent 출력 파싱
- **`print_agent_result()`**: 결과 출력

## 🛠 설치 및 환경 설정

### 1. 저장소 클론

```bash
git clone https://github.com/yourusername/algorithm-trading-with-agent-tutorial.git
cd algorithm-trading-with-agent-tutorial
```

### 2. Python 패키지 설치

```bash
pip install -r requirements.txt
```

주요 패키지:
- `langchain` - AI Agent 프레임워크
- `langchain-openai` - OpenAI 통합
- `langchain-community` - Tavily 검색 도구
- `ccxt` - 암호화폐 거래소 API
- `pandas` - 데이터 분석
- `python-dotenv` - 환경 변수 관리

### 3. 환경 변수 설정

`.env` 파일을 생성하고 필요한 API 키를 설정합니다:

```bash
# OpenAI API 키 (필수)
OPENAI_API_KEY=your_openai_api_key_here

# Tavily API 키 (뉴스 검색용, 필수)
TAVILY_API_KEY=your_tavily_api_key_here

# Binance API 키 (실제 거래시에만 필요)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here
```

#### API 키 발급 방법

1. **OpenAI API**: https://platform.openai.com/api-keys
2. **Tavily API**: https://tavily.com/
3. **Binance API** (선택사항): https://www.binance.com/en/my/settings/api-management

⚠️ **주의**: Binance API 키는 실제 거래를 할 때만 필요합니다. 분석만 테스트하는 경우 불필요합니다.

## 🚀 사용 방법

### 기본 실행

```bash
python main.py
```

기본적으로 BTC/USDT를 1시간 타임프레임으로 분석합니다.

### 출력 예시

```json
{
  "symbol": "BTC/USDT",
  "exchange": "Binance",
  "timeframe": "1h",
  "timestamp": "2025-11-06T10:30:00Z",
  "current_price": 95234.50,
  "analysis": {
    "news": {
      "sentiment": "positive",
      "summary": "비트코인이 최근 긍정적인 시장 반응을 보이고 있습니다..."
    },
    "rsi": {
      "value": 65.5,
      "signal": "neutral"
    },
    "macd": {
      "value": 123.45,
      "signal": "bullish"
    },
    "moving_averages": {
      "short_ma": 94500.0,
      "long_ma": 93000.0,
      "signal": "bullish"
    }
  },
  "recommendation": {
    "action": "buy",
    "confidence": "medium",
    "position_type": "entry",
    "reason": "RSI가 중립적이고 MACD가 상승세를 보이며..."
  },
  "risk_assessment": {
    "risk_level": "medium",
    "stop_loss": 93000.0,
    "take_profit": 97000.0
  }
}
```

## 🔧 도구 설명

### 시장 데이터 도구

#### `fetch_crypto_candle_chart_tool`
캔들 차트 데이터(OHLCV)를 가져옵니다.

```python
fetch_crypto_candle_chart_tool(
    symbol="BTC/USDT",
    timeframe="1h",  # 1m, 5m, 15m, 1h, 4h, 1d 등
    limit=100        # 가져올 캔들 수
)
```

#### `get_current_price_tool`
현재 가격 정보를 조회합니다.

```python
get_current_price_tool(symbol="BTC/USDT")
```

### 기술적 지표 도구

#### `calculate_rsi_tool`
RSI (Relative Strength Index)를 계산합니다.
- RSI > 70: 과매수 (매도 고려)
- RSI < 30: 과매도 (매수 고려)

```python
calculate_rsi_tool(
    symbol="BTC/USDT",
    timeframe="1h",
    period=14
)
```

#### `calculate_moving_averages_tool`
단순 이동평균선(SMA)을 계산합니다.
- Golden Cross: 단기 MA가 장기 MA를 상향 돌파 (매수 신호)
- Death Cross: 단기 MA가 장기 MA를 하향 돌파 (매도 신호)

```python
calculate_moving_averages_tool(
    symbol="BTC/USDT",
    timeframe="1h",
    short_period=20,
    long_period=50
)
```

#### `calculate_macd_tool`
MACD (Moving Average Convergence Divergence)를 계산합니다.

```python
calculate_macd_tool(
    symbol="BTC/USDT",
    timeframe="1h",
    fast_period=12,
    slow_period=26,
    signal_period=9
)
```

### 뉴스 검색 도구

#### `search_crypto_news_tool`
최신 암호화폐 뉴스를 검색합니다.

```python
search_crypto_news_tool(query="BTC/USDT news")
```

## 📝 예제 코드

### 예제 1: 기본 분석

```python
from main import create_trading_agent, analyze_ticker, print_agent_result
from tools import ANALYSIS_TOOLS

# Agent 생성 (분석 도구만 사용)
agent = create_trading_agent(tools_to_use=ANALYSIS_TOOLS)

# BTC 분석
result = analyze_ticker("BTC", timeframe="1h", agent_executor=agent)

# 결과 출력
print_agent_result(result)
```

### 예제 2: 여러 코인 비교 분석

```python
from main import create_trading_agent, analyze_ticker
from tools import ANALYSIS_TOOLS

agent = create_trading_agent(tools_to_use=ANALYSIS_TOOLS)

tickers = ["BTC", "ETH", "SOL"]

for ticker in tickers:
    print(f"\n{'='*80}")
    print(f"Analyzing {ticker}/USDT")
    print('='*80)
    
    result = analyze_ticker(ticker, timeframe="1h", agent_executor=agent)
    print(result["output"])
```

### 예제 3: 커스텀 쿼리

```python
from main import create_trading_agent
from tools import ANALYSIS_TOOLS

agent = create_trading_agent(tools_to_use=ANALYSIS_TOOLS)

# 커스텀 분석 요청
result = agent.invoke({
    "input": """
    ETH/USDT의 4시간 차트를 분석해주세요.
    RSI와 MACD를 계산하고, 최근 이더리움 관련 뉴스도 검색해주세요.
    종합적인 매매 추천을 해주세요.
    """
})

print(result["output"])
```

### 예제 4: 계좌 조회 포함 (Binance API 필요)

```python
from main import create_trading_agent
from tools import ANALYSIS_TOOLS, ACCOUNT_TOOLS

# 분석 + 계좌 조회 도구 사용
agent = create_trading_agent(tools_to_use=ANALYSIS_TOOLS + ACCOUNT_TOOLS)

result = agent.invoke({
    "input": """
    현재 내 계좌 잔고를 확인하고,
    BTC/USDT를 분석해서 매수 추천을 해주세요.
    """
})

print(result["output"])
```

### 예제 5: 다양한 타임프레임 분석

```python
from main import create_trading_agent
from tools import ANALYSIS_TOOLS

agent = create_trading_agent(tools_to_use=ANALYSIS_TOOLS)

timeframes = ["15m", "1h", "4h", "1d"]

for tf in timeframes:
    result = agent.invoke({
        "input": f"""
        BTC/USDT를 {tf} 타임프레임으로 분석하고,
        RSI와 MACD를 계산해주세요.
        """
    })
    print(f"\n=== {tf} Timeframe ===")
    print(result["output"])
```

## ⚠️ 주의사항

1. **실제 거래 주의**: `TRADING_TOOLS`는 실제 거래를 실행합니다. 테스트시에는 `ANALYSIS_TOOLS`만 사용하세요.
2. **API 키 보안**: `.env` 파일을 절대 공개 저장소에 커밋하지 마세요.
3. **Rate Limiting**: Binance API는 요청 제한이 있습니다. `enableRateLimit: True` 설정을 유지하세요.
4. **비용**: OpenAI API 사용에 따른 비용이 발생합니다.

## 🔐 보안 권장사항

- `.env` 파일을 `.gitignore`에 추가하세요
- Binance API 키는 IP 제한을 설정하세요
- Testnet을 먼저 사용해 테스트하세요
- 소액으로 시작하세요

## TO-DO
- [ ] CCXT를 이용해서 실매매 연결
- [ ] LangGraph를 이용해서 Multi-Agent로 확장