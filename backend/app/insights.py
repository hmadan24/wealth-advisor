"""
Portfolio Insights Engine

Generates actionable insights and recommendations from portfolio data.
"""
from typing import Dict, Any, List
from app.rules_config import rules


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
    summary = portfolio.get("summary", {})
    
    # 1. Portfolio Concentration Analysis
    concentration_insights = analyze_concentration(holdings, summary)
    insights["risks"].extend(concentration_insights.get("risks", []))
    insights["actionables"].extend(concentration_insights.get("actionables", []))
    
    # 2. Asset Allocation Analysis
    allocation_insights = analyze_asset_allocation(asset_allocation)
    insights["summary_insights"].extend(allocation_insights.get("summary", []))
    insights["actionables"].extend(allocation_insights.get("actionables", []))
    
    # 3. Performance Analysis
    performance_insights = analyze_performance(holdings)
    insights["summary_insights"].extend(performance_insights.get("summary", []))
    insights["opportunities"].extend(performance_insights.get("opportunities", []))
    
    # 4. Fund Overlap Detection
    overlap_insights = detect_fund_overlap(holdings)
    insights["risks"].extend(overlap_insights.get("risks", []))
    insights["actionables"].extend(overlap_insights.get("actionables", []))
    
    # 5. Portfolio Health Score
    insights["health_score"] = calculate_health_score(insights, portfolio)
    
    return insights


