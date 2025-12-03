"""
US Equity PDF Parser (VF Securities / Vested format)

Parses account statements from Vested/VF Securities to extract US stock holdings.
Converts USD values to INR for consistent display.
"""
import fitz  # PyMuPDF
import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

# USD to INR exchange rate (update this periodically or fetch from API)
USD_TO_INR = 84.50


def parse_us_equity_pdf(file_path: str) -> Dict[str, Any]:
    """
    Parse VF Securities / Vested account statement PDF.
    Uses text extraction and regex patterns.
    """
    try:
        doc = fitz.open(file_path)
        
        holdings = []
        total_value = 0.0
        total_invested = 0.0
        account_name = ""
        
        # Get all text from PDF
        all_text = ""
        for page in doc:
            all_text += page.get_text() + "\n"
        
        # Extract account name
        name_match = re.search(r'Account Name[:\s]*([A-Za-z\s]+?)(?:\n|Account)', all_text)
        if name_match:
            account_name = name_match.group(1).strip()
        
        logger.info(f"Account name: {account_name}")
        
        # Find the Holdings/Equity section
        # Pattern to match stock rows:
        # Description (with spaces) | Symbol | Quantity | Unit Cost | Total Cost | Market Price | Market Value | Gain/(Loss) | A/C Type
        
        # First, let's try to find the data using a different approach - 
        # extract tables properly using layout analysis
        
        for page_num, page in enumerate(doc):
            # Get text with layout preservation
            blocks = page.get_text("dict")["blocks"]
            
            # Try to find table-like structures
            lines = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        for span in line["spans"]:
                            line_text += span["text"] + " "
                        lines.append(line_text.strip())
            
            logger.info(f"Page {page_num + 1}: {len(lines)} text lines")
        
        # Alternative: Parse using word positions
        for page_num, page in enumerate(doc):
            words = page.get_text("words")  # Returns list of (x0, y0, x1, y1, word, block_no, line_no, word_no)
            
            if not words:
                continue
            
            # Group words by y-position (same line)
            lines_by_y = {}
            for word in words:
                y = round(word[1] / 5) * 5  # Round to nearest 5 pixels
                if y not in lines_by_y:
                    lines_by_y[y] = []
                lines_by_y[y].append((word[0], word[4]))  # (x position, text)
            
            # Sort each line by x position
            for y in lines_by_y:
                lines_by_y[y].sort(key=lambda x: x[0])
            
            # Process lines looking for stock data
            sorted_ys = sorted(lines_by_y.keys())
            
            in_holdings_section = False
            
            for y in sorted_ys:
                line_words = [w[1] for w in lines_by_y[y]]
                line_text = " ".join(line_words)
                
                # Check if we're entering holdings section
                if "HOLDINGS" in line_text.upper() or "Equity" in line_text:
                    in_holdings_section = True
                    continue
                
                if "ACTIVITY" in line_text.upper():
                    in_holdings_section = False
                    continue
                
                if not in_holdings_section:
                    continue
                
                # Try to parse as a stock row
                # Look for patterns like: STOCK NAME ... SYMBOL NUMBER NUMBER NUMBER ...
                holding = try_parse_stock_line(line_words, lines_by_y[y])
                
                if holding:
                    holdings.append(holding)
                    # Use original USD values for totals
                    total_value += holding.get('usd_value', 0)
                    total_invested += holding.get('usd_invested', 0)
                    logger.info(f"Found: {holding['symbol']} - ${holding.get('usd_value', 0)}")
        
        doc.close()
        
        # If no holdings found with word-based parsing, try regex on full text
        if not holdings:
            logger.info("Trying regex-based parsing...")
            holdings, total_value, total_invested = parse_with_regex(all_text)
        
        # Sort by value
        holdings.sort(key=lambda x: x['current_value'], reverse=True)
        
        # Convert totals to INR
        total_value_inr = total_value * USD_TO_INR
        total_invested_inr = total_invested * USD_TO_INR
        total_return_inr = total_value_inr - total_invested_inr
        return_pct = (total_return_inr / total_invested_inr * 100) if total_invested_inr > 0 else 0
        
        logger.info(f"Parsed {len(holdings)} US equity holdings, Total: ${total_value:.2f} (₹{total_value_inr:.2f})")
        
        return {
            "investor": {
                "name": account_name,
                "email": "",
                "mobile": "",
            },
            "summary": {
                "total_value": round(total_value_inr, 2),  # INR
                "total_invested": round(total_invested_inr, 2),  # INR
                "total_return": round(total_return_inr, 2),  # INR
                "return_percentage": round(return_pct, 2),
                "scheme_count": len(holdings),
                "folio_count": 1,
                "currency": "INR",
                "usd_total": round(total_value, 2),  # Keep USD total for reference
                "exchange_rate": USD_TO_INR,
            },
            "holdings": holdings,
            "asset_allocation": [
                {
                    "asset_class": "US Equity",
                    "value": round(total_value_inr, 2),  # INR
                    "percentage": 100.0,
                    "scheme_count": len(holdings)
                }
            ] if holdings else [],
            "amc_allocation": [
                {
                    "amc": "Vested",
                    "value": round(total_value_inr, 2),  # INR
                    "percentage": 100.0,
                    "scheme_count": len(holdings)
                }
            ] if holdings else [],
            "statement_period": {},
            "source": "us_equity_pdf",
        }
        
    except Exception as e:
        logger.error(f"US Equity PDF parse error: {str(e)}", exc_info=True)
        raise Exception(f"Failed to parse US Equity PDF: {str(e)}")


