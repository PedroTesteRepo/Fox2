from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import aiomysql
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from enum import Enum
import uuid
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MySQL connection pool
db_pool = None

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
    phone: str  # Mantido para compatibilidade, mas deprecated
    address: str  # Mantido para compatibilidade, mas deprecated
    document: str
    document_type: Literal["cpf", "cnpj"]

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: Optional[EmailStr] = None
    phone: str  # Deprecated - usar client_phones
    address: str  # Deprecated - usar client_addresses
    document: str
    document_type: Literal["cpf", "cnpj"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# New models for multiple phones and addresses
class ClientPhoneCreate(BaseModel):
    phone: str
    phone_type: str = "Celular"
    is_primary: bool = False

class ClientPhone(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    phone: str
    phone_type: str
    is_primary: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientAddressCreate(BaseModel):
    address_type: str = "Residencial"
    cep: str
    street: str
    number: str
    complement: Optional[str] = None
    neighborhood: str
    city: str
    state: str
    is_primary: bool = False

class ClientAddress(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    client_id: str
    address_type: str
    cep: str
    street: str
    number: str
    complement: Optional[str] = None
    neighborhood: str
    city: str
    state: str
    is_primary: bool
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientWithDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    email: Optional[EmailStr] = None
    document: str
    document_type: Literal["cpf", "cnpj"]
    created_at: datetime
    phones: List[ClientPhone] = []
    addresses: List[ClientAddress] = []

class ViaCEPResponse(BaseModel):
    cep: str
    logradouro: str
    complemento: str
    bairro: str
    localidade: str
    uf: str
    erro: Optional[bool] = None

class ClientFinancialSummary(BaseModel):
    client: Client
    total_orders: int
    pending_orders: int
    completed_orders: int
    total_receivable: float
    total_received: float
    pending_amount: float
    orders: List[Order]
    accounts_receivable: List[AccountsReceivable]

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
    delivery_address: str  # Texto livre (fallback)
    delivery_address_id: Optional[str] = None  # ID do endereço do cliente
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

# Database connection
async def get_db():
    global db_pool
    if db_pool is None:
        db_pool = await aiomysql.create_pool(
            host=os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('MYSQL_PORT', 3306)),
            user=os.environ.get('MYSQL_USER', 'root'),
            password=os.environ.get('MYSQL_PASSWORD', ''),
            db=os.environ.get('MYSQL_DB', 'fox_db'),
            charset='utf8mb4',
            autocommit=True,
            minsize=1,
            maxsize=10
        )
    return db_pool

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
        
        pool = await get_db()
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute("SELECT email, full_name, created_at FROM users WHERE email = %s", (email,))
                user = await cursor.fetchone()
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
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT email FROM users WHERE email = %s", (user_data.email,))
            existing = await cursor.fetchone()
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            
            hashed_pw = hash_password(user_data.password)
            await cursor.execute(
                "INSERT INTO users (email, password, full_name, created_at) VALUES (%s, %s, %s, %s)",
                (user_data.email, hashed_pw, user_data.full_name, datetime.now(timezone.utc))
            )
            
            access_token = create_access_token(data={"sub": user_data.email})
            user = User(email=user_data.email, full_name=user_data.full_name)
            return Token(access_token=access_token, user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM users WHERE email = %s", (credentials.email,))
            user = await cursor.fetchone()
            if not user or not verify_password(credentials.password, user["password"]):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            access_token = create_access_token(data={"sub": credentials.email})
            user_obj = User(email=user["email"], full_name=user["full_name"])
            return Token(access_token=access_token, user=user_obj)

# Client routes
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    client_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """INSERT INTO clients (id, name, email, phone, address, document, document_type, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (client_id, client.name, client.email, client.phone, client.address, 
                 client.document, client.document_type, datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            result = await cursor.fetchone()
            return Client(**result)

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM clients ORDER BY created_at DESC")
            clients = await cursor.fetchall()
            return [Client(**c) for c in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            client = await cursor.fetchone()
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            return Client(**client)

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_data: ClientCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """UPDATE clients SET name = %s, email = %s, phone = %s, 
                   address = %s, document = %s, document_type = %s WHERE id = %s""",
                (client_data.name, client_data.email, client_data.phone, 
                 client_data.address, client_data.document, client_data.document_type, client_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Client not found")
            
            await cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            result = await cursor.fetchone()
            return Client(**result)

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Client not found")
            return {"message": "Client deleted successfully"}

# Dumpster routes
@api_router.post("/dumpsters", response_model=Dumpster)
async def create_dumpster(dumpster: DumpsterCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    dumpster_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """INSERT INTO dumpsters (id, identifier, size, capacity, description, status, current_location, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (dumpster_id, dumpster.identifier, dumpster.size, dumpster.capacity,
                 dumpster.description, DumpsterStatus.AVAILABLE, None, datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM dumpsters WHERE id = %s", (dumpster_id,))
            result = await cursor.fetchone()
            return Dumpster(**result)

@api_router.get("/dumpsters", response_model=List[Dumpster])
async def get_dumpsters(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM dumpsters ORDER BY created_at DESC")
            dumpsters = await cursor.fetchall()
            return [Dumpster(**d) for d in dumpsters]

@api_router.get("/dumpsters/{dumpster_id}", response_model=Dumpster)
async def get_dumpster(dumpster_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM dumpsters WHERE id = %s", (dumpster_id,))
            dumpster = await cursor.fetchone()
            if not dumpster:
                raise HTTPException(status_code=404, detail="Dumpster not found")
            return Dumpster(**dumpster)

@api_router.put("/dumpsters/{dumpster_id}", response_model=Dumpster)
async def update_dumpster(dumpster_id: str, dumpster_data: DumpsterCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """UPDATE dumpsters SET identifier = %s, size = %s, capacity = %s, 
                   description = %s WHERE id = %s""",
                (dumpster_data.identifier, dumpster_data.size, dumpster_data.capacity,
                 dumpster_data.description, dumpster_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Dumpster not found")
            
            await cursor.execute("SELECT * FROM dumpsters WHERE id = %s", (dumpster_id,))
            result = await cursor.fetchone()
            return Dumpster(**result)

@api_router.patch("/dumpsters/{dumpster_id}/status")
async def update_dumpster_status(dumpster_id: str, status: DumpsterStatus, location: Optional[str] = None, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            if location:
                await cursor.execute(
                    "UPDATE dumpsters SET status = %s, current_location = %s WHERE id = %s",
                    (status, location, dumpster_id)
                )
            else:
                await cursor.execute(
                    "UPDATE dumpsters SET status = %s WHERE id = %s",
                    (status, dumpster_id)
                )
            
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Dumpster not found")
            return {"message": "Status updated successfully"}

@api_router.delete("/dumpsters/{dumpster_id}")
async def delete_dumpster(dumpster_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("DELETE FROM dumpsters WHERE id = %s", (dumpster_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Dumpster not found")
            return {"message": "Dumpster deleted successfully"}

# Order routes
@api_router.post("/orders", response_model=Order)
async def create_order(order: OrderCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    order_id = str(uuid.uuid4())
    
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Get client
            await cursor.execute("SELECT * FROM clients WHERE id = %s", (order.client_id,))
            client = await cursor.fetchone()
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Get dumpster
            await cursor.execute("SELECT * FROM dumpsters WHERE id = %s", (order.dumpster_id,))
            dumpster = await cursor.fetchone()
            if not dumpster:
                raise HTTPException(status_code=404, detail="Dumpster not found")
            
            if dumpster["status"] != DumpsterStatus.AVAILABLE and order.order_type == OrderType.PLACEMENT:
                raise HTTPException(status_code=400, detail="Dumpster not available")
            
            # Create order
            await cursor.execute(
                """INSERT INTO orders (id, client_id, client_name, dumpster_id, dumpster_identifier,
                   order_type, status, delivery_address, rental_value, payment_method, 
                   scheduled_date, completed_date, notes, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (order_id, order.client_id, client["name"], order.dumpster_id, dumpster["identifier"],
                 order.order_type, OrderStatus.PENDING, order.delivery_address, order.rental_value,
                 order.payment_method, order.scheduled_date, None, order.notes, datetime.now(timezone.utc))
            )
            
            # Update dumpster status
            if order.order_type == OrderType.PLACEMENT:
                await cursor.execute(
                    "UPDATE dumpsters SET status = %s, current_location = %s WHERE id = %s",
                    (DumpsterStatus.RENTED, order.delivery_address, order.dumpster_id)
                )
            
            # Create accounts receivable
            receivable_id = str(uuid.uuid4())
            await cursor.execute(
                """INSERT INTO accounts_receivable (id, client_id, client_name, order_id, amount,
                   due_date, received_date, is_received, notes, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (receivable_id, order.client_id, client["name"], order_id, order.rental_value,
                 order.scheduled_date, None, False, 
                 f"Pedido {order.order_type.value} - {dumpster['identifier']}", 
                 datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            result = await cursor.fetchone()
            return Order(**result)

@api_router.get("/orders", response_model=List[Order])
async def get_orders(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
            orders = await cursor.fetchall()
            return [Order(**o) for o in orders]

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = await cursor.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            return Order(**order)

@api_router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Get order
            await cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
            order = await cursor.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="Order not found")
            
            # Update order status
            if status == OrderStatus.COMPLETED:
                await cursor.execute(
                    "UPDATE orders SET status = %s, completed_date = %s WHERE id = %s",
                    (status, datetime.now(timezone.utc), order_id)
                )
            else:
                await cursor.execute(
                    "UPDATE orders SET status = %s WHERE id = %s",
                    (status, order_id)
                )
            
            # Update dumpster status if completed
            if status == OrderStatus.COMPLETED and order["order_type"] == "removal":
                await cursor.execute(
                    "UPDATE dumpsters SET status = %s, current_location = %s WHERE id = %s",
                    (DumpsterStatus.AVAILABLE, None, order["dumpster_id"])
                )
            
            return {"message": "Order status updated successfully"}

@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Order not found")
            return {"message": "Order deleted successfully"}

# Accounts Payable routes
@api_router.post("/finance/accounts-payable", response_model=AccountsPayable)
async def create_accounts_payable(account: AccountsPayableCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    account_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                """INSERT INTO accounts_payable (id, description, amount, due_date, paid_date,
                   category, is_paid, notes, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (account_id, account.description, account.amount, account.due_date, None,
                 account.category, False, account.notes, datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM accounts_payable WHERE id = %s", (account_id,))
            result = await cursor.fetchone()
            return AccountsPayable(**result)

@api_router.get("/finance/accounts-payable", response_model=List[AccountsPayable])
async def get_accounts_payable(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM accounts_payable ORDER BY due_date DESC")
            accounts = await cursor.fetchall()
            return [AccountsPayable(**a) for a in accounts]

@api_router.patch("/finance/accounts-payable/{account_id}/pay")
async def pay_account(account_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE accounts_payable SET is_paid = %s, paid_date = %s WHERE id = %s",
                (True, datetime.now(timezone.utc), account_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Account not found")
            return {"message": "Account marked as paid"}

@api_router.delete("/finance/accounts-payable/{account_id}")
async def delete_accounts_payable(account_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("DELETE FROM accounts_payable WHERE id = %s", (account_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Account not found")
            return {"message": "Account deleted successfully"}

# Accounts Receivable routes
@api_router.get("/finance/accounts-receivable", response_model=List[AccountsReceivable])
async def get_accounts_receivable(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM accounts_receivable ORDER BY due_date DESC")
            accounts = await cursor.fetchall()
            return [AccountsReceivable(**a) for a in accounts]

@api_router.patch("/finance/accounts-receivable/{account_id}/receive")
async def receive_payment(account_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "UPDATE accounts_receivable SET is_received = %s, received_date = %s WHERE id = %s",
                (True, datetime.now(timezone.utc), account_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Account not found")
            return {"message": "Payment received"}

@api_router.delete("/finance/accounts-receivable/{account_id}")
async def delete_accounts_receivable(account_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("DELETE FROM accounts_receivable WHERE id = %s", (account_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Account not found")
            return {"message": "Account deleted successfully"}

# Dashboard stats
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Count dumpsters by status
            await cursor.execute("SELECT COUNT(*) as total FROM dumpsters")
            result = await cursor.fetchone()
            total_dumpsters = result['total']
            
            await cursor.execute("SELECT COUNT(*) as total FROM dumpsters WHERE status = 'available'")
            result = await cursor.fetchone()
            available_dumpsters = result['total']
            
            await cursor.execute("SELECT COUNT(*) as total FROM dumpsters WHERE status = 'rented'")
            result = await cursor.fetchone()
            rented_dumpsters = result['total']
            
            # Count orders
            await cursor.execute("SELECT COUNT(*) as total FROM orders WHERE status IN ('pending', 'in_progress')")
            result = await cursor.fetchone()
            active_orders = result['total']
            
            await cursor.execute("SELECT COUNT(*) as total FROM orders WHERE status = 'pending'")
            result = await cursor.fetchone()
            pending_orders = result['total']
            
            # Calculate revenue for current month
            now = datetime.now(timezone.utc)
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            await cursor.execute(
                "SELECT COALESCE(SUM(rental_value), 0) as total FROM orders WHERE created_at >= %s",
                (start_of_month,)
            )
            result = await cursor.fetchone()
            total_revenue_month = float(result['total'])
            
            # Calculate receivables
            await cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM accounts_receivable WHERE is_received = FALSE"
            )
            result = await cursor.fetchone()
            total_receivable = float(result['total'])
            
            # Calculate payables
            await cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM accounts_payable WHERE is_paid = FALSE"
            )
            result = await cursor.fetchone()
            total_payable = float(result['total'])
            
            # Calculate cash balance
            await cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM accounts_receivable WHERE is_received = TRUE"
            )
            result = await cursor.fetchone()
            received = float(result['total'])
            
            await cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) as total FROM accounts_payable WHERE is_paid = TRUE"
            )
            result = await cursor.fetchone()
            paid = float(result['total'])
            
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
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute("SELECT * FROM orders WHERE client_id = %s ORDER BY created_at DESC", (client_id,))
            orders = await cursor.fetchall()
            return [Order(**o) for o in orders]

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
async def shutdown_db():
    global db_pool
    if db_pool:
        db_pool.close()
        await db_pool.wait_closed()
