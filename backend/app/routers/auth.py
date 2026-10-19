"""认证接口：注册、登录、用户信息。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import (
    LoginIn, ProfileUpdateIn, RefreshIn, RegisterIn, TokenOut, UserOut,
)
from app.security import (
    create_refresh_token, create_token, decode_refresh_token,
    hash_password, verify_password,
)

router = APIRouter()


@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.username == data.username))
    if exists:
        raise HTTPException(400, "用户名已被注册")
    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname or data.username,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenOut(
        access_token=create_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(400, "用户名或密码不正确")
    return TokenOut(
        access_token=create_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenOut)
def refresh(data: RefreshIn, db: Session = Depends(get_db)):
    """用刷新令牌换取新的访问令牌（刷新令牌轮换）。"""
    user_id = decode_refresh_token(data.refresh_token)
    if user_id is None:
        raise HTTPException(401, "刷新令牌无效或已过期，请重新登录")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(401, "用户不存在，请重新登录")
    return TokenOut(
        access_token=create_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
def update_me(data: ProfileUpdateIn, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    if data.nickname:
        user.nickname = data.nickname
    if data.new_password:
        if len(data.new_password) < 6:
            raise HTTPException(400, "新密码长度不得少于 6 位")
        if not verify_password(data.old_password, user.password_hash):
            raise HTTPException(400, "原密码不正确")
        user.password_hash = hash_password(data.new_password)
    db.commit()
    db.refresh(user)
    return UserOut.model_validate(user)
