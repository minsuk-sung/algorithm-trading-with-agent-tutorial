"""
Cryptocurrency Trading Agent with LangChain and Binance Futures API
"""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json

# Import tools from tools module
from tools import ANALYSIS_TOOLS, ACCOUNT_TOOLS, TRADING_TOOLS

################################################################################################################
# System Prompt Template
################################################################################################################
SYSTEM_PROMPT = """You are an expert cryptocurrency trading agent for Binance Futures.

Your responsibilities:
1. Analyze market data using technical indicators (RSI, MACD, Moving Averages)
2. Make informed trading decisions based on technical analysis
3. Manage risk by checking balance and existing positions before trading
4. Execute trades only when analysis strongly supports the decision

Trading Strategy Guidelines:
- Use RSI: Overbought (>70) suggests sell, Oversold (<30) suggests buy
- Use Moving Averages: Golden cross (short MA > long MA) suggests buy, Death cross suggests sell
- Use MACD: Bullish crossover suggests buy, Bearish crossover suggests sell
- Always check current balance before placing orders
- Check existing positions before opening new ones
- Consider closing positions that show losses or if trend reverses

Workflow for analyzing a ticker:
1. Fetch candle chart data for the ticker
2. Get current price
3. Calculate technical indicators (RSI, MACD, Moving Averages)
4. Analyze all indicators together to make decision
5. Check balance and existing positions
6. Execute trade if conditions are favorable, otherwise explain why not trading

IMPORTANT: You MUST respond with a valid JSON object in the following format:
{{
  "symbol": "BTC/USDT",
  "exchange": "Binance",
  "timeframe": "1h",
  "timestamp": "2025-01-01T00:00:00Z",
  "current_price": 50000.0,
  "analysis": {{
    "news": {{
        "sentiment": "positive|negative|neutral",
        "summary": "Summary of the news in Korean",
    }},
    "rsi": {{
      "value": 65.5,
      "signal": "neutral"
    }},
    "macd": {{
      "value": 123.45,
      "signal": "bullish"
    }},
    "moving_averages": {{
      "short_ma": 49500.0,
      "long_ma": 48000.0,
      "signal": "bullish"
    }}
  }},
  "recommendation": {{
    "action": "buy|sell|hold",
    "confidence": "high|medium|low",
    "position_type": "entry|exit|hold",
    "reason": "Detailed reasoning here"
  }},
  "risk_assessment": {{
    "risk_level": "high|medium|low",
    "stop_loss": 48000.0,
    "take_profit": 52000.0
  }}
}}

Always provide clear reasoning for your trading decisions in the "reason" field.
Answer in Korean.
"""

################################################################################################################
# Agent Configuration
################################################################################################################

def create_trading_agent(tools_to_use=None, model="gpt-4o-mini", temperature=0, 
                        max_iterations=10, max_execution_time=10):
    """
    Create a configured trading agent.
    
    Args:
        tools_to_use: List of tools to use (default: ANALYSIS_TOOLS only)
        model: OpenAI model name
        temperature: Model temperature (0 = deterministic)
        max_iterations: Maximum number of agent iterations
        max_execution_time: Maximum execution time in seconds
    
    Returns:
        AgentExecutor instance
    """
    # Default to analysis tools only (safe for testing)
    if tools_to_use is None:
        tools_to_use = ANALYSIS_TOOLS
    
    # Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])
    
    # Initialize LLM
    llm = ChatOpenAI(model=model, temperature=temperature)
    
    # Create agent
    agent = create_tool_calling_agent(llm, tools_to_use, prompt)
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools_to_use,
        verbose=True,
        max_iterations=max_iterations,
        max_execution_time=max_execution_time,
        handle_parsing_errors=True,
    )
    
    return agent_executor

################################################################################################################
# Helper Functions
################################################################################################################

def parse_agent_output(output_text: str) -> dict:
    """
    Parse agent output to extract JSON response.
    
    Args:
        output_text: Raw text output from agent
    
    Returns:
        Parsed JSON dictionary or fallback structure
    """
    try:
        # Try to extract JSON from markdown code blocks
        if "```json" in output_text:
            json_start = output_text.find("```json") + 7
            json_end = output_text.find("```", json_start)
            json_str = output_text[json_start:json_end].strip()
        elif "```" in output_text:
            json_start = output_text.find("```") + 3
            json_end = output_text.find("```", json_start)
            json_str = output_text[json_start:json_end].strip()
        elif output_text.strip().startswith("{"):
            json_str = output_text.strip()
        else:
            json_str = output_text
        
        return json.loads(json_str)
        
    except json.JSONDecodeError:
        # Return fallback structure on parsing failure
        return {
            "status": "parsing_failed",
            "raw_output": output_text,
            "note": "Agent did not return structured JSON"
        }


def print_agent_result(result: dict, show_intermediate_steps: bool = True):
    """
    Pretty print agent execution results.
    
    Args:
        result: Agent execution result dictionary
        show_intermediate_steps: Whether to display intermediate steps
    """
    print("\n" + "=" * 80)
    print("Agent 실행 결과 (Structured JSON)")
    print("=" * 80)
    
    output_text = result["output"]
    parsed_output = parse_agent_output(output_text)
    print(json.dumps(parsed_output, ensure_ascii=False, indent=2))
    
    if show_intermediate_steps and "intermediate_steps" in result:
        print("\n" + "=" * 80)
        print("중간 단계 (Intermediate Steps)")
        print("=" * 80)
        for i, step in enumerate(result["intermediate_steps"], 1):
            action, observation = step
            print(f"\n--- Step {i} ---")
            print(f"Tool: {action.tool}")
            print(f"Input: {json.dumps(action.tool_input, ensure_ascii=False, indent=2)}")
            print(f"Output: {observation[:500]}...")  # First 500 chars only


def analyze_ticker(ticker: str, timeframe: str = "1h", agent_executor=None):
    """
    Analyze a cryptocurrency ticker and make trading recommendation.
    
    Args:
        ticker: Ticker symbol (e.g., 'BTC', 'ETH')
        timeframe: Timeframe for analysis (default: '1h')
        agent_executor: AgentExecutor instance (creates new one if None)
    
    Returns:
        Agent execution result dictionary
    """
    if agent_executor is None:
        agent_executor = create_trading_agent()
    
    query = f"""
    Analyze {ticker}/USDT using {timeframe} timeframe.
    Calculate RSI, MACD, and Moving Averages.
    Find the latest news about {ticker}/USDT.
    Make a trading recommendation based on the analysis.
    Respond with a structured JSON format as specified in the system prompt.
    """
    
    result = agent_executor.invoke({"input": query})
    return result

################################################################################################################
# Main Execution
################################################################################################################

def main():
    """
    Main function to run the trading agent.
    
    Example commands:
    - Analyze BTC/USDT and make a trading decision
    - Check my current positions and balance  
    - Get current price of ETH/USDT
    """
    print("=" * 80)
    print("Crypto Trading Agent - Ready")
    print("=" * 80)
    print("\n📊 Analyzing BTC/USDT...")
    
    # Create agent with analysis tools only (safe for testing)
    agent_executor = create_trading_agent(tools_to_use=ANALYSIS_TOOLS)
    
    # Analyze BTC
    ticker = "BTC"
    result = analyze_ticker(ticker=ticker, timeframe="1h", agent_executor=agent_executor)
    
    # Print results
    print_agent_result(result, show_intermediate_steps=True)


if __name__ == "__main__":
    main()