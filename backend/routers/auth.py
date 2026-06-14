import os
import httpx
import jwt
from datetime import datetime, timedelta, UTC
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecret")
JWT_ALGORITHM = "HS256"

def create_jwt_token(user_id: str) -> str:
    expiration = datetime.now(UTC) + timedelta(days=7)
    return jwt.encode({"sub": user_id, "exp": expiration}, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request, session: AsyncSession = Depends(get_db)) -> User | None:
    token = request.cookies.get("auth_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    except jwt.PyJWTError:
        return None

@router.get("/github/login")
async def github_login():
    if not GITHUB_CLIENT_ID:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID is not configured.")
    redirect_uri = "http://localhost:8000/api/v1/auth/github/callback"
    github_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(github_url)

@router.get("/github/callback")
async def github_callback(code: str, response: Response, session: AsyncSession = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="No code provided")
    
    # 1. Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            }
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Could not retrieve access token")

        # 2. Get user info
        user_response = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_data = user_response.json()
        github_id = str(user_data.get("id"))
        username = user_data.get("login")
        avatar_url = user_data.get("avatar_url")
        
        # 3. Create or update user
        result = await session.execute(select(User).where(User.github_id == github_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                github_id=github_id,
                username=username,
                avatar_url=avatar_url,
                access_token=access_token
            )
            session.add(user)
        else:
            user.username = username
            user.avatar_url = avatar_url
            user.access_token = access_token
            
        await session.commit()
        
        # 4. Issue JWT and redirect to frontend
        jwt_token = create_jwt_token(user.id)
        
        # We redirect back to the frontend with the cookie set
        redirect_url = "http://localhost:5173/projects"
        redirect_response = RedirectResponse(url=redirect_url)
        redirect_response.set_cookie(
            key="auth_token", 
            value=jwt_token, 
            httponly=True, 
            samesite="lax",
            max_age=7 * 24 * 3600
        )
        return redirect_response

@router.get("/me")
async def get_me(user: User | None = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user.id,
        "username": user.username,
        "avatar_url": user.avatar_url
    }
