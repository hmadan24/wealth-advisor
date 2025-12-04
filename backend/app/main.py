from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import tempfile
import os
import json
import logging
from datetime import datetime
from copy import deepcopy
import uuid

from app.parser import parse_cas_file
from app.us_equity_parser import parse_us_equity_pdf, is_us_equity_pdf
from app.insights import generate_insights
from app.database import get_db, init_db, User, Portfolio
from app.auth import (
    OTPRequest, OTPVerify, Token, TokenData,
    send_otp, verify_otp, create_access_token,
    get_current_user, require_auth
)
from app.config import settings

# Set up logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Wealth Advisor API",
    description="Parse NSDL CAS and US Equity files, aggregate into unified portfolio",
    version="2.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/api/redoc" if settings.DEBUG else None,
)

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized")
    logger.info(f"CORS origins: {settings.CORS_ORIGINS}")
    logger.info(f"Demo mode: {settings.DEMO_MODE}")
    logger.info(f"Production: {settings.is_production}")

# CORS for React frontend - supports multiple origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PortfolioResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class PortfolioSummary(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    total_value: float
    scheme_count: int


class PortfolioSegment(BaseModel):
    """Represents a segment of the portfolio (CAS, US Equity, etc.)"""
    source: str  # 'cas', 'us_equity', 'manual'
    filename: str
    uploaded_at: str
    holdings_count: int
    total_value: float


@app.get("/")
async def root():
    return {"message": "Wealth Advisor API", "status": "running"}


# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/send-otp")
async def api_send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number."""
    result = send_otp(request.phone)
    
    if result["success"]:
        # Create or update user record
        user = db.query(User).filter(User.phone == request.phone).first()
        if not user:
            user = User(phone=request.phone)
            db.add(user)
            db.commit()
    
    return result


@app.post("/api/auth/verify-otp", response_model=Token)
async def api_verify_otp(request: OTPVerify, db: Session = Depends(get_db)):
    """Verify OTP and return JWT token."""
    if not verify_otp(request.phone, request.otp):
        raise HTTPException(status_code=401, detail="Invalid OTP")
    
    # Update last login
    user = db.query(User).filter(User.phone == request.phone).first()
    if user:
        user.last_login = datetime.utcnow()
        db.commit()
    
    # Generate token
    access_token = create_access_token(request.phone)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        phone=request.phone
    )


@app.get("/api/auth/me")
async def get_me(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get current user info."""
    user = db.query(User).filter(User.phone == current_user.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "phone": user.phone,
        "name": user.name,
        "email": user.email,
        "created_at": str(user.created_at),
        "last_login": str(user.last_login)
    }


# ==================== PORTFOLIO AGGREGATION HELPERS ====================

