from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..models.user import User, UserCreate, UserUpdate, UserRole, Token
from ..services.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_user, get_password_hash, require_role, users_db, ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint to obtain JWT token"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token with user data
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role},
        expires_delta=access_token_expires
    )

    # Return token with expiration time
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_at=datetime.utcnow() + access_token_expires
    )


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, admin_user: User = Depends(require_role(UserRole.ADMIN))):
    """Register a new user - requires admin privileges"""
    # Check if email is already registered
    if user_data.email in users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user_id = str(uuid4())
    created_at = datetime.now()
    
    # In a real application, this would be stored in a database
    users_db[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "organization": user_data.organization,
        "role": user_data.role,
        "is_active": user_data.is_active,
        "hashed_password": get_password_hash(user_data.password),
        "created_at": created_at,
        "updated_at": created_at
    }
    
    # Return new user (without sensitive data)
    return User(
        id=user_id,
        email=user_data.email,
        full_name=user_data.full_name,
        organization=user_data.organization,
        role=user_data.role,
        is_active=user_data.is_active,
        created_at=created_at,
        updated_at=created_at
    )


@router.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return current_user


@router.get("/users", response_model=List[User])
async def get_all_users(admin_user: User = Depends(require_role(UserRole.ADMIN))):
    """Get all users - requires admin privileges"""
    users = []
    for email, user_data in users_db.items():
        users.append(User(
            id=user_data["id"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            organization=user_data["organization"],
            role=user_data["role"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        ))
    return users


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin_user: User = Depends(require_role(UserRole.ADMIN))
):
    """Update user information - requires admin privileges"""
    # Find user by ID
    target_user = None
    target_email = None
    
    for email, user_data in users_db.items():
        if user_data["id"] == user_id:
            target_user = user_data
            target_email = email
            break
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user data
    if user_update.email is not None and user_update.email != target_email:
        if user_update.email in users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        # Update email key in dict
        users_db[user_update.email] = users_db.pop(target_email)
        target_email = user_update.email
        target_user["email"] = user_update.email
    
    if user_update.full_name is not None:
        target_user["full_name"] = user_update.full_name
    
    if user_update.organization is not None:
        target_user["organization"] = user_update.organization
    
    if user_update.role is not None:
        target_user["role"] = user_update.role
    
    if user_update.is_active is not None:
        target_user["is_active"] = user_update.is_active
    
    if user_update.password is not None:
        target_user["hashed_password"] = get_password_hash(user_update.password)
    
    target_user["updated_at"] = datetime.now()
    
    # Return updated user
    return User(
        id=target_user["id"],
        email=target_user["email"],
        full_name=target_user["full_name"],
        organization=target_user["organization"],
        role=target_user["role"],
        is_active=target_user["is_active"],
        created_at=target_user["created_at"],
        updated_at=target_user["updated_at"]
    ) 