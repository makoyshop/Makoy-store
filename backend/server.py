from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import shutil
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    username: str
    password_hash: str
    is_admin: bool = False
    wallet_balance: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    is_admin: bool = False

class UserLogin(BaseModel):
    email: str
    password: str

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    image_url: str
    category: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    image_url: str
    category: str

class TopUpRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    amount: float
    receipt_data: str  # base64 encoded receipt image
    status: str = "pending"  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None

class TopUpCreate(BaseModel):
    amount: float
    receipt_data: str

class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    product_id: str
    product_name: str
    amount: float
    created_at: datetime = Field(default_factory=datetime.utcnow)

class SupportTicket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    subject: str
    message: str
    status: str = "open"  # open, closed, in_progress
    created_at: datetime = Field(default_factory=datetime.utcnow)
    responses: List[dict] = []

class TicketCreate(BaseModel):
    subject: str
    message: str

class BlogPost(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    author_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_published: bool = True

class BlogPostCreate(BaseModel):
    title: str
    content: str

# Helper functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        user = await db.users.find_one({"email": email})
        if user is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_admin_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Auth endpoints
@api_router.post("/register")
async def register(user: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    user_data = user.dict()
    user_data["password_hash"] = hash_password(user_data.pop("password"))
    user_obj = User(**user_data)
    
    await db.users.insert_one(user_obj.dict())
    
    # Create token
    access_token = create_access_token(data={"sub": user_obj.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_obj.id,
            "email": user_obj.email,
            "username": user_obj.username,
            "is_admin": user_obj.is_admin,
            "wallet_balance": user_obj.wallet_balance
        }
    }

@api_router.post("/login")
async def login(user: UserLogin):
    # Find user
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "email": db_user["email"],
            "username": db_user["username"],
            "is_admin": db_user["is_admin"],
            "wallet_balance": db_user["wallet_balance"]
        }
    }

@api_router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "wallet_balance": current_user.wallet_balance
    }

# Product endpoints
@api_router.get("/products")
async def get_products():
    products = await db.products.find({"is_active": True}).to_list(100)
    return [Product(**product) for product in products]

@api_router.post("/products")
async def create_product(product: ProductCreate, admin_user: User = Depends(get_admin_user)):
    product_obj = Product(**product.dict())
    await db.products.insert_one(product_obj.dict())
    return product_obj

@api_router.get("/products/{product_id}")
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

# Wallet endpoints
@api_router.post("/topup")
async def request_topup(topup: TopUpCreate, current_user: User = Depends(get_current_user)):
    topup_obj = TopUpRequest(user_id=current_user.id, **topup.dict())
    await db.topup_requests.insert_one(topup_obj.dict())
    return {"message": "Top-up request submitted successfully", "request_id": topup_obj.id}

@api_router.get("/topup-requests")
async def get_user_topup_requests(current_user: User = Depends(get_current_user)):
    requests = await db.topup_requests.find({"user_id": current_user.id}).to_list(100)
    return [TopUpRequest(**req) for req in requests]

@api_router.get("/admin/topup-requests")
async def get_all_topup_requests(admin_user: User = Depends(get_admin_user)):
    requests = await db.topup_requests.find().to_list(100)
    return [TopUpRequest(**req) for req in requests]

@api_router.post("/admin/topup-requests/{request_id}/approve")
async def approve_topup(request_id: str, admin_notes: Optional[str] = None, admin_user: User = Depends(get_admin_user)):
    # Get the request
    request = await db.topup_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Update user wallet balance
    await db.users.update_one(
        {"id": request["user_id"]},
        {"$inc": {"wallet_balance": request["amount"]}}
    )
    
    # Update request status
    await db.topup_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "approved",
                "processed_at": datetime.utcnow(),
                "admin_notes": admin_notes
            }
        }
    )
    
    return {"message": "Top-up approved successfully"}

@api_router.post("/admin/topup-requests/{request_id}/reject")
async def reject_topup(request_id: str, admin_notes: str = "", admin_user: User = Depends(get_admin_user)):
    request = await db.topup_requests.find_one({"id": request_id})
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Update request status
    await db.topup_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": "rejected",
                "processed_at": datetime.utcnow(),
                "admin_notes": admin_notes
            }
        }
    )
    
    return {"message": "Top-up rejected"}

# Purchase endpoints
@api_router.post("/purchase/{product_id}")
async def purchase_product(product_id: str, current_user: User = Depends(get_current_user)):
    # Get product
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has enough balance
    if current_user.wallet_balance < product["price"]:
        raise HTTPException(status_code=400, detail="Insufficient wallet balance")
    
    # Deduct from wallet
    await db.users.update_one(
        {"id": current_user.id},
        {"$inc": {"wallet_balance": -product["price"]}}
    )
    
    # Create purchase record
    purchase = Purchase(
        user_id=current_user.id,
        product_id=product_id,
        product_name=product["name"],
        amount=product["price"]
    )
    await db.purchases.insert_one(purchase.dict())
    
    return {"message": "Purchase successful", "purchase_id": purchase.id}

@api_router.get("/purchases")
async def get_user_purchases(current_user: User = Depends(get_current_user)):
    purchases = await db.purchases.find({"user_id": current_user.id}).to_list(100)
    return [Purchase(**purchase) for purchase in purchases]

# Support ticket endpoints
@api_router.post("/tickets")
async def create_ticket(ticket: TicketCreate, current_user: User = Depends(get_current_user)):
    ticket_obj = SupportTicket(user_id=current_user.id, **ticket.dict())
    await db.tickets.insert_one(ticket_obj.dict())
    return ticket_obj

@api_router.get("/tickets")
async def get_user_tickets(current_user: User = Depends(get_current_user)):
    tickets = await db.tickets.find({"user_id": current_user.id}).to_list(100)
    return [SupportTicket(**ticket) for ticket in tickets]

# Blog endpoints
@api_router.get("/blog")
async def get_blog_posts():
    posts = await db.blog_posts.find({"is_published": True}).to_list(100)
    return [BlogPost(**post) for post in posts]

@api_router.post("/blog")
async def create_blog_post(post: BlogPostCreate, admin_user: User = Depends(get_admin_user)):
    post_obj = BlogPost(author_id=admin_user.id, **post.dict())
    await db.blog_posts.insert_one(post_obj.dict())
    return post_obj

@api_router.get("/blog/{post_id}")
async def get_blog_post(post_id: str):
    post = await db.blog_posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return BlogPost(**post)

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()