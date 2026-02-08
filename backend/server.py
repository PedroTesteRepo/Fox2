from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'fox-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Enums
class DumpsterStatus(str, Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    IN_TRANSIT = "in_transit"

class OrderType(str, Enum):
    PLACEMENT = "placement"
    REMOVAL = "removal"
    EXCHANGE = "exchange"

class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PIX = "pix"

class TransactionType(str, Enum):
    INCOME = "income"
    EXPENSE = "expense"

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    email: EmailStr
    full_name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class ClientCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: str
    address: str
    document: str
    document_type: Literal["cpf", "cnpj"]

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: Optional[EmailStr] = None
    phone: str
    address: str
    document: str
    document_type: Literal["cpf", "cnpj"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DumpsterCreate(BaseModel):
    identifier: str
    size: str
    capacity: str
    description: Optional[str] = None

class Dumpster(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    identifier: str
    size: str
    capacity: str
    description: Optional[str] = None
    status: DumpsterStatus = DumpsterStatus.AVAILABLE
    current_location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrderCreate(BaseModel):
    client_id: str
    dumpster_id: str
    order_type: OrderType
    delivery_address: str
    rental_value: float
    payment_method: PaymentMethod
    scheduled_date: datetime
    notes: Optional[str] = None

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    client_name: str
    dumpster_id: str
    dumpster_identifier: str
    order_type: OrderType
    status: OrderStatus = OrderStatus.PENDING
    delivery_address: str
    rental_value: float
    payment_method: PaymentMethod
    scheduled_date: datetime
    completed_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccountsPayableCreate(BaseModel):
    description: str
    amount: float
    due_date: datetime
    category: str
    notes: Optional[str] = None

class AccountsPayable(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    description: str
    amount: float
    due_date: datetime
    paid_date: Optional[datetime] = None
    category: str
    is_paid: bool = False
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccountsReceivableCreate(BaseModel):
    client_id: str
    order_id: str
    amount: float
    due_date: datetime
    notes: Optional[str] = None

class AccountsReceivable(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    client_name: str
    order_id: str
    amount: float
    due_date: datetime
    received_date: Optional[datetime] = None
    is_received: bool = False
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    type: TransactionType
    description: str
    amount: float
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    category: str
    reference_id: Optional[str] = None

class DashboardStats(BaseModel):
    total_dumpsters: int
    available_dumpsters: int
    rented_dumpsters: int
    active_orders: int
    pending_orders: int
    total_revenue_month: float
    total_receivable: float
    total_payable: float
    cash_balance: float

# Auth utilities
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"email": email}, {"_id": 0, "password": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return User(**user)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

# Auth routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_dict = {
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_dict)
    
    access_token = create_access_token(data={"sub": user_data.email})
    user = User(email=user_data.email, full_name=user_data.full_name)
    return Token(access_token=access_token, user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": credentials.email})
    user_obj = User(email=user["email"], full_name=user["full_name"])
    return Token(access_token=access_token, user=user_obj)

# Client routes
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate, current_user: User = Depends(get_current_user)):
    import uuid
    client_dict = client.model_dump()
    client_dict["id"] = str(uuid.uuid4())
    client_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.clients.insert_one(client_dict)
    return Client(**client_dict)

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    clients = await db.clients.find({}, {"_id": 0}).to_list(1000)
    for c in clients:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
    return clients

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if isinstance(client.get('created_at'), str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_data: ClientCreate, current_user: User = Depends(get_current_user)):
    result = await db.clients.find_one_and_update(
        {"id": client_id},
        {"$set": client_data.model_dump()},
        return_document=True,
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Client not found")
    if isinstance(result.get('created_at'), str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    return Client(**result)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: User = Depends(get_current_user)):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Dumpster routes
@api_router.post("/dumpsters", response_model=Dumpster)
async def create_dumpster(dumpster: DumpsterCreate, current_user: User = Depends(get_current_user)):
    import uuid
    dumpster_dict = dumpster.model_dump()
    dumpster_dict["id"] = str(uuid.uuid4())
    dumpster_dict["status"] = DumpsterStatus.AVAILABLE
    dumpster_dict["current_location"] = None
    dumpster_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    await db.dumpsters.insert_one(dumpster_dict)
    return Dumpster(**dumpster_dict)

@api_router.get("/dumpsters", response_model=List[Dumpster])
async def get_dumpsters(current_user: User = Depends(get_current_user)):
    dumpsters = await db.dumpsters.find({}, {"_id": 0}).to_list(1000)
    for d in dumpsters:
        if isinstance(d.get('created_at'), str):
            d['created_at'] = datetime.fromisoformat(d['created_at'])
    return dumpsters

@api_router.get("/dumpsters/{dumpster_id}", response_model=Dumpster)
async def get_dumpster(dumpster_id: str, current_user: User = Depends(get_current_user)):
    dumpster = await db.dumpsters.find_one({"id": dumpster_id}, {"_id": 0})
    if not dumpster:
        raise HTTPException(status_code=404, detail="Dumpster not found")
    if isinstance(dumpster.get('created_at'), str):
        dumpster['created_at'] = datetime.fromisoformat(dumpster['created_at'])
    return Dumpster(**dumpster)

@api_router.put("/dumpsters/{dumpster_id}", response_model=Dumpster)
async def update_dumpster(dumpster_id: str, dumpster_data: DumpsterCreate, current_user: User = Depends(get_current_user)):
    result = await db.dumpsters.find_one_and_update(
        {"id": dumpster_id},
        {"$set": dumpster_data.model_dump()},
        return_document=True,
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dumpster not found")
    if isinstance(result.get('created_at'), str):
        result['created_at'] = datetime.fromisoformat(result['created_at'])
    return Dumpster(**result)

@api_router.patch("/dumpsters/{dumpster_id}/status")
async def update_dumpster_status(dumpster_id: str, status: DumpsterStatus, location: Optional[str] = None, current_user: User = Depends(get_current_user)):
    update_data = {"status": status}
    if location:
        update_data["current_location"] = location
    
    result = await db.dumpsters.find_one_and_update(
        {"id": dumpster_id},
        {"$set": update_data},
        return_document=True,
        projection={"_id": 0}
    )
    if not result:
        raise HTTPException(status_code=404, detail="Dumpster not found")
    return {"message": "Status updated successfully"}

@api_router.delete("/dumpsters/{dumpster_id}")
async def delete_dumpster(dumpster_id: str, current_user: User = Depends(get_current_user)):
    result = await db.dumpsters.delete_one({"id": dumpster_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Dumpster not found")
    return {"message": "Dumpster deleted successfully"}

# Order routes
@api_router.post("/orders", response_model=Order)
async def create_order(order: OrderCreate, current_user: User = Depends(get_current_user)):
    import uuid
    
    # Get client and dumpster info
    client = await db.clients.find_one({"id": order.client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    dumpster = await db.dumpsters.find_one({"id": order.dumpster_id}, {"_id": 0})
    if not dumpster:
        raise HTTPException(status_code=404, detail="Dumpster not found")
    
    if dumpster["status"] != DumpsterStatus.AVAILABLE and order.order_type == OrderType.PLACEMENT:
        raise HTTPException(status_code=400, detail="Dumpster not available")
    
    order_dict = order.model_dump()
    order_dict["id"] = str(uuid.uuid4())
    order_dict["client_name"] = client["name"]
    order_dict["dumpster_identifier"] = dumpster["identifier"]
    order_dict["status"] = OrderStatus.PENDING
    order_dict["completed_date"] = None
    order_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    order_dict["scheduled_date"] = order.scheduled_date.isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Update dumpster status
    if order.order_type == OrderType.PLACEMENT:
        await db.dumpsters.update_one(
            {"id": order.dumpster_id},
            {"$set": {"status": DumpsterStatus.RENTED, "current_location": order.delivery_address}}
        )
    
    # Create accounts receivable
    receivable_dict = {
        "id": str(uuid.uuid4()),
        "client_id": order.client_id,
        "client_name": client["name"],
        "order_id": order_dict["id"],
        "amount": order.rental_value,
        "due_date": order.scheduled_date.isoformat(),
        "received_date": None,
        "is_received": False,
        "notes": f"Pedido {order.order_type.value} - {dumpster['identifier']}",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounts_receivable.insert_one(receivable_dict)
    
    order_dict['scheduled_date'] = datetime.fromisoformat(order_dict['scheduled_date'])
    order_dict['created_at'] = datetime.fromisoformat(order_dict['created_at'])
    return Order(**order_dict)

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({}, {"_id": 0}).to_list(1000)
    for o in orders:
        if isinstance(o.get('created_at'), str):
            o['created_at'] = datetime.fromisoformat(o['created_at'])
        if isinstance(o.get('scheduled_date'), str):
            o['scheduled_date'] = datetime.fromisoformat(o['scheduled_date'])
        if o.get('completed_date') and isinstance(o['completed_date'], str):
            o['completed_date'] = datetime.fromisoformat(o['completed_date'])
    return orders

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user: User = Depends(get_current_user)):
    order = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if isinstance(order.get('created_at'), str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order.get('scheduled_date'), str):
        order['scheduled_date'] = datetime.fromisoformat(order['scheduled_date'])
    if order.get('completed_date') and isinstance(order['completed_date'], str):
        order['completed_date'] = datetime.fromisoformat(order['completed_date'])
    return Order(**order)

@api_router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: User = Depends(get_current_user)):
    update_data = {"status": status}
    if status == OrderStatus.COMPLETED:
        update_data["completed_date"] = datetime.now(timezone.utc).isoformat()
    
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": update_data}
    )
    
    # Update dumpster status if completed
    if status == OrderStatus.COMPLETED and order["order_type"] == "removal":
        await db.dumpsters.update_one(
            {"id": order["dumpster_id"]},
            {"$set": {"status": DumpsterStatus.AVAILABLE, "current_location": None}}
        )
    
    return {"message": "Order status updated successfully"}

@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str, current_user: User = Depends(get_current_user)):
    result = await db.orders.delete_one({"id": order_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order deleted successfully"}

# Accounts Payable routes
@api_router.post("/finance/accounts-payable", response_model=AccountsPayable)
async def create_accounts_payable(account: AccountsPayableCreate, current_user: User = Depends(get_current_user)):
    import uuid
    account_dict = account.model_dump()
    account_dict["id"] = str(uuid.uuid4())
    account_dict["is_paid"] = False
    account_dict["paid_date"] = None
    account_dict["created_at"] = datetime.now(timezone.utc).isoformat()
    account_dict["due_date"] = account.due_date.isoformat()
    await db.accounts_payable.insert_one(account_dict)
    
    account_dict['due_date'] = datetime.fromisoformat(account_dict['due_date'])
    account_dict['created_at'] = datetime.fromisoformat(account_dict['created_at'])
    return AccountsPayable(**account_dict)

@api_router.get("/finance/accounts-payable", response_model=List[AccountsPayable])
async def get_accounts_payable(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts_payable.find({}, {"_id": 0}).to_list(1000)
    for a in accounts:
        if isinstance(a.get('created_at'), str):
            a['created_at'] = datetime.fromisoformat(a['created_at'])
        if isinstance(a.get('due_date'), str):
            a['due_date'] = datetime.fromisoformat(a['due_date'])
        if a.get('paid_date') and isinstance(a['paid_date'], str):
            a['paid_date'] = datetime.fromisoformat(a['paid_date'])
    return accounts

@api_router.patch("/finance/accounts-payable/{account_id}/pay")
async def pay_account(account_id: str, current_user: User = Depends(get_current_user)):
    result = await db.accounts_payable.find_one_and_update(
        {"id": account_id},
        {"$set": {"is_paid": True, "paid_date": datetime.now(timezone.utc).isoformat()}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account marked as paid"}

@api_router.delete("/finance/accounts-payable/{account_id}")
async def delete_accounts_payable(account_id: str, current_user: User = Depends(get_current_user)):
    result = await db.accounts_payable.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}

# Accounts Receivable routes
@api_router.get("/finance/accounts-receivable", response_model=List[AccountsReceivable])
async def get_accounts_receivable(current_user: User = Depends(get_current_user)):
    accounts = await db.accounts_receivable.find({}, {"_id": 0}).to_list(1000)
    for a in accounts:
        if isinstance(a.get('created_at'), str):
            a['created_at'] = datetime.fromisoformat(a['created_at'])
        if isinstance(a.get('due_date'), str):
            a['due_date'] = datetime.fromisoformat(a['due_date'])
        if a.get('received_date') and isinstance(a['received_date'], str):
            a['received_date'] = datetime.fromisoformat(a['received_date'])
    return accounts

@api_router.patch("/finance/accounts-receivable/{account_id}/receive")
async def receive_payment(account_id: str, current_user: User = Depends(get_current_user)):
    result = await db.accounts_receivable.find_one_and_update(
        {"id": account_id},
        {"$set": {"is_received": True, "received_date": datetime.now(timezone.utc).isoformat()}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Payment received"}

@api_router.delete("/finance/accounts-receivable/{account_id}")
async def delete_accounts_receivable(account_id: str, current_user: User = Depends(get_current_user)):
    result = await db.accounts_receivable.delete_one({"id": account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}

# Dashboard stats
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    # Count dumpsters by status
    all_dumpsters = await db.dumpsters.find({}, {"_id": 0}).to_list(1000)
    total_dumpsters = len(all_dumpsters)
    available_dumpsters = len([d for d in all_dumpsters if d.get("status") == "available"])
    rented_dumpsters = len([d for d in all_dumpsters if d.get("status") == "rented"])
    
    # Count orders
    all_orders = await db.orders.find({}, {"_id": 0}).to_list(1000)
    active_orders = len([o for o in all_orders if o.get("status") in ["pending", "in_progress"]])
    pending_orders = len([o for o in all_orders if o.get("status") == "pending"])
    
    # Calculate revenue for current month
    now = datetime.now(timezone.utc)
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_orders = [o for o in all_orders if isinstance(o.get('created_at'), str) and 
                    datetime.fromisoformat(o['created_at']) >= start_of_month]
    total_revenue_month = sum(o.get("rental_value", 0) for o in month_orders)
    
    # Calculate receivables and payables
    all_receivables = await db.accounts_receivable.find({}, {"_id": 0}).to_list(1000)
    total_receivable = sum(a.get("amount", 0) for a in all_receivables if not a.get("is_received", False))
    
    all_payables = await db.accounts_payable.find({}, {"_id": 0}).to_list(1000)
    total_payable = sum(a.get("amount", 0) for a in all_payables if not a.get("is_paid", False))
    
    # Calculate cash balance (simplified)
    received = sum(a.get("amount", 0) for a in all_receivables if a.get("is_received", False))
    paid = sum(a.get("amount", 0) for a in all_payables if a.get("is_paid", False))
    cash_balance = received - paid
    
    return DashboardStats(
        total_dumpsters=total_dumpsters,
        available_dumpsters=available_dumpsters,
        rented_dumpsters=rented_dumpsters,
        active_orders=active_orders,
        pending_orders=pending_orders,
        total_revenue_month=total_revenue_month,
        total_receivable=total_receivable,
        total_payable=total_payable,
        cash_balance=cash_balance
    )

# Client order history
@api_router.get("/clients/{client_id}/orders", response_model=List[Order])
async def get_client_orders(client_id: str, current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"client_id": client_id}, {"_id": 0}).to_list(1000)
    for o in orders:
        if isinstance(o.get('created_at'), str):
            o['created_at'] = datetime.fromisoformat(o['created_at'])
        if isinstance(o.get('scheduled_date'), str):
            o['scheduled_date'] = datetime.fromisoformat(o['scheduled_date'])
        if o.get('completed_date') and isinstance(o['completed_date'], str):
            o['completed_date'] = datetime.fromisoformat(o['completed_date'])
    return orders

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()