def try_parse_stock_line(words: List[str], word_positions: List[tuple]) -> Optional[Dict]:
    """Try to parse a line as a stock holding."""
    
    # Need at least symbol + several numbers
    if len(words) < 5:
        return None
    
    # Look for a stock symbol (2-5 uppercase letters)
    symbol = None
    symbol_idx = -1
    
    for i, word in enumerate(words):
        # Stock symbols are typically 1-5 uppercase letters
        if re.match(r'^[A-Z]{1,5}$', word) and word not in ['COM', 'INC', 'ETF', 'TR', 'CLASS', 'CL', 'A', 'B', 'C', 'NEW', 'DEL']:
            # Check if followed by numbers (quantity, prices)
            numbers_after = sum(1 for w in words[i+1:] if is_number(w))
            if numbers_after >= 3:
                symbol = word
                symbol_idx = i
                break
    
    if not symbol:
        return None
    
    # Get description (everything before symbol)
    description = " ".join(words[:symbol_idx]).strip()
    
    # Get numbers after symbol
    numbers = []
    for word in words[symbol_idx + 1:]:
        num = parse_number(word)
        if num is not None:
            numbers.append(num)
    
    # We expect: Quantity, Unit Cost, Total Cost, Market Price, Market Value, Gain/Loss
    if len(numbers) < 5:
        return None
    
    quantity = numbers[0]
    unit_cost = numbers[1]
    total_cost = numbers[2]
    market_price = numbers[3]
    market_value = numbers[4]
    gain_loss = numbers[5] if len(numbers) > 5 else (market_value - total_cost)
    
    if quantity <= 0 or market_value <= 0:
        return None
    
    pct_return = (gain_loss / total_cost * 100) if total_cost > 0 else 0
    clean_name = clean_description(description, symbol)
    
    # Convert USD to INR
    return {
        "folio": "Vested",
        "amc": "Vested",
        "scheme_name": clean_name,
        "isin": "",
        "symbol": symbol,
        "units": round(quantity, 6),
        "nav": round(market_price * USD_TO_INR, 2),  # Convert to INR
        "current_value": round(market_value * USD_TO_INR, 2),  # Convert to INR
        "invested_amount": round(total_cost * USD_TO_INR, 2),  # Convert to INR
        "absolute_return": round(gain_loss * USD_TO_INR, 2),  # Convert to INR
        "percentage_return": round(pct_return, 2),  # Percentage stays same
        "asset_class": "us_equity",
        "valuation_date": "",
        "currency": "USD",  # Original currency marker
        "usd_value": round(market_value, 2),  # Keep original USD value
        "usd_invested": round(total_cost, 2),  # Keep original USD invested
    }


