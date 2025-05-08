from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
import datetime
import motor.motor_asyncio
from bson import ObjectId

# ----- Cấu hình ứng dụng -----
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Cho phép từ tất cả domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Kết nối MongoDB -----
MONGO_URL = "mongodb://admin:password@mongo:27017"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.nihongocast
users_collection = db.user

# ----- Cấu hình bảo mật -----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "mysecretkey"  # Nên lưu ở biến môi trường thực tế

# ----- Pydantic Models -----
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ----- Hàm tiện ích -----
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# ----- API đăng ký -----
@app.post("/register")
async def register(user: UserRegister):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    user_doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "createdAt": datetime.datetime.now(datetime.timezone.utc)
    }

    await users_collection.insert_one(user_doc)
    return {"username": user.username,
        "email": user.email}

# ----- API đăng nhập -----
from bson import ObjectId  # Thêm import này để xử lý ObjectId

@app.post("/login")
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    expiration = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    token = jwt.encode(
        {
            "sub": str(db_user["_id"]),  # dùng ID làm định danh
            "exp": expiration
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return {
        "user": {
            "id": str(db_user["_id"]),
            "username": db_user["username"],
            "email": db_user["email"]
        },
        "access_token": token,
        "token_type": "bearer"
    }
