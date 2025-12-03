"""
NSDL CAS PDF Parser

Uses casparser library to extract portfolio data from password-protected CAS PDFs.
Handles both NSDL CAS (with demat accounts) and CAMS CAS (with folios) formats.
"""
import casparser
from casparser.types import NSDLCASData
from typing import Dict, Any, List
from datetime import datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def parse_cas_file(file_path: str, password: str) -> Dict[str, Any]:
    """
    Parse NSDL CAS PDF file and extract portfolio data.
    """
    try:
        data = casparser.read_cas_pdf(file_path, password)
        
        logger.info(f"CAS Data type: {type(data)}")
        
        # Check if it's NSDL CAS format
        if isinstance(data, NSDLCASData):
            logger.info("Detected NSDL CAS format")
            return transform_nsdl_cas_data(data)
        else:
            logger.info("Detected CAMS CAS format")
            return transform_cams_cas_data(data)
        
    except Exception as e:
        logger.error(f"Parse error: {str(e)}", exc_info=True)
        raise Exception(f"Failed to parse CAS file: {str(e)}")


def to_float(val) -> float:
    """Convert Decimal or any numeric to float."""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def transform_nsdl_cas_data(cas_data: NSDLCASData) -> Dict[str, Any]:
    """Transform NSDL CAS data (demat accounts) to our portfolio format."""
    
    holdings = []
    total_value = 0.0
    
    # Asset class aggregations
    asset_classes = {
        "equity": {"value": 0, "schemes": []},
        "debt": {"value": 0, "schemes": []},
        "hybrid": {"value": 0, "schemes": []},
        "gold": {"value": 0, "schemes": []},
        "other": {"value": 0, "schemes": []},
    }
    
    # Broker/AMC-wise aggregation
    broker_holdings = {}
    
    accounts = cas_data.accounts or []
    logger.info(f"Number of demat accounts: {len(accounts)}")
    
    for account in accounts:
        broker_name = account.name or "Unknown Broker"
        account_type = account.type or ""
        dp_id = account.dp_id or ""
        client_id = account.client_id or ""
        
        logger.info(f"Processing account: {broker_name} ({account_type})")
        
        # Process Equities
        equities = account.equities or []
        logger.info(f"  Equities: {len(equities)}")
        
        for equity in equities:
            name = equity.name or f"ISIN: {equity.isin}"
            isin = equity.isin or ""
            num_shares = to_float(equity.num_shares)
            price = to_float(equity.price)
            value = to_float(equity.value)
            
            holding = {
                "folio": f"{dp_id}-{client_id}",
                "amc": broker_name,
                "scheme_name": name,
                "isin": isin,
                "units": round(num_shares, 3),
                "nav": round(price, 4),
                "current_value": round(value, 2),
                "invested_amount": 0,  # Not available in NSDL CAS
                "absolute_return": 0,
                "percentage_return": 0,
                "asset_class": "equity",
                "valuation_date": "",
                "account_type": account_type,
            }
            
            if value > 0 or num_shares > 0:
                holdings.append(holding)
                total_value += value
                asset_classes["equity"]["value"] += value
                asset_classes["equity"]["schemes"].append(name)
                
                if broker_name not in broker_holdings:
                    broker_holdings[broker_name] = {"value": 0, "schemes": 0}
                broker_holdings[broker_name]["value"] += value
                broker_holdings[broker_name]["schemes"] += 1
        
        # Process Mutual Funds (in demat)
        mutual_funds = account.mutual_funds or []
        logger.info(f"  Mutual Funds: {len(mutual_funds)}")
        
        for mf in mutual_funds:
            name = mf.name or f"ISIN: {mf.isin}"
            isin = mf.isin or ""
            units = to_float(mf.balance)
            nav = to_float(mf.nav)
            value = to_float(mf.value)
            
            # Classify the mutual fund
            asset_class = classify_scheme(name)
            
            holding = {
                "folio": f"{dp_id}-{client_id}",
                "amc": broker_name,
                "scheme_name": name,
                "isin": isin,
                "units": round(units, 3),
                "nav": round(nav, 4),
                "current_value": round(value, 2),
                "invested_amount": 0,  # Not available in NSDL CAS
                "absolute_return": 0,
                "percentage_return": 0,
                "asset_class": asset_class,
                "valuation_date": "",
                "account_type": account_type,
            }
            
            if value > 0 or units > 0:
                holdings.append(holding)
                total_value += value
                asset_classes[asset_class]["value"] += value
                asset_classes[asset_class]["schemes"].append(name)
                
                if broker_name not in broker_holdings:
                    broker_holdings[broker_name] = {"value": 0, "schemes": 0}
                broker_holdings[broker_name]["value"] += value
                broker_holdings[broker_name]["schemes"] += 1
    
    # Calculate asset allocation percentages
    asset_allocation = []
    for asset_class, data in asset_classes.items():
        if data["value"] > 0:
            asset_allocation.append({
                "asset_class": asset_class.title(),
                "value": round(data["value"], 2),
                "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0,
                "scheme_count": len(data["schemes"])
            })
    
    # Sort by value descending
    asset_allocation.sort(key=lambda x: x["value"], reverse=True)
    holdings.sort(key=lambda x: x["current_value"], reverse=True)
    
    # Broker allocation
    amc_allocation = [
        {
            "amc": broker,
            "value": round(data["value"], 2),
            "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0,
            "scheme_count": data["schemes"]
        }
        for broker, data in broker_holdings.items()
    ]
    amc_allocation.sort(key=lambda x: x["value"], reverse=True)
    
    # Extract investor info
    investor_info = cas_data.investor_info
    investor_name = getattr(investor_info, 'name', '') if investor_info else ''
    investor_email = getattr(investor_info, 'email', '') if investor_info else ''
    investor_mobile = getattr(investor_info, 'mobile', '') if investor_info else ''
    
    # Statement period
    statement_period = cas_data.statement_period
    period_from = str(getattr(statement_period, 'from_', '')) if statement_period else ''
    period_to = str(getattr(statement_period, 'to', '')) if statement_period else ''
    
    logger.info(f"Total holdings: {len(holdings)}, Total value: {total_value}")
    
    return {
        "investor": {
            "name": str(investor_name) if investor_name else "",
            "email": str(investor_email) if investor_email else "",
            "mobile": str(investor_mobile) if investor_mobile else "",
        },
        "summary": {
            "total_value": round(total_value, 2),
            "total_invested": 0,  # Not available in NSDL CAS
            "total_return": 0,
            "return_percentage": 0,
            "scheme_count": len(holdings),
            "folio_count": len(accounts),
        },
        "holdings": holdings,
        "asset_allocation": asset_allocation,
        "amc_allocation": amc_allocation,
        "statement_period": {
            "from": period_from,
            "to": period_to,
        },
    }