def parse_with_regex(text: str) -> tuple:
    """Parse holdings using regex patterns."""
    holdings = []
    total_value = 0.0
    total_invested = 0.0
    
    # Known US stock symbols and their names
    known_stocks = {
        'AAPL': 'Apple Inc',
        'AMZN': 'Amazon',
        'ARKK': 'ARK Innovation ETF',
        'BRK.B': 'Berkshire Hathaway',
        'FIG': 'Figma Inc',
        'GOOGL': 'Alphabet (Google)',
        'ITA': 'iShares US Aerospace & Defense ETF',
        'JPM': 'JPMorgan Chase',
        'META': 'Meta (Facebook)',
        'METV': 'Roundhill Ball Metaverse ETF',
        'MSFT': 'Microsoft',
        'SHOP': 'Shopify',
        'SOXX': 'iShares Semiconductor ETF',
        'XYZ': 'Block Inc',
        'TSLA': 'Tesla',
        'NVDA': 'NVIDIA',
        'NFLX': 'Netflix',
        'DIS': 'Disney',
        'V': 'Visa',
        'MA': 'Mastercard',
        'DWBS': 'DW Bank Sweep',
    }
    
    # Pattern to find stock rows - look for symbol followed by numbers
    # Format: SYMBOL followed by quantity, unit cost, total cost, market price, market value, gain/loss
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Try to find known symbols in the line
        for symbol, name in known_stocks.items():
            if symbol in line.upper().split():
                # Try to extract numbers from this line and nearby lines
                combined = line
                if i + 1 < len(lines):
                    combined += " " + lines[i + 1]
                
                numbers = extract_numbers(combined)
                
                if len(numbers) >= 5:
                    quantity = numbers[0]
                    unit_cost = numbers[1]
                    total_cost = numbers[2]
                    market_price = numbers[3]
                    market_value = numbers[4]
                    gain_loss = numbers[5] if len(numbers) > 5 else (market_value - total_cost)
                    
                        # Validate - market value should be positive and reasonable
                    if market_value > 0 and quantity > 0:
                        pct_return = (gain_loss / total_cost * 100) if total_cost > 0 else 0
                        
                        # Convert USD to INR
                        holding = {
                            "folio": "Vested",
                            "amc": "Vested",
                            "scheme_name": name,
                            "isin": "",
                            "symbol": symbol,
                            "units": round(quantity, 6),
                            "nav": round(market_price * USD_TO_INR, 2),  # Convert to INR
                            "current_value": round(market_value * USD_TO_INR, 2),  # Convert to INR
                            "invested_amount": round(total_cost * USD_TO_INR, 2),  # Convert to INR
                            "absolute_return": round(gain_loss * USD_TO_INR, 2),  # Convert to INR
                            "percentage_return": round(pct_return, 2),  # Percentage stays same
                            "asset_class": "us_equity",
                            "valuation_date": "",
                            "currency": "USD",  # Original currency marker
                            "usd_value": round(market_value, 2),  # Keep original USD value
                            "usd_invested": round(total_cost, 2),  # Keep original USD invested
                        }
                        
                        # Avoid duplicates
                        if not any(h['symbol'] == symbol for h in holdings):
                            holdings.append(holding)
                            total_value += market_value
                            total_invested += total_cost
                            logger.info(f"Regex found: {symbol} - ${market_value}")
                        break
    
    return holdings, total_value, total_invested


def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    numbers = []
    # Match numbers including decimals and negative (with parentheses)
    pattern = r'[\d,]+\.?\d*|\([\d,]+\.?\d*\)'
    
    for match in re.findall(pattern, text):
        num = parse_number(match)
        if num is not None and num != 0:
            numbers.append(num)
    
    return numbers


def is_number(s: str) -> bool:
    """Check if string is a number."""
    s = s.replace(',', '').replace('$', '')
    if s.startswith('(') and s.endswith(')'):
        s = s[1:-1]
    try:
        float(s)
        return True
    except ValueError:
        return False