def get_or_create_master_portfolio(db: Session, phone: str) -> Portfolio:
    """Get or create the master portfolio for a user."""
    portfolio = db.query(Portfolio).filter(
        Portfolio.phone == phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not portfolio:
        portfolio = Portfolio(
            id=str(uuid.uuid4()),
            phone=phone,
            filename="__master__",
            portfolio_data={
                "segments": {},
                "investor": {},
                "summary": {
                    "total_value": 0,
                    "total_invested": 0,
                    "total_return": 0,
                    "return_percentage": 0,
                    "scheme_count": 0,
                    "folio_count": 0
                },
                "holdings": [],
                "asset_allocation": [],
                "amc_allocation": [],
                "insights": {}
            }
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    return portfolio


def merge_portfolio_segment(master_data: Dict[str, Any], segment_data: Dict[str, Any], source: str, filename: str) -> Dict[str, Any]:
    """Merge a new segment into the master portfolio."""
    result = deepcopy(master_data)
    
    # Initialize segments dict if not exists
    if "segments" not in result:
        result["segments"] = {}
    
    # Store segment metadata
    segment_summary = segment_data.get("summary", {})
    result["segments"][source] = {
        "filename": filename,
        "uploaded_at": datetime.utcnow().isoformat(),
        "holdings_count": len(segment_data.get("holdings", [])),
        "total_value": segment_summary.get("total_value", 0),
        "source_summary": segment_summary
    }
    
    logger.info(f"Merging segment '{source}' with {len(segment_data.get('holdings', []))} holdings, value: {segment_summary.get('total_value', 0)}")
    
    # Update investor info (prefer CAS data)
    if source == "cas" or not result.get("investor", {}).get("name"):
        investor = segment_data.get("investor", {})
        if investor.get("name"):
            result["investor"] = investor
    
    # Remove old holdings from this source and add new ones
    existing_holdings = [h for h in result.get("holdings", []) 
                        if h.get("source") != source]
    
    logger.info(f"Keeping {len(existing_holdings)} holdings from other sources")
    
    new_holdings = []
    for holding in segment_data.get("holdings", []):
        h = deepcopy(holding)
        h["source"] = source
        new_holdings.append(h)
    
    logger.info(f"Adding {len(new_holdings)} new holdings from '{source}'")
    
    result["holdings"] = existing_holdings + new_holdings
    
    # Log some sample holdings values for debugging
    if new_holdings:
        sample = new_holdings[0]
        logger.info(f"Sample holding from '{source}': {sample.get('scheme_name', 'N/A')[:30]}, value: {sample.get('current_value', 0)}")
    
    # Recalculate summary and allocations
    result = recalculate_portfolio_totals(result)
    
    return result


def recalculate_portfolio_totals(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
    """Recalculate all totals and allocations from holdings."""
    holdings = portfolio_data.get("holdings", [])
    
    total_value = 0
    total_invested = 0
    asset_classes = {}
    amcs = {}
    folios = set()
    
    for h in holdings:
        value = h.get("current_value", 0) or 0
        invested = h.get("invested_amount", 0) or 0
        asset_class = h.get("asset_class", "Other")
        amc = h.get("amc", "Unknown")
        folio = h.get("folio", "")
        
        total_value += value
        total_invested += invested
        
        # Asset allocation
        if asset_class not in asset_classes:
            asset_classes[asset_class] = {"value": 0, "count": 0}
        asset_classes[asset_class]["value"] += value
        asset_classes[asset_class]["count"] += 1
        
        # AMC allocation
        if amc not in amcs:
            amcs[amc] = {"value": 0, "count": 0}
        amcs[amc]["value"] += value
        amcs[amc]["count"] += 1
        
        if folio:
            folios.add(folio)
    
    # Build asset allocation with percentages
    asset_allocation = []
    for asset_class, data in asset_classes.items():
        pct = (data["value"] / total_value * 100) if total_value > 0 else 0
        # Normalize asset class names for display
        display_name = normalize_asset_class(asset_class)
        asset_allocation.append({
            "asset_class": display_name,
            "value": round(data["value"], 2),
            "percentage": round(pct, 2),
            "scheme_count": data["count"]
        })
    asset_allocation.sort(key=lambda x: x["value"], reverse=True)
    
    # Build AMC allocation with percentages
    amc_allocation = []
    for amc, data in amcs.items():
        pct = (data["value"] / total_value * 100) if total_value > 0 else 0
        amc_allocation.append({
            "amc": amc,
            "value": round(data["value"], 2),
            "percentage": round(pct, 2),
            "scheme_count": data["count"]
        })
    amc_allocation.sort(key=lambda x: x["value"], reverse=True)
    
    total_return = total_value - total_invested
    return_pct = (total_return / total_invested * 100) if total_invested > 0 else 0
    
    portfolio_data["summary"] = {
        "total_value": round(total_value, 2),
        "total_invested": round(total_invested, 2),
        "total_return": round(total_return, 2),
        "return_percentage": round(return_pct, 2),
        "scheme_count": len(holdings),
        "folio_count": len(folios)
    }
    
    portfolio_data["asset_allocation"] = asset_allocation
    portfolio_data["amc_allocation"] = amc_allocation
    
    return portfolio_data


def normalize_asset_class(asset_class: str) -> str:
    """Normalize asset class names for consistent display."""
    mapping = {
        "equity": "Equity",
        "debt": "Debt",
        "hybrid": "Hybrid",
        "gold": "Gold",
        "other": "Mutual Funds",
        "mutual_fund": "Mutual Funds",
        "mutual_funds": "Mutual Funds",
        "us_equity": "US Equity",
        "crypto": "Crypto",
        "cash": "Cash",
    }
    return mapping.get(asset_class.lower(), asset_class)


# ==================== PORTFOLIO ENDPOINTS ====================

@app.post("/api/upload-cas", response_model=PortfolioResponse)
async def upload_cas(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    current_user: Optional[TokenData] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and parse portfolio file (CAS PDF or US Equity PDF).
    Files are aggregated into a single master portfolio per user.
    
    Supported file types:
    - NSDL CAS PDF: Indian mutual funds and equities
    - Vested/VF Securities PDF: US equity holdings
    
    Password is optional (only needed for password-protected PDFs).
    """
    filename_lower = file.filename.lower()
    is_pdf = filename_lower.endswith('.pdf')
    
    if not is_pdf:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted (CAS or Vested statements)")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Detect file type and parse
        logger.info(f"Parsing file: {file.filename}")
        
        if is_us_equity_pdf(tmp_path):
            logger.info("Detected US Equity PDF (Vested/VF Securities)")
            segment_data = parse_us_equity_pdf(tmp_path)
            source = "us_equity"
        else:
            logger.info("Detected CAS PDF")
            segment_data = parse_cas_file(tmp_path, password or "")
            source = "cas"
        
        # Log parsed data summary
        logger.info(f"Parsed {source} segment: {segment_data.get('summary', {})}")
        logger.info(f"Number of holdings: {len(segment_data.get('holdings', []))}")
        
        # Cleanup temp file
        os.unlink(tmp_path)
        
        # If authenticated, merge into master portfolio
        if current_user:
            master = get_or_create_master_portfolio(db, current_user.phone)
            master_data = master.portfolio_data or {}
            
            # Log existing data before merge
            existing_segments = list(master_data.get('segments', {}).keys())
            existing_holdings = len(master_data.get('holdings', []))
            logger.info(f"Existing portfolio - Segments: {existing_segments}, Holdings: {existing_holdings}")
            
            # Log new segment data
            new_holdings = segment_data.get('holdings', [])
            new_total = segment_data.get('summary', {}).get('total_value', 0)
            logger.info(f"New {source} segment - Holdings: {len(new_holdings)}, Value: {new_total}")
            
            # Merge new segment
            updated_data = merge_portfolio_segment(
                master_data, 
                segment_data, 
                source, 
                file.filename
            )
            
            # Generate insights
            updated_data["insights"] = generate_insights(updated_data)
            
            # Log merged data
            merged_holdings = len(updated_data.get('holdings', []))
            merged_total = updated_data.get('summary', {}).get('total_value', 0)
            logger.info(f"After merge - Holdings: {merged_holdings}, Total value: {merged_total}")
            
            # Save - assign new dict to ensure SQLAlchemy detects the change
            master.portfolio_data = dict(updated_data)
            master.uploaded_at = datetime.utcnow()
            db.commit()
            db.refresh(master)  # Refresh to get the committed data
            
            logger.info(f"Saved portfolio for user {current_user.phone}")
            logger.info(f"Final segments: {list(updated_data.get('segments', {}).keys())}")
            
            return PortfolioResponse(success=True, data=updated_data)
        else:
            # Not authenticated - just return parsed data
            segment_data["insights"] = generate_insights(segment_data)
            return PortfolioResponse(success=True, data=segment_data)
    
    except Exception as e:
        logger.error(f"Error parsing file: {str(e)}", exc_info=True)
        # Cleanup on error
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return PortfolioResponse(success=False, error=str(e))


@app.post("/api/manual-entry", response_model=PortfolioResponse)
async def add_manual_entry(
    entry: dict,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Add a manual portfolio entry."""
    try:
        master = get_or_create_master_portfolio(db, current_user.phone)
        master_data = master.portfolio_data or {}
        
        # Create holding from manual entry
        holding = {
            "scheme_name": entry.get("scheme_name"),
            "asset_class": entry.get("asset_class"),
            "units": entry.get("units", 0),
            "nav": entry.get("nav", 0),
            "current_value": entry.get("current_value", 0),
            "invested_amount": entry.get("invested_amount", 0),
            "absolute_return": entry.get("absolute_return", 0),
            "percentage_return": entry.get("percentage_return", 0),
            "amc": entry.get("amc", "Manual"),
            "isin": "",
            "folio": "",
            "valuation_date": entry.get("valuation_date", datetime.utcnow().strftime("%Y-%m-%d")),
            "source": "manual"
        }
        
        # Add to holdings
        holdings = master_data.get("holdings", [])
        holdings.append(holding)
        master_data["holdings"] = holdings
        
        # Recalculate totals
        master_data = recalculate_portfolio_totals(master_data)
        master_data["insights"] = generate_insights(master_data)
        
        # Save
        master.portfolio_data = dict(master_data)
        master.uploaded_at = datetime.utcnow()
        db.commit()
        db.refresh(master)
        
        logger.info(f"Added manual entry for user {current_user.phone}: {holding['scheme_name']}")
        
        return PortfolioResponse(success=True, data=master_data)
    except Exception as e:
        logger.error(f"Error adding manual entry: {str(e)}", exc_info=True)
        return PortfolioResponse(success=False, error=str(e))


@app.delete("/api/manual-entry/{scheme_name}")
async def delete_manual_entry(
    scheme_name: str,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a manual entry by scheme name."""
    try:
        master = get_or_create_master_portfolio(db, current_user.phone)
        master_data = master.portfolio_data or {}
        
        # Remove manual entry with matching scheme name and source
        holdings = master_data.get("holdings", [])
        original_count = len(holdings)
        master_data["holdings"] = [h for h in holdings 
                                   if not (h.get("source") == "manual" and 
                                          h.get("scheme_name") == scheme_name)]
        
        deleted_count = original_count - len(master_data["holdings"])
        
        if deleted_count == 0:
            raise HTTPException(status_code=404, detail="Manual entry not found")
        
        # Recalculate totals
        master_data = recalculate_portfolio_totals(master_data)
        master_data["insights"] = generate_insights(master_data)
        
        # Save
        master.portfolio_data = dict(master_data)
        db.commit()
        
        logger.info(f"Deleted manual entry for user {current_user.phone}: {scheme_name}")
        
        return {"success": True, "deleted": deleted_count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting manual entry: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/portfolio", response_model=PortfolioResponse)
async def get_portfolio(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get the user's aggregated portfolio."""
    master = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not master or not master.portfolio_data.get("holdings"):
        return PortfolioResponse(success=True, data=None)
    
    return PortfolioResponse(success=True, data=master.portfolio_data)


@app.get("/api/portfolio/segments")
async def get_portfolio_segments(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get list of portfolio segments (uploaded files)."""
    master = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not master:
        return {"segments": []}
    
    segments = master.portfolio_data.get("segments", {})
    result = []
    
    for source, data in segments.items():
        result.append({
            "source": source,
            "filename": data.get("filename", ""),
            "uploaded_at": data.get("uploaded_at", ""),
            "holdings_count": data.get("holdings_count", 0),
            "total_value": data.get("total_value", 0)
        })
    
    return {"segments": result}


@app.delete("/api/portfolio/segment/{source}")
async def delete_portfolio_segment(
    source: str,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a specific segment from the portfolio."""
    master = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not master:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    data = master.portfolio_data
    
    # Remove segment metadata
    if source in data.get("segments", {}):
        del data["segments"][source]
    
    # Remove holdings from this source
    data["holdings"] = [h for h in data.get("holdings", []) if h.get("source") != source]
    
    # Recalculate totals
    data = recalculate_portfolio_totals(data)
    data["insights"] = generate_insights(data)
    
    master.portfolio_data = data
    db.commit()
    
    return {"success": True, "message": f"Segment '{source}' deleted"}


@app.delete("/api/portfolio")
async def delete_portfolio(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete the entire portfolio."""
    # Delete all portfolios for this user (including old format ones)
    db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone
    ).delete()
    db.commit()
    
    logger.info(f"Deleted all portfolios for user {current_user.phone}")
    
    return {"success": True, "message": "Portfolio deleted"}


@app.post("/api/portfolio/reset")
async def reset_portfolio(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Reset portfolio - delete all data and start fresh."""
    # Delete all portfolios for this user
    deleted = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone
    ).delete()
    db.commit()
    
    logger.info(f"Reset portfolio for user {current_user.phone}, deleted {deleted} records")
    
    return {"success": True, "message": f"Portfolio reset. Deleted {deleted} records."}


# Legacy endpoint for backwards compatibility
@app.get("/api/portfolios", response_model=List[PortfolioSummary])
async def get_user_portfolios(
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get portfolio summary (legacy endpoint)."""
    master = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not master or not master.portfolio_data.get("holdings"):
        return []
    
    data = master.portfolio_data
    summary = data.get("summary", {})
    
    return [PortfolioSummary(
        id=master.id,
        filename="My Portfolio",
        uploaded_at=str(master.uploaded_at),
        total_value=summary.get("total_value", 0),
        scheme_count=summary.get("scheme_count", 0)
    )]


@app.get("/api/portfolios/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio_by_id(
    portfolio_id: str,
    current_user: TokenData = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Get portfolio by ID (legacy endpoint)."""
    master = db.query(Portfolio).filter(
        Portfolio.phone == current_user.phone,
        Portfolio.filename == "__master__"
    ).first()
    
    if not master:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return PortfolioResponse(success=True, data=master.portfolio_data)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
