from fastapi import APIRouter, Depends, HTTPException, FastAPI
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, models # Dấu .. để quay ngược ra thư mục cha lấy crud/schemas
from ..database import get_db

# Khởi tạo Router
router = APIRouter(
    prefix="/users", # Tất cả các đường dẫn trong này sẽ bắt đầu bằng /users
    tags=["users"]   # Gom nhóm lại trong trang /docs cho dễ nhìn
)
@router.post("/", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)
@router.get("/", response_model=List[schemas.UserOut])
def read_users(db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    return users

@router.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    # Tìm user theo full_name (tên đăng nhập)
    user = db.query(models.User).filter(models.User.full_name == payload.get("username")).first()

    # Kiểm tra xem có user đó không và mật khẩu có khớp không
    if not user or user.password != payload.get("password"):
        raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

    return {"status": "success", "full_name": user.full_name}