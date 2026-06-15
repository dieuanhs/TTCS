from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models
from ..database import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.UserOut])
def read_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)

@router.post("/login")
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    # Tìm kiếm người dùng dựa trên tên đăng nhập
    user = db.query(models.User).filter(models.User.full_name == payload.username).first()
    if not user or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

    return {
        "status": "success",
        "full_name": user.full_name,
        "user_id": user.user_id,
        "email": user.email
    }

@router.put("/{user_id}/update-profile")
def update_profile(user_id: int, payload: schemas.UpdateProfile, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user.full_name = payload.full_name
    user.email = payload.email
    db.commit()
    return {"status": "success", "full_name": user.full_name, "email": user.email}

@router.put("/{user_id}/change-password")
def change_password(user_id: int, payload: schemas.ChangePassword, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    if user.password != payload.old_password:
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng")

    user.password = payload.new_password
    db.commit()
    return {"status": "success"}