def transform_cams_cas_data(cas_data) -> Dict[str, Any]:
    """Transform CAMS CAS data (folios) to our portfolio format."""
    
    # Handle both dict and object access
    def safe_get(obj, attr, default=None):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    
    investor_info = safe_get(cas_data, "investor_info", {})
    folios = safe_get(cas_data, "folios", []) or []
    
    holdings = []
    total_value = 0.0
    total_invested = 0.0
    
    asset_classes = {
        "equity": {"value": 0, "schemes": []},
        "debt": {"value": 0, "schemes": []},
        "hybrid": {"value": 0, "schemes": []},
        "gold": {"value": 0, "schemes": []},
        "other": {"value": 0, "schemes": []},
    }
    
    amc_holdings = {}
    
    for folio in folios:
        folio_number = safe_get(folio, "folio", "")
        amc = safe_get(folio, "amc", "Unknown AMC")
        schemes = safe_get(folio, "schemes", []) or []
        
        for scheme in schemes:
            scheme_name = safe_get(scheme, "scheme", "")
            isin = safe_get(scheme, "isin", "")
            
            valuation = safe_get(scheme, "valuation", None)
            current_value = to_float(safe_get(valuation, "value", 0)) if valuation else 0
            nav = to_float(safe_get(valuation, "nav", 0)) if valuation else 0
            valuation_date = safe_get(valuation, "date", "") if valuation else ""
            
            units = to_float(safe_get(scheme, "close", 0)) or to_float(safe_get(scheme, "close_calculated", 0)) or 0
            
            if current_value == 0 and units > 0 and nav > 0:
                current_value = units * nav
            
            transactions = safe_get(scheme, "transactions", []) or []
            invested_amount = calculate_invested_amount(transactions)
            
            scheme_type = safe_get(scheme, "type", "")
            asset_class = classify_scheme(scheme_name, scheme_type)
            
            absolute_return = current_value - invested_amount if invested_amount > 0 else 0
            percentage_return = (absolute_return / invested_amount * 100) if invested_amount > 0 else 0
            
            holding = {
                "folio": str(folio_number),
                "amc": str(amc),
                "scheme_name": str(scheme_name),
                "isin": str(isin) if isin else "",
                "units": round(float(units), 3),
                "nav": round(float(nav), 4),
                "current_value": round(float(current_value), 2),
                "invested_amount": round(float(invested_amount), 2),
                "absolute_return": round(float(absolute_return), 2),
                "percentage_return": round(float(percentage_return), 2),
                "asset_class": asset_class,
                "valuation_date": str(valuation_date) if valuation_date else "",
            }
            
            if current_value > 0 or units > 0:
                holdings.append(holding)
                total_value += current_value
                total_invested += invested_amount
                
                asset_classes[asset_class]["value"] += current_value
                asset_classes[asset_class]["schemes"].append(scheme_name)
                
                amc_str = str(amc)
                if amc_str not in amc_holdings:
                    amc_holdings[amc_str] = {"value": 0, "schemes": 0}
                amc_holdings[amc_str]["value"] += current_value
                amc_holdings[amc_str]["schemes"] += 1
    
    asset_allocation = []
    for asset_class, data in asset_classes.items():
        if data["value"] > 0:
            asset_allocation.append({
                "asset_class": asset_class.title(),
                "value": round(data["value"], 2),
                "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0,
                "scheme_count": len(data["schemes"])
            })
    
    asset_allocation.sort(key=lambda x: x["value"], reverse=True)
    holdings.sort(key=lambda x: x["current_value"], reverse=True)
    
    amc_allocation = [
        {
            "amc": amc,
            "value": round(data["value"], 2),
            "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0,
            "scheme_count": data["schemes"]
        }
        for amc, data in amc_holdings.items()
    ]
    amc_allocation.sort(key=lambda x: x["value"], reverse=True)
    
    total_return = total_value - total_invested
    return_percentage = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    def safe_get_nested(obj, attr, default=None):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    
    investor_name = safe_get_nested(investor_info, "name", "")
    investor_email = safe_get_nested(investor_info, "email", "")
    investor_mobile = safe_get_nested(investor_info, "mobile", "")
    
    return {
        "investor": {
            "name": str(investor_name) if investor_name else "",
            "email": str(investor_email) if investor_email else "",
            "mobile": str(investor_mobile) if investor_mobile else "",
        },
        "summary": {
            "total_value": round(total_value, 2),
            "total_invested": round(total_invested, 2),
            "total_return": round(total_return, 2),
            "return_percentage": round(return_percentage, 2),
            "scheme_count": len(holdings),
            "folio_count": len(folios),
        },
        "holdings": holdings,
        "asset_allocation": asset_allocation,
        "amc_allocation": amc_allocation,
        "statement_period": {},
    }


