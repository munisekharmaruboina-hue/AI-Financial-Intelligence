REPORT_PROMPT = """You are generating a final investment analysis report.

Ticker: {ticker}

Market Data:
{market}

Technical Analysis:
{technical}

Research Findings:
{research}

Advisor Recommendation:
{advisor}

Write a well-structured report with these sections:
1. **Overview** - current price, market cap, general position
2. **Technical Analysis** - trend direction and what the indicators suggest
3. **Research & Sentiment** - summary of recent news and market sentiment
4. **Recommendation** - the advisor's call and reasoning
5. **Disclaimer** - one line noting this is not financial advice

Keep the total report under 300 words. Use clear headers and be concise.
"""