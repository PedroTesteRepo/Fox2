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

# Client Phones routes
@api_router.post("/clients/{client_id}/phones", response_model=ClientPhone)
async def create_client_phone(client_id: str, phone_data: ClientPhoneCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    phone_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Check if client exists
            await cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Client not found")
            
            # If is_primary is True, set all other phones to non-primary
            if phone_data.is_primary:
                await cursor.execute(
                    "UPDATE client_phones SET is_primary = FALSE WHERE client_id = %s",
                    (client_id,)
                )
            
            await cursor.execute(
                """INSERT INTO client_phones (id, client_id, phone, phone_type, is_primary, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (phone_id, client_id, phone_data.phone, phone_data.phone_type, 
                 phone_data.is_primary, datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM client_phones WHERE id = %s", (phone_id,))
            result = await cursor.fetchone()
            return ClientPhone(**result)

@api_router.get("/clients/{client_id}/phones", response_model=List[ClientPhone])
async def get_client_phones(client_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM client_phones WHERE client_id = %s ORDER BY is_primary DESC, created_at ASC",
                (client_id,)
            )
            phones = await cursor.fetchall()
            return [ClientPhone(**p) for p in phones]

@api_router.put("/clients/{client_id}/phones/{phone_id}", response_model=ClientPhone)
async def update_client_phone(client_id: str, phone_id: str, phone_data: ClientPhoneCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # If is_primary is True, set all other phones to non-primary
            if phone_data.is_primary:
                await cursor.execute(
                    "UPDATE client_phones SET is_primary = FALSE WHERE client_id = %s AND id != %s",
                    (client_id, phone_id)
                )
            
            await cursor.execute(
                """UPDATE client_phones SET phone = %s, phone_type = %s, is_primary = %s 
                   WHERE id = %s AND client_id = %s""",
                (phone_data.phone, phone_data.phone_type, phone_data.is_primary, phone_id, client_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Phone not found")
            
            await cursor.execute("SELECT * FROM client_phones WHERE id = %s", (phone_id,))
            result = await cursor.fetchone()
            return ClientPhone(**result)

@api_router.delete("/clients/{client_id}/phones/{phone_id}")
async def delete_client_phone(client_id: str, phone_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "DELETE FROM client_phones WHERE id = %s AND client_id = %s",
                (phone_id, client_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Phone not found")
            return {"message": "Phone deleted successfully"}

# Client Addresses routes
@api_router.post("/clients/{client_id}/addresses", response_model=ClientAddress)
async def create_client_address(client_id: str, address_data: ClientAddressCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    address_id = str(uuid.uuid4())
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Check if client exists
            await cursor.execute("SELECT id FROM clients WHERE id = %s", (client_id,))
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail="Client not found")
            
            # If is_primary is True, set all other addresses to non-primary
            if address_data.is_primary:
                await cursor.execute(
                    "UPDATE client_addresses SET is_primary = FALSE WHERE client_id = %s",
                    (client_id,)
                )
            
            await cursor.execute(
                """INSERT INTO client_addresses (id, client_id, address_type, cep, street, number, 
                   complement, neighborhood, city, state, is_primary, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (address_id, client_id, address_data.address_type, address_data.cep,
                 address_data.street, address_data.number, address_data.complement,
                 address_data.neighborhood, address_data.city, address_data.state,
                 address_data.is_primary, datetime.now(timezone.utc))
            )
            
            await cursor.execute("SELECT * FROM client_addresses WHERE id = %s", (address_id,))
            result = await cursor.fetchone()
            return ClientAddress(**result)

@api_router.get("/clients/{client_id}/addresses", response_model=List[ClientAddress])
async def get_client_addresses(client_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "SELECT * FROM client_addresses WHERE client_id = %s ORDER BY is_primary DESC, created_at ASC",
                (client_id,)
            )
            addresses = await cursor.fetchall()
            return [ClientAddress(**a) for a in addresses]

@api_router.put("/clients/{client_id}/addresses/{address_id}", response_model=ClientAddress)
async def update_client_address(client_id: str, address_id: str, address_data: ClientAddressCreate, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # If is_primary is True, set all other addresses to non-primary
            if address_data.is_primary:
                await cursor.execute(
                    "UPDATE client_addresses SET is_primary = FALSE WHERE client_id = %s AND id != %s",
                    (client_id, address_id)
                )
            
            await cursor.execute(
                """UPDATE client_addresses SET address_type = %s, cep = %s, street = %s, 
                   number = %s, complement = %s, neighborhood = %s, city = %s, state = %s, 
                   is_primary = %s WHERE id = %s AND client_id = %s""",
                (address_data.address_type, address_data.cep, address_data.street,
                 address_data.number, address_data.complement, address_data.neighborhood,
                 address_data.city, address_data.state, address_data.is_primary, 
                 address_id, client_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Address not found")
            
            await cursor.execute("SELECT * FROM client_addresses WHERE id = %s", (address_id,))
            result = await cursor.fetchone()
            return ClientAddress(**result)

@api_router.delete("/clients/{client_id}/addresses/{address_id}")
async def delete_client_address(client_id: str, address_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(
                "DELETE FROM client_addresses WHERE id = %s AND client_id = %s",
                (address_id, client_id)
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Address not found")
            return {"message": "Address deleted successfully"}

# CEP Lookup (ViaCEP integration)
@api_router.get("/cep/{cep}")
async def get_address_by_cep(cep: str, current_user: User = Depends(get_current_user)):
    # Remove non-numeric characters
    cep_clean = ''.join(filter(str.isdigit, cep))
    
    if len(cep_clean) != 8:
        raise HTTPException(status_code=400, detail="CEP must have 8 digits")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://viacep.com.br/ws/{cep_clean}/json/")
            response.raise_for_status()
            data = response.json()
            
            if data.get("erro"):
                raise HTTPException(status_code=404, detail="CEP not found")
            
            return {
                "cep": data.get("cep", ""),
                "street": data.get("logradouro", ""),
                "complement": data.get("complemento", ""),
                "neighborhood": data.get("bairro", ""),
                "city": data.get("localidade", ""),
                "state": data.get("uf", "")
            }
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Error connecting to CEP service")

# Client Financial Summary
@api_router.get("/clients/{client_id}/financial-summary", response_model=ClientFinancialSummary)
async def get_client_financial_summary(client_id: str, current_user: User = Depends(get_current_user)):
    pool = await get_db()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cursor:
            # Get client
            await cursor.execute("SELECT * FROM clients WHERE id = %s", (client_id,))
            client = await cursor.fetchone()
            if not client:
                raise HTTPException(status_code=404, detail="Client not found")
            
            # Get orders
            await cursor.execute(
                "SELECT * FROM orders WHERE client_id = %s ORDER BY created_at DESC",
                (client_id,)
            )
            orders = await cursor.fetchall()
            
            # Get accounts receivable
            await cursor.execute(
                "SELECT * FROM accounts_receivable WHERE client_id = %s ORDER BY due_date ASC",
                (client_id,)
            )
            accounts = await cursor.fetchall()
            
            # Calculate statistics
            total_orders = len(orders)
            pending_orders = len([o for o in orders if o["status"] == OrderStatus.PENDING or o["status"] == OrderStatus.IN_PROGRESS])
            completed_orders = len([o for o in orders if o["status"] == OrderStatus.COMPLETED])
            
            total_receivable = sum(a["amount"] for a in accounts)
            total_received = sum(a["amount"] for a in accounts if a["is_received"])
            pending_amount = sum(a["amount"] for a in accounts if not a["is_received"])
            
            return ClientFinancialSummary(
                client=Client(**client),
                total_orders=total_orders,
                pending_orders=pending_orders,
                completed_orders=completed_orders,
                total_receivable=total_receivable,
                total_received=total_received,
                pending_amount=pending_amount,
                orders=[Order(**o) for o in orders],
                accounts_receivable=[AccountsReceivable(**a) for a in accounts]
            )


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
            
            # If delivery_address_id is provided, get the full address
            delivery_address_text = order.delivery_address
            if order.delivery_address_id:
                await cursor.execute(
                    "SELECT * FROM client_addresses WHERE id = %s AND client_id = %s",
                    (order.delivery_address_id, order.client_id)
                )
                address = await cursor.fetchone()
                if address:
                    # Format full address
                    delivery_address_text = f"{address['street']}, {address['number']}"
                    if address['complement']:
                        delivery_address_text += f" - {address['complement']}"
                    delivery_address_text += f" - {address['neighborhood']}, {address['city']}/{address['state']} - CEP: {address['cep']}"
            
            # Create order
            await cursor.execute(
                """INSERT INTO orders (id, client_id, client_name, dumpster_id, dumpster_identifier,
                   order_type, status, delivery_address, delivery_address_id, rental_value, payment_method, 
                   scheduled_date, completed_date, notes, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (order_id, order.client_id, client["name"], order.dumpster_id, dumpster["identifier"],
                 order.order_type, OrderStatus.PENDING, delivery_address_text, order.delivery_address_id,
                 order.rental_value, order.payment_method, order.scheduled_date, None, order.notes, 
                 datetime.now(timezone.utc))
            )
            
            # Update dumpster status
            if order.order_type == OrderType.PLACEMENT:
                await cursor.execute(
                    "UPDATE dumpsters SET status = %s, current_location = %s WHERE id = %s",
                    (DumpsterStatus.RENTED, delivery_address_text, order.dumpster_id)
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
