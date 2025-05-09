import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer

from ..models.user import User, UserInDB, TokenData, UserRole

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "temporary_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token validation
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Mock database for demonstration - replace with actual database in production
users_db = {
    "admin@example.com": {
        "id": "user1",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "organization": "Hegel Organization",
        "role": UserRole.ADMIN,
        "is_active": True,
        "hashed_password": pwd_context.hash("admin123"),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    },
    "researcher@example.com": {
        "id": "user2",
        "email": "researcher@example.com",
        "full_name": "Research User",
        "organization": "Research Lab",
        "role": UserRole.RESEARCHER,
        "is_active": True,
        "hashed_password": pwd_context.hash("research123"),
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)


def get_user(email: str) -> Optional[UserInDB]:
    """Get a user by email (from mock database)"""
    if email in users_db:
        user_dict = users_db[email]
        return UserInDB(**user_dict)
    return None


def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password"""
    user = get_user(email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Return User model (without sensitive data)
    return User(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization=user.organization,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Validate token and return current user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        role: str = payload.get("role", UserRole.RESEARCHER)
        exp: datetime = datetime.fromtimestamp(payload.get("exp"))
        
        if user_id is None:
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, role=role, exp=exp)
    except InvalidTokenError:
        raise credentials_exception
    
    # In a real application, fetch user from database using user_id
    for user_data in users_db.values():
        if user_data["id"] == token_data.user_id:
            return User(
                id=user_data["id"],
                email=user_data["email"],
                full_name=user_data["full_name"],
                organization=user_data["organization"],
                role=user_data["role"],
                is_active=user_data["is_active"],
                created_at=user_data["created_at"],
                updated_at=user_data["updated_at"]
            )
    
    raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Check if the current user is active"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """Dependency to check if the user has the required role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role and current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role"
            )
        return current_user
    
    return role_checker 