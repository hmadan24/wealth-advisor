"""
Dexter Integration Module
Connects autonomous financial research agent to wealth advisor platform.
"""
import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import logging

logger = logging.getLogger(__name__)


class DexterAgent:
    """
    Autonomous financial research agent for deep portfolio analysis.
    Based on virattt/dexter architecture with custom tools for Indian mutual funds.
    """
    
    def __init__(self, openai_api_key: str, financial_datasets_api_key: Optional[str] = None):
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            openai_api_key=openai_api_key
        )
        self.financial_api_key = financial_datasets_api_key
        self.tools = self._initialize_tools()
        self.agent = self._create_agent()
    
    def _initialize_tools(self) -> List[Tool]:
        """Initialize financial research tools."""
        tools = [
            Tool(
                name="get_fund_nav",
                func=self._get_fund_nav,
                description="Get the current NAV (Net Asset Value) and historical performance of a mutual fund by ISIN or scheme code"
            ),
            Tool(
                name="get_fund_holdings",
                func=self._get_fund_holdings,
                description="Get the top holdings and sector allocation of a mutual fund"
            ),
            Tool(
                name="compare_funds",
                func=self._compare_funds,
                description="Compare multiple mutual funds on parameters like returns, expense ratio, AUM, etc."
            ),
            Tool(
                name="get_benchmark_returns",
                func=self._get_benchmark_returns,
                description="Get historical returns of benchmark indices like Nifty 50, Sensex, Nifty 100"
            ),
            Tool(
                name="analyze_portfolio_overlap",
                func=self._analyze_portfolio_overlap,
                description="Analyze overlapping holdings between multiple funds in the portfolio"
            ),
            Tool(
                name="get_fund_expense_ratio",
                func=self._get_fund_expense_ratio,
                description="Get expense ratio and other cost metrics for a mutual fund"
            ),
        ]
        
        # Add US equity tools if API key provided
        if self.financial_api_key:
            tools.extend([
                Tool(
                    name="get_income_statement",
                    func=self._get_income_statement,
                    description="Get income statement data for a US company (revenue, expenses, net income)"
                ),
                Tool(
                    name="get_balance_sheet",
                    func=self._get_balance_sheet,
                    description="Get balance sheet data for a US company (assets, liabilities, equity)"
                ),
                Tool(
                    name="get_cash_flow",
                    func=self._get_cash_flow,
                    description="Get cash flow statement for a US company"
                ),
            ])
        
        return tools
    
    def _create_agent(self) -> AgentExecutor:
        """Create the Dexter agent with planning and validation capabilities."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are Dexter, an autonomous financial research agent.

Your role is to:
1. Break down complex financial questions into research tasks
2. Use available tools to gather real-time financial data
3. Analyze the data critically
4. Provide data-backed insights and recommendations

When analyzing portfolios:
- Focus on actionable insights (not just stating facts)
- Compare against relevant benchmarks
- Identify concentration risks and overlaps
- Consider expense ratios and fund quality
- Provide specific recommendations with reasoning

Think step-by-step and validate your findings before concluding."""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
    
    async def research(self, query: str, portfolio_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run autonomous research on a financial query.
        
        Args:
            query: The research question (e.g., "Why is my Axis Bluechip Fund underperforming?")
            portfolio_context: Optional context about user's portfolio
        
        Returns:
            Research results with analysis and recommendations
        """
        try:
            # Add portfolio context to query if provided
            if portfolio_context:
                context_str = self._format_portfolio_context(portfolio_context)
                full_query = f"{query}\n\nPortfolio Context:\n{context_str}"
            else:
                full_query = query
            
            # Run agent
            result = await asyncio.to_thread(
                self.agent.invoke,
                {"input": full_query}
            )
            
            return {
                "success": True,
                "query": query,
                "analysis": result.get("output", ""),
                "steps": result.get("intermediate_steps", []),
            }
        
        except Exception as e:
            logger.error(f"Dexter research error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_portfolio_context(self, portfolio: Dict) -> str:
        """Format portfolio data for context."""
        summary = portfolio.get("summary", {})
        holdings = portfolio.get("holdings", [])[:10]  # Top 10 holdings
        
        context = f"""
Total Portfolio Value: ₹{summary.get('total_value', 0):,.0f}
Total Return: {summary.get('return_percentage', 0):.1f}%
Number of Schemes: {summary.get('scheme_count', 0)}

Top Holdings:
"""
        for i, h in enumerate(holdings, 1):
            context += f"{i}. {h.get('scheme_name', 'N/A')[:50]} - ₹{h.get('current_value', 0):,.0f} ({h.get('percentage_return', 0):.1f}%)\n"
        
        return context
    
    # Tool implementations (mock for now - replace with actual APIs)
    
    def _get_fund_nav(self, fund_identifier: str) -> str:
        """Get NAV data for a fund."""
        # TODO: Integrate with MFAPI or similar
        return f"Mock NAV data for {fund_identifier}: Current NAV ₹150, 1Y return: 15.2%"
    
    def _get_fund_holdings(self, fund_identifier: str) -> str:
        """Get fund holdings."""
        return f"Mock holdings for {fund_identifier}: Top holdings - Reliance 8%, TCS 6%, HDFC Bank 5.5%"
    
    def _compare_funds(self, fund_list: str) -> str:
        """Compare multiple funds."""
        return f"Comparing funds: {fund_list}"
    
    def _get_benchmark_returns(self, benchmark: str) -> str:
        """Get benchmark returns."""
        return f"Mock benchmark data for {benchmark}: 1Y: 18.5%, 3Y: 14.2% CAGR"
    
    def _analyze_portfolio_overlap(self, fund_list: str) -> str:
        """Analyze fund overlap."""
        return f"Analyzing overlap for: {fund_list}"
    
    def _get_fund_expense_ratio(self, fund_identifier: str) -> str:
        """Get expense ratio."""
        return f"Expense ratio for {fund_identifier}: 1.8% (higher than category average of 1.5%)"
    
    def _get_income_statement(self, ticker: str) -> str:
        """Get income statement for US company."""
        # TODO: Integrate with Financial Datasets API
        return f"Mock income statement for {ticker}"
    
    def _get_balance_sheet(self, ticker: str) -> str:
        """Get balance sheet."""
        return f"Mock balance sheet for {ticker}"
    
    def _get_cash_flow(self, ticker: str) -> str:
        """Get cash flow statement."""
        return f"Mock cash flow for {ticker}"


# Singleton instance
_dexter_agent: Optional[DexterAgent] = None

def get_dexter_agent(openai_api_key: str, financial_api_key: Optional[str] = None) -> DexterAgent:
    """Get or create Dexter agent instance."""
    global _dexter_agent
    if _dexter_agent is None:
        _dexter_agent = DexterAgent(openai_api_key, financial_api_key)
    return _dexter_agent
