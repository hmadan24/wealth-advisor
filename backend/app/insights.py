"""
Portfolio Insights Engine

Generates actionable insights and recommendations from portfolio data.
"""
from typing import Dict, Any, List


def generate_insights(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate insights and actionable recommendations from portfolio data.
    """
    insights = {
        "summary_insights": [],
        "actionables": [],
        "risks": [],
        "opportunities": [],
    }
    
    holdings = portfolio.get("holdings", [])
    asset_allocation = portfolio.get("asset_allocation", [])
    amc_allocation = portfolio.get("amc_allocation", [])
    summary = portfolio.get("summary", {})
    
    # 1. Portfolio Concentration Analysis
    concentration_insights = analyze_concentration(holdings, summary)
    insights["risks"].extend(concentration_insights.get("risks", []))
    insights["actionables"].extend(concentration_insights.get("actionables", []))
    
    # 2. Asset Allocation Analysis
    allocation_insights = analyze_asset_allocation(asset_allocation)
    insights["summary_insights"].extend(allocation_insights.get("summary", []))
    insights["actionables"].extend(allocation_insights.get("actionables", []))
    
    # 3. AMC Diversification
    amc_insights = analyze_amc_diversification(amc_allocation)
    insights["risks"].extend(amc_insights.get("risks", []))
    
    # 4. Performance Analysis
    performance_insights = analyze_performance(holdings)
    insights["summary_insights"].extend(performance_insights.get("summary", []))
    insights["opportunities"].extend(performance_insights.get("opportunities", []))
    
    # 5. Fund Overlap Detection
    overlap_insights = detect_fund_overlap(holdings)
    insights["risks"].extend(overlap_insights.get("risks", []))
    insights["actionables"].extend(overlap_insights.get("actionables", []))
    
    # 6. Portfolio Health Score
    insights["health_score"] = calculate_health_score(insights, portfolio)
    
    return insights


def analyze_concentration(holdings: List[Dict], summary: Dict) -> Dict[str, List]:
    """Analyze portfolio concentration risks."""
    risks = []
    actionables = []
    
    total_value = summary.get("total_value", 0)
    if total_value == 0:
        return {"risks": risks, "actionables": actionables}
    
    # Check top holding concentration
    if holdings:
        top_holding = holdings[0]
        top_concentration = (top_holding["current_value"] / total_value) * 100
        
        if top_concentration > 40:
            risks.append({
                "type": "high_concentration",
                "severity": "high",
                "title": "High Single Fund Concentration",
                "description": f"Your largest holding '{top_holding['scheme_name'][:40]}...' represents {top_concentration:.1f}% of your portfolio.",
                "recommendation": "Consider rebalancing to reduce concentration below 25% in any single fund."
            })
        elif top_concentration > 25:
            risks.append({
                "type": "moderate_concentration",
                "severity": "medium",
                "title": "Moderate Concentration Risk",
                "description": f"Your top fund represents {top_concentration:.1f}% of portfolio.",
                "recommendation": "Monitor this position and consider gradual diversification."
            })
    
    # Check if portfolio is too fragmented
    scheme_count = summary.get("scheme_count", 0)
    if scheme_count > 15:
        risks.append({
            "type": "over_diversification",
            "severity": "medium",
            "title": "Portfolio Over-Diversification",
            "description": f"You have {scheme_count} schemes which may be difficult to track and manage.",
            "recommendation": "Consider consolidating into 8-12 well-chosen funds for better manageability."
        })
        actionables.append({
            "priority": "medium",
            "action": "Consolidate Portfolio",
            "description": f"Review and merge similar funds. Target: reduce from {scheme_count} to ~10 schemes.",
            "impact": "Easier tracking, lower overlap, potentially lower costs"
        })
    
    return {"risks": risks, "actionables": actionables}


def analyze_asset_allocation(allocation: List[Dict]) -> Dict[str, List]:
    """Analyze asset allocation and provide recommendations."""
    summary = []
    actionables = []
    
    equity_pct = 0
    debt_pct = 0
    
    for asset in allocation:
        asset_class = asset.get("asset_class", "").lower()
        pct = asset.get("percentage", 0)
        
        if asset_class == "equity":
            equity_pct = pct
        elif asset_class == "debt":
            debt_pct = pct
    
    # Asset allocation insights
    if equity_pct > 80:
        summary.append({
            "type": "allocation",
            "title": "Aggressive Portfolio",
            "description": f"Your portfolio is {equity_pct:.0f}% in equity - suitable for long-term goals (7+ years) with high risk tolerance."
        })
        actionables.append({
            "priority": "low",
            "action": "Consider Adding Debt",
            "description": "For stability during market corrections, consider 10-20% allocation to debt funds.",
            "impact": "Reduced volatility, emergency liquidity"
        })
    elif equity_pct < 40:
        summary.append({
            "type": "allocation",
            "title": "Conservative Portfolio",
            "description": f"Your portfolio has only {equity_pct:.0f}% in equity - may not beat inflation long-term."
        })
        actionables.append({
            "priority": "medium",
            "action": "Increase Equity Exposure",
            "description": "If your investment horizon is 5+ years, consider increasing equity to 60-70%.",
            "impact": "Better long-term wealth creation potential"
        })
    else:
        summary.append({
            "type": "allocation",
            "title": "Balanced Portfolio",
            "description": f"Your {equity_pct:.0f}% equity and {debt_pct:.0f}% debt allocation is well-balanced for moderate risk."
        })
    
    return {"summary": summary, "actionables": actionables}


def analyze_amc_diversification(amc_allocation: List[Dict]) -> Dict[str, List]:
    """Analyze AMC-level diversification."""
    risks = []
    
    if not amc_allocation:
        return {"risks": risks}
    
    top_amc = amc_allocation[0]
    if top_amc.get("percentage", 0) > 60:
        risks.append({
            "type": "amc_concentration",
            "severity": "low",
            "title": "AMC Concentration",
            "description": f"{top_amc['percentage']:.0f}% of your portfolio is with {top_amc['amc']}.",
            "recommendation": "Consider diversifying across 3-4 AMCs to reduce operational risk."
        })
    
    return {"risks": risks}


def analyze_performance(holdings: List[Dict]) -> Dict[str, List]:
    """Analyze fund performance and identify opportunities."""
    summary = []
    opportunities = []
    
    # Find underperformers
    underperformers = [h for h in holdings if h.get("percentage_return", 0) < 0]
    outperformers = [h for h in holdings if h.get("percentage_return", 0) > 15]
    
    if underperformers:
        total_loss = sum(h.get("absolute_return", 0) for h in underperformers)
        summary.append({
            "type": "performance",
            "title": "Underperforming Funds",
            "description": f"{len(underperformers)} funds are in loss, totaling ₹{abs(total_loss):,.0f} unrealized loss."
        })
        
        for fund in underperformers[:3]:  # Top 3 losers
            opportunities.append({
                "type": "review_needed",
                "fund": fund["scheme_name"][:50],
                "return": f"{fund['percentage_return']:.1f}%",
                "suggestion": "Review fund's recent performance and consider switching if consistently underperforming benchmark."
            })
    
    if outperformers:
        total_gain = sum(h.get("absolute_return", 0) for h in outperformers)
        summary.append({
            "type": "performance",
            "title": "Strong Performers",
            "description": f"{len(outperformers)} funds have delivered >15% returns, totaling ₹{total_gain:,.0f} in gains."
        })
    
    return {"summary": summary, "opportunities": opportunities}


def detect_fund_overlap(holdings: List[Dict]) -> Dict[str, List]:
    """Detect potential fund overlap issues."""
    risks = []
    actionables = []
    
    # Group by asset class
    equity_funds = [h for h in holdings if h.get("asset_class") == "equity"]
    
    # Check for similar fund categories
    large_cap_funds = []
    flexi_cap_funds = []
    index_funds = []
    
    for fund in equity_funds:
        name_lower = fund.get("scheme_name", "").lower()
        if "large cap" in name_lower or "largecap" in name_lower or "bluechip" in name_lower:
            large_cap_funds.append(fund)
        if "flexi" in name_lower or "multi" in name_lower:
            flexi_cap_funds.append(fund)
        if "index" in name_lower or "nifty" in name_lower or "sensex" in name_lower:
            index_funds.append(fund)
    
    if len(large_cap_funds) > 2:
        risks.append({
            "type": "fund_overlap",
            "severity": "medium",
            "title": "Large Cap Fund Overlap",
            "description": f"You have {len(large_cap_funds)} large cap funds which likely hold similar stocks.",
            "recommendation": "Large cap funds typically hold the same top 50-100 stocks. Consider consolidating into 1-2 funds."
        })
        actionables.append({
            "priority": "medium",
            "action": "Consolidate Large Cap Funds",
            "description": "Keep 1 active large cap fund OR switch entirely to a low-cost Nifty 50 index fund.",
            "impact": "Reduced overlap, lower expense ratio, simpler tracking"
        })
    
    if len(flexi_cap_funds) > 2:
        risks.append({
            "type": "fund_overlap",
            "severity": "low",
            "title": "Multiple Flexi Cap Funds",
            "description": f"You have {len(flexi_cap_funds)} flexi/multi cap funds with overlapping mandates.",
            "recommendation": "Consider keeping 1-2 best performing flexi cap funds."
        })
    
    return {"risks": risks, "actionables": actionables}


def calculate_health_score(insights: Dict, portfolio: Dict) -> Dict[str, Any]:
    """Calculate overall portfolio health score."""
    score = 100
    factors = []
    
    # Deduct for risks
    high_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "high"])
    medium_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "medium"])
    low_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "low"])
    
    score -= high_risks * 15
    score -= medium_risks * 8
    score -= low_risks * 3
    
    # Add for good performance
    summary = portfolio.get("summary", {})
    return_pct = summary.get("return_percentage", 0)
    
    if return_pct > 12:
        score += 5
        factors.append("Strong returns")
    elif return_pct < 0:
        score -= 10
        factors.append("Negative returns")
    
    # Diversification bonus
    scheme_count = summary.get("scheme_count", 0)
    if 5 <= scheme_count <= 12:
        score += 5
        factors.append("Good diversification")
    
    score = max(0, min(100, score))  # Clamp between 0-100
    
    # Determine grade
    if score >= 80:
        grade = "A"
        verdict = "Excellent"
    elif score >= 65:
        grade = "B"
        verdict = "Good"
    elif score >= 50:
        grade = "C"
        verdict = "Average"
    else:
        grade = "D"
        verdict = "Needs Attention"
    
    return {
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "factors": factors
    }