def parse_number(value: str) -> Optional[float]:
    """Parse number from string, handling parentheses for negative."""
    if not value:
        return None
    
    # Remove currency symbols and commas
    value = str(value).replace('$', '').replace(',', '').strip()
    
    # Handle parentheses for negative numbers
    if value.startswith('(') and value.endswith(')'):
        value = '-' + value[1:-1]
    
    try:
        return float(value)
    except ValueError:
        return None


def clean_description(description: str, symbol: str) -> str:
    """Clean up stock description to readable name."""
    if not description:
        return symbol
    
    # Known mappings
    name_map = {
        'AAPL': 'Apple Inc',
        'AMZN': 'Amazon',
        'ARKK': 'ARK Innovation ETF',
        'BRK.B': 'Berkshire Hathaway',
        'GOOGL': 'Alphabet (Google)',
        'META': 'Meta (Facebook)',
        'MSFT': 'Microsoft',
        'JPM': 'JPMorgan Chase',
        'SHOP': 'Shopify',
        'TSLA': 'Tesla',
        'NVDA': 'NVIDIA',
    }
    
    if symbol in name_map:
        return name_map[symbol]
    
    # Clean up the description
    name = description.upper()
    suffixes = [' COM', ' INC', ' CORP', ' CLASS A', ' CLASS B', ' CL A', ' CL B', ' ETF', ' TR', ' LTD', ' NEW', ' DEL']
    
    for suffix in suffixes:
        name = name.replace(suffix, '')
    
    return name.strip().title() if name.strip() else symbol


def is_us_equity_pdf(file_path: str) -> bool:
    """
    Check if the PDF is a VF Securities / Vested account statement.
    Priority: Filename patterns > Definitive text indicators > Content analysis
    """
    try:
        import os
        filename = os.path.basename(file_path).lower()
        
        # ============ CHECK FILENAME FIRST (HIGHEST PRIORITY) ============
        # Vested PDFs have distinctive filename patterns
        if 'vstf' in filename or 'vsvt' in filename:
            logger.info(f"US Equity PDF detected via filename pattern: {filename}")
            return True
        
        # ============ NOW CHECK TEXT CONTENT ============
        doc = fitz.open(file_path)
        
        # Get text from first few pages (enough for detection)
        all_text = ""
        for i, page in enumerate(doc):
            if i >= 3:  # Only check first 3 pages for detection
                break
            all_text += page.get_text().lower() + " "
        doc.close()
        
        # Definitive US equity indicators - these are unique to US brokerage statements
        definitive_us_indicators = [
            'vf securities',
            'drivewealth',
            'alpaca securities',
            'clearing by apex',
            'account type: individual',  # US brokerage specific
        ]
        
        for indicator in definitive_us_indicators:
            if indicator in all_text:
                logger.info(f"US Equity PDF detected via definitive indicator: {indicator}")
                return True
        
        # ============ CHECK FOR INDIAN CAS INDICATORS ============
        # These indicate it's definitely NOT a US equity PDF
        indian_cas_indicators = [
            'nsdl',
            'cdsl', 
            'consolidated account statement',
            'depository participant',
            'demat account',
            'folio no',
            'pan:',
            'cams',
            'karvy',
            'kfintech',
            'sebi registration',
        ]
        
        indian_matches = sum(1 for ind in indian_cas_indicators if ind in all_text)
        
        if indian_matches >= 2:
            logger.info(f"Indian CAS PDF detected ({indian_matches} indicators found), NOT US equity")
            return False
        
        # Check for US stock symbols (at least 3 different ones)
        us_symbols = ['aapl', 'googl', 'goog', 'msft', 'amzn', 'meta', 'tsla', 'nvda', 'nflx', 'spy', 'qqq', 'voo']
        symbol_matches = sum(1 for sym in us_symbols if f' {sym} ' in all_text or f' {sym},' in all_text)
        
        if symbol_matches >= 3:
            logger.info(f"US Equity PDF detected via US stock symbols: {symbol_matches} matches")
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"Error checking if US equity PDF: {e}")
        return False