def analyze_concentration(holdings: List[Dict], summary: Dict) -> Dict[str, List]:
    """Analyze portfolio concentration risks."""
    risks = []
    actionables = []
    
    total_value = summary.get("total_value", 0)
    if total_value == 0:
        return {"risks": risks, "actionables": actionables}
    
    # Get concentration rules from config
    conc_rules = rules.concentration
    
    # Check top holding concentration
    if holdings:
        top_holding = holdings[0]
        top_concentration = (top_holding["current_value"] / total_value)
        
        if top_concentration > conc_rules["high"]["threshold"]:
            high_rule = conc_rules["high"]
            risks.append({
                "type": "high_concentration",
                "severity": high_rule["severity"],
                "title": high_rule["title"],
                "description": high_rule["description_template"].format(
                    fund_name=top_holding['scheme_name'][:40],
                    percentage=top_concentration * 100
                ),
                "recommendation": high_rule["recommendation"]
            })
        elif top_concentration > conc_rules["moderate"]["threshold"]:
            mod_rule = conc_rules["moderate"]
            risks.append({
                "type": "moderate_concentration",
                "severity": mod_rule["severity"],
                "title": mod_rule["title"],
                "description": mod_rule["description_template"].format(
                    percentage=top_concentration * 100
                ),
                "recommendation": mod_rule["recommendation"]
            })
    
    # Check if portfolio is too fragmented
    div_rules = rules.diversification
    scheme_count = summary.get("scheme_count", 0)
    over_div = div_rules["over_diversified"]
    
    if scheme_count > over_div["threshold"]:
        risks.append({
            "type": "over_diversification",
            "severity": over_div["severity"],
            "title": over_div["title"],
            "description": over_div["description_template"].format(count=scheme_count),
            "recommendation": over_div["recommendation"]
        })
        actionables.append({
            "priority": over_div["actionable"]["priority"],
            "action": over_div["actionable"]["action"],
            "description": over_div["actionable"]["description_template"].format(count=scheme_count),
            "impact": over_div["actionable"]["impact"]
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
        
        # Include both Indian equity and US equity in total equity calculation
        if asset_class in ["equity", "us equity"]:
            equity_pct += pct
        elif asset_class == "debt":
            debt_pct += pct
    
    # Get asset allocation rules from config
    alloc_rules = rules.asset_allocation
    equity_ratio = equity_pct / 100
    
    # Asset allocation insights
    if equity_ratio > alloc_rules["aggressive"]["equity_threshold"]:
        agg_rule = alloc_rules["aggressive"]
        summary.append({
            "type": "allocation",
            "title": agg_rule["title"],
            "description": agg_rule["description_template"].format(percentage=equity_pct)
        })
        actionables.append({
            "priority": agg_rule["actionable"]["priority"],
            "action": agg_rule["actionable"]["action"],
            "description": agg_rule["actionable"]["description"],
            "impact": agg_rule["actionable"]["impact"]
        })
    elif equity_ratio < alloc_rules["conservative"]["equity_threshold"]:
        cons_rule = alloc_rules["conservative"]
        summary.append({
            "type": "allocation",
            "title": cons_rule["title"],
            "description": cons_rule["description_template"].format(percentage=equity_pct)
        })
        actionables.append({
            "priority": cons_rule["actionable"]["priority"],
            "action": cons_rule["actionable"]["action"],
            "description": cons_rule["actionable"]["description"],
            "impact": cons_rule["actionable"]["impact"]
        })
    else:
        bal_rule = alloc_rules["balanced"]
        summary.append({
            "type": "allocation",
            "title": bal_rule["title"],
            "description": bal_rule["description_template"].format(
                equity_pct=equity_pct,
                debt_pct=debt_pct
            )
        })
    
    return {"summary": summary, "actionables": actionables}


def analyze_performance(holdings: List[Dict]) -> Dict[str, List]:
    """Analyze fund performance and identify opportunities."""
    summary = []
    opportunities = []
    
    # Get performance rules from config
    perf_rules = rules.performance
    
    # Find underperformers and outperformers
    underperformers = [h for h in holdings if h.get("percentage_return", 0) < perf_rules["underperformer_threshold"]]
    outperformers = [h for h in holdings if h.get("percentage_return", 0) > perf_rules["strong_performer_threshold"] * 100]
    
    if underperformers:
        total_loss = sum(h.get("absolute_return", 0) for h in underperformers)
        summary.append({
            "type": "performance",
            "title": "Underperforming Funds",
            "description": f"{len(underperformers)} funds are in loss, totaling ₹{abs(total_loss):,.0f} unrealized loss."
        })
        
        # Top N underperformers
        for fund in underperformers[:perf_rules["top_underperformers_to_show"]]:
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
    
    # Get fund overlap rules from config
    overlap_rules = rules.fund_overlap
    
    # Group by asset class
    equity_funds = [h for h in holdings if h.get("asset_class") == "equity"]
    
    # Check for similar fund categories
    large_cap_funds = []
    flexi_cap_funds = []
    
    for fund in equity_funds:
        name_lower = fund.get("scheme_name", "").lower()
        
        # Check large cap
        if any(keyword in name_lower for keyword in overlap_rules["large_cap"]["keywords"]):
            large_cap_funds.append(fund)
        
        # Check flexi cap
        if any(keyword in name_lower for keyword in overlap_rules["flexi_cap"]["keywords"]):
            flexi_cap_funds.append(fund)
    
    # Large cap overlap check
    if len(large_cap_funds) > overlap_rules["large_cap"]["threshold"]:
        lc_rule = overlap_rules["large_cap"]
        risks.append({
            "type": "fund_overlap",
            "severity": lc_rule["severity"],
            "title": lc_rule["title"],
            "description": lc_rule["description_template"].format(count=len(large_cap_funds)),
            "recommendation": lc_rule["recommendation"]
        })
        actionables.append({
            "priority": lc_rule["actionable"]["priority"],
            "action": lc_rule["actionable"]["action"],
            "description": lc_rule["actionable"]["description"],
            "impact": lc_rule["actionable"]["impact"]
        })
    
    # Flexi cap overlap check
    if len(flexi_cap_funds) > overlap_rules["flexi_cap"]["threshold"]:
        fc_rule = overlap_rules["flexi_cap"]
        risks.append({
            "type": "fund_overlap",
            "severity": fc_rule["severity"],
            "title": fc_rule["title"],
            "description": fc_rule["description_template"].format(count=len(flexi_cap_funds)),
            "recommendation": fc_rule["recommendation"]
        })
    
    return {"risks": risks, "actionables": actionables}


def calculate_health_score(insights: Dict, portfolio: Dict) -> Dict[str, Any]:
    """Calculate overall portfolio health score."""
    score = 100
    factors = []
    
    # Get health score rules from config
    hs_rules = rules.health_score
    penalties = hs_rules["penalties"]
    
    # Deduct for risks
    high_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "high"])
    medium_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "medium"])
    low_risks = len([r for r in insights.get("risks", []) if r.get("severity") == "low"])
    
    score -= high_risks * penalties["high_risk"]
    score -= medium_risks * penalties["medium_risk"]
    score -= low_risks * penalties["low_risk"]
    
    # Add for good performance
    bonuses = hs_rules["bonuses"]
    summary = portfolio.get("summary", {})
    return_pct = summary.get("return_percentage", 0) / 100
    
    if return_pct > bonuses["strong_returns_threshold"]:
        score += bonuses["strong_returns_bonus"]
        factors.append("Strong returns")
    elif return_pct < 0:
        score -= bonuses["negative_returns_penalty"]
        factors.append("Negative returns")
    
    # Diversification bonus
    scheme_count = summary.get("scheme_count", 0)
    if bonuses["diversification_min"] <= scheme_count <= bonuses["diversification_max"]:
        score += bonuses["diversification_bonus"]
        factors.append("Good diversification")
    
    score = max(0, min(100, score))  # Clamp between 0-100
    
    # Determine grade
    grades = hs_rules["grades"]
    if score >= grades["A"]["min_score"]:
        grade = "A"
        verdict = grades["A"]["verdict"]
    elif score >= grades["B"]["min_score"]:
        grade = "B"
        verdict = grades["B"]["verdict"]
    elif score >= grades["C"]["min_score"]:
        grade = "C"
        verdict = grades["C"]["verdict"]
    else:
        grade = "D"
        verdict = grades["D"]["verdict"]
    
    return {
        "score": score,
        "grade": grade,
        "verdict": verdict,
        "factors": factors
    }
