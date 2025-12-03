"""
Authentication module with OTP verification and JWT tokens.
Supports both Supabase Auth (production) and demo mode (local dev).
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
import random
import string

from app.config import settings

logger = logging.getLogger(__name__)

# In-memory OTP storage (for demo mode and fallback)
# In production with Supabase, their Auth handles OTP
otp_store: Dict[str, dict] = {}

security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    phone: str
    supabase_uid: Optional[str] = None


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str


class Token(BaseModel):
    access_token: str
    token_type: str
    phone: str


def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))


def send_otp(phone: str) -> dict:
    """
    Send OTP to phone number.
    - In demo mode: Returns hardcoded OTP for test number
    - In production: Would use Supabase Auth or SMS provider
    """
    # Demo mode - use hardcoded credentials
    if settings.DEMO_MODE:
        if phone == settings.DEMO_PHONE:
            logger.info(f"[DEMO] OTP for {phone}: {settings.DEMO_OTP}")
            return {"success": True, "message": "OTP sent successfully", "demo": True}
        
        # In demo mode, also allow any phone with generated OTP
        otp = generate_otp()
        otp_store[phone] = {
            "otp": otp,
            "created_at": datetime.utcnow(),
            "attempts": 0
        }
        logger.info(f"[DEMO] Generated OTP for {phone}: {otp}")
        return {"success": True, "message": f"OTP sent (demo mode: {otp})", "demo": True, "otp": otp}
    
    # Production mode - generate and store OTP
    # In a real app, you'd send this via SMS (Twilio, etc.)
    otp = generate_otp()
    otp_store[phone] = {
        "otp": otp,
        "created_at": datetime.utcnow(),
        "attempts": 0
    }
    
    # TODO: Integrate with SMS provider (Twilio, MSG91, etc.)
    logger.info(f"OTP generated for {phone} (SMS integration needed)")
    
    return {"success": True, "message": "OTP sent successfully"}


def verify_otp(phone: str, otp: str) -> bool:
    """Verify OTP for a phone number."""
    # Demo mode - check hardcoded credentials
    if settings.DEMO_MODE and phone == settings.DEMO_PHONE:
        return otp == settings.DEMO_OTP
    
    # Check stored OTP
    stored = otp_store.get(phone)
    if not stored:
        return False
    
    # Check expiry (10 minutes)
    if datetime.utcnow() - stored["created_at"] > timedelta(minutes=10):
        del otp_store[phone]
        return False
    
    # Check attempts (max 3)
    if stored["attempts"] >= 3:
        del otp_store[phone]
        return False
    
    stored["attempts"] += 1
    
    if stored["otp"] == otp:
        del otp_store[phone]  # Clear after successful verification
        return True
    
    return False


def create_access_token(phone: str, supabase_uid: Optional[str] = None) -> str:
    """Create JWT access token for authenticated user."""
    expire = datetime.utcnow() + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": phone,
        "exp": expire
    }
    if supabase_uid:
        to_encode["supabase_uid"] = supabase_uid
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            return None
        return TokenData(
            phone=phone,
            supabase_uid=payload.get("supabase_uid")
        )
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[TokenData]:
    """
    Dependency to get current authenticated user from JWT token.
    Returns None if not authenticated (for optional auth).
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    token_data = decode_token(token)
    return token_data


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency that requires authentication.
    Raises 401 if not authenticated.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    token_data = decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data