def calculate_invested_amount(transactions: List) -> float:
    """Calculate total invested amount from transactions using FIFO."""
    def safe_get(obj, attr, default=None):
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    
    invested = 0.0
    for txn in transactions:
        txn_type = str(safe_get(txn, "type", "")).upper()
        amount = safe_get(txn, "amount", 0) or 0
        
        if txn_type in ["PURCHASE", "PURCHASE_SIP", "SWITCH_IN", "SWITCH_IN_MERGER", 
                        "REINVESTMENT", "REINVEST", "DIVIDEND_REINVEST"]:
            invested += abs(float(amount))
        elif txn_type in ["REDEMPTION", "SWITCH_OUT", "SWITCH_OUT_MERGER"]:
            invested -= abs(float(amount))
    
    return max(invested, 0)


def classify_scheme(scheme_name: str, scheme_type: str = "") -> str:
    """Classify mutual fund scheme by asset class based on name and type."""
    name_lower = str(scheme_name).lower()
    type_lower = str(scheme_type).lower() if scheme_type else ""
    
    if type_lower:
        if "equity" in type_lower:
            return "equity"
        if "debt" in type_lower or "liquid" in type_lower:
            return "debt"
        if "hybrid" in type_lower:
            return "hybrid"
    
    equity_keywords = [
        "equity", "flexi cap", "flexicap", "large cap", "largecap", "mid cap", "midcap",
        "small cap", "smallcap", "multi cap", "multicap", "focused", "elss", "tax saver",
        "bluechip", "blue chip", "value fund", "contra", "dividend yield", "index fund",
        "nifty", "sensex", "etf", "exchange traded", "thematic", "sectoral", "pharma",
        "banking", "infrastructure", "consumption", "technology", "it fund"
    ]
    
    debt_keywords = [
        "debt", "liquid", "overnight", "ultra short", "money market",
        "low duration", "short duration", "medium duration", "long duration",
        "gilt", "corporate bond", "credit risk", "banking & psu", "psu bond",
        "floater", "fixed maturity", "fmp", "income fund", "bond fund"
    ]
    
    hybrid_keywords = [
        "hybrid", "balanced", "aggressive hybrid", "conservative hybrid", "dynamic",
        "asset allocation", "multi asset", "arbitrage", "equity savings", "balanced advantage"
    ]
    
    gold_keywords = ["gold", "precious metal", "commodities", "silver"]
    
    for keyword in equity_keywords:
        if keyword in name_lower:
            return "equity"
    
    for keyword in debt_keywords:
        if keyword in name_lower:
            return "debt"
    
    for keyword in hybrid_keywords:
        if keyword in name_lower:
            return "hybrid"
    
    for keyword in gold_keywords:
        if keyword in name_lower:
            return "gold"
    
    if "growth" in name_lower and "fund" in name_lower:
        return "equity"
    
    return "other"
