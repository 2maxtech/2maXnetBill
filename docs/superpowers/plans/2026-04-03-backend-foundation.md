# 2maXnetBill Sub-plan 1: Backend Foundation + Core APIs

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up the backend project with Docker, database models, JWT authentication, and CRUD APIs for Plans, Customers, and Staff Users.

**Architecture:** Monolithic FastAPI backend with PostgreSQL (via SQLAlchemy 2.0 + Alembic), Redis for caching, and JWT-based authentication with role-based access control. All services run via Docker Compose for development.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, Redis 7, Docker Compose, pytest, bcrypt, python-jose

---

### Task 1: Project Scaffolding + Docker Compose

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `docker-compose.yml`
- Create: `docker-compose.dev.yml`

- [ ] **Step 1: Create backend requirements.txt**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.1
pydantic==2.10.4
pydantic-settings==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20
redis==5.2.1
celery[redis]==5.4.0
httpx==0.28.1
weasyprint==63.1
Jinja2==3.1.5
pytest==8.3.4
pytest-asyncio==0.25.0
pytest-httpx==0.35.0
email-validator==2.2.0
```

- [ ] **Step 2: Create backend Dockerfile**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

- [ ] **Step 3: Create app config**

Create `backend/app/__init__.py` (empty file).

Create `backend/app/core/__init__.py` (empty file).

Create `backend/app/core/config.py`:

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "2maXnetBill"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://netbill:netbill@db:5432/netbill"
    REDIS_URL: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    GATEWAY_AGENT_URL: str = "https://gateway:8443"
    GATEWAY_API_KEY: str = "change-me-in-production"

    BILLING_GENERATE_DAY: int = 1
    BILLING_DUE_DAY: int = 15
    BILLING_REMINDER_DAYS_BEFORE_DUE: int = 5
    BILLING_THROTTLE_DAYS_AFTER_DUE: int = 3
    BILLING_DISCONNECT_DAYS_AFTER_DUE: int = 5
    BILLING_TERMINATE_DAYS_AFTER_DUE: int = 35
    THROTTLE_DOWNLOAD_MBPS: int = 1
    THROTTLE_UPLOAD_KBPS: int = 512

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: Create FastAPI main app**

Create `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
```

- [ ] **Step 5: Create docker-compose.yml**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: netbill
      POSTGRES_PASSWORD: netbill
      POSTGRES_DB: netbill
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    environment:
      DATABASE_URL: postgresql+asyncpg://netbill:netbill@db:5432/netbill
      REDIS_URL: redis://redis:6379/0

volumes:
  pgdata:
```

- [ ] **Step 6: Create docker-compose.dev.yml**

```yaml
services:
  backend:
    environment:
      SECRET_KEY: dev-secret-key-not-for-production
      GATEWAY_API_KEY: dev-gateway-key
```

- [ ] **Step 7: Build and verify the stack starts**

Run: `cd /c/Users/2max/Desktop/2maXnetBill && docker compose up --build -d`

Then: `curl http://localhost:8000/health`

Expected: `{"status":"ok","service":"2maXnetBill"}`

- [ ] **Step 8: Commit**

```bash
git add backend/ docker-compose.yml docker-compose.dev.yml
git commit -m "feat: project scaffolding with FastAPI + Docker Compose"
```

---

### Task 2: Database Setup + Base Model

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/base.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`
- Create: `backend/alembic/versions/` (directory)

- [ ] **Step 1: Create database module**

Create `backend/app/core/database.py`:

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 2: Create base model**

Create `backend/app/models/__init__.py` (empty file).

Create `backend/app/models/base.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
```

- [ ] **Step 3: Initialize Alembic**

Run inside the backend container:

```bash
docker compose exec backend alembic init alembic
```

Then replace `backend/alembic.ini` sqlalchemy.url line:

```ini
sqlalchemy.url = postgresql+asyncpg://netbill:netbill@db:5432/netbill
```

- [ ] **Step 4: Configure Alembic env.py for async**

Replace `backend/alembic/env.py`:

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/database.py backend/app/models/ backend/alembic.ini backend/alembic/
git commit -m "feat: database setup with SQLAlchemy async + Alembic"
```

---

### Task 3: User Model + Migration

**Files:**
- Create: `backend/app/models/user.py`
- Modify: `backend/alembic/env.py` (import models)

- [ ] **Step 1: Create User model**

Create `backend/app/models/user.py`:

```python
import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    admin = "admin"
    billing = "billing"
    technician = "technician"


class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.admin)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

- [ ] **Step 2: Import User model in alembic env.py**

Add this import at the top of `backend/alembic/env.py`, after the existing imports:

```python
import app.models.user  # noqa: F401
```

- [ ] **Step 3: Generate and run migration**

```bash
docker compose exec backend alembic revision --autogenerate -m "create users table"
docker compose exec backend alembic upgrade head
```

- [ ] **Step 4: Verify table exists**

```bash
docker compose exec db psql -U netbill -c "\dt"
```

Expected: `users` table in the list.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/user.py backend/alembic/
git commit -m "feat: add User model with roles"
```

---

### Task 4: Auth System (JWT + Password Hashing)

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/dependencies.py`
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/main.py` (register router)
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: Create security module**

Create `backend/app/core/security.py`:

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
```

- [ ] **Step 2: Create auth schemas**

Create `backend/app/schemas/__init__.py` (empty file).

Create `backend/app/schemas/auth.py`:

```python
from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
```

Create `backend/app/schemas/user.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.admin


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
```

- [ ] **Step 3: Create auth dependencies**

Create `backend/app/core/dependencies.py`:

```python
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole

security_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user


def require_role(*roles: UserRole):
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return role_checker
```

- [ ] **Step 4: Create auth API endpoints**

Create `backend/app/api/__init__.py` (empty file).

Create `backend/app/api/auth.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 5: Register auth router in main.py**

Replace `backend/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": settings.PROJECT_NAME}
```

- [ ] **Step 6: Create test fixtures**

Create `backend/tests/__init__.py` (empty file).

Create `backend/tests/conftest.py`:

```python
import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.base import Base
from app.models.user import User, UserRole

TEST_DATABASE_URL = settings.DATABASE_URL.replace("/netbill", "/netbill_test")

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid.uuid4(),
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    response = await client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    return response.json()["access_token"]


@pytest_asyncio.fixture
async def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}
```

- [ ] **Step 7: Write auth tests**

Create `backend/tests/test_auth.py`:

```python
import pytest

from app.core.config import settings

API = settings.API_V1_PREFIX


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    response = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    response = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client):
    response = await client.post(f"{API}/auth/login", json={"username": "nobody", "password": "pass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    response = await client.get(f"{API}/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    response = await client.get(f"{API}/auth/me")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token(client, admin_user):
    login = await client.post(f"{API}/auth/login", json={"username": "admin", "password": "admin123"})
    refresh_token = login.json()["refresh_token"]

    response = await client.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()
```

- [ ] **Step 8: Create test database and run tests**

```bash
docker compose exec db psql -U netbill -c "CREATE DATABASE netbill_test;"
docker compose exec backend pytest tests/test_auth.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 9: Commit**

```bash
git add backend/app/core/security.py backend/app/core/dependencies.py backend/app/schemas/ backend/app/api/ backend/tests/
git commit -m "feat: JWT auth system with login, refresh, and RBAC"
```

---

### Task 5: Plan Model + CRUD API

**Files:**
- Create: `backend/app/models/plan.py`
- Create: `backend/app/schemas/plan.py`
- Create: `backend/app/api/admin/__init__.py`
- Create: `backend/app/api/admin/plans.py`
- Modify: `backend/app/main.py` (register router)
- Modify: `backend/alembic/env.py` (import model)
- Create: `backend/tests/test_plans.py`

- [ ] **Step 1: Create Plan model**

Create `backend/app/models/plan.py`:

```python
from decimal import Decimal

from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Plan(BaseModel):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    download_mbps: Mapped[int] = mapped_column(Integer, nullable=False)
    upload_mbps: Mapped[int] = mapped_column(Integer, nullable=False)
    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

- [ ] **Step 2: Create Plan schemas**

Create `backend/app/schemas/plan.py`:

```python
import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    download_mbps: int
    upload_mbps: int
    monthly_price: Decimal
    description: str | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    download_mbps: int | None = None
    upload_mbps: int | None = None
    monthly_price: Decimal | None = None
    description: str | None = None
    is_active: bool | None = None


class PlanResponse(BaseModel):
    id: uuid.UUID
    name: str
    download_mbps: int
    upload_mbps: int
    monthly_price: Decimal
    description: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Create Plan API endpoints**

Create `backend/app/api/admin/__init__.py` (empty file).

Create `backend/app/api/admin/plans.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.plan import Plan
from app.models.user import User
from app.schemas.plan import PlanCreate, PlanResponse, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanResponse])
async def list_plans(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Plan)
    if active_only:
        query = query.where(Plan.is_active == True)
    query = query.order_by(Plan.monthly_price)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    body: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = Plan(**body.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    body: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.flush()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Plan).where(Plan.id == plan_id))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan.is_active = False
    await db.flush()
```

- [ ] **Step 4: Register plans router in main.py**

Add import and include in `backend/app/main.py`:

```python
from app.api.admin.plans import router as plans_router

app.include_router(plans_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 5: Import model in alembic env.py and run migration**

Add to `backend/alembic/env.py`:

```python
import app.models.plan  # noqa: F401
```

Run:

```bash
docker compose exec backend alembic revision --autogenerate -m "create plans table"
docker compose exec backend alembic upgrade head
```

- [ ] **Step 6: Write plan tests**

Create `backend/tests/test_plans.py`:

```python
import pytest

from app.core.config import settings

API = settings.API_V1_PREFIX


@pytest.mark.asyncio
async def test_create_plan(client, auth_headers):
    response = await client.post(
        f"{API}/plans/",
        json={
            "name": "Basic 10Mbps",
            "download_mbps": 10,
            "upload_mbps": 5,
            "monthly_price": "999.00",
            "description": "Basic plan",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Basic 10Mbps"
    assert data["download_mbps"] == 10
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_list_plans(client, auth_headers):
    await client.post(
        f"{API}/plans/",
        json={"name": "Plan A", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    await client.post(
        f"{API}/plans/",
        json={"name": "Plan B", "download_mbps": 20, "upload_mbps": 10, "monthly_price": "1000.00"},
        headers=auth_headers,
    )
    response = await client.get(f"{API}/plans/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_get_plan(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "Test Plan", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.get(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Plan"


@pytest.mark.asyncio
async def test_update_plan(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "Old Name", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.put(
        f"{API}/plans/{plan_id}", json={"name": "New Name"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_plan_soft(client, auth_headers):
    create = await client.post(
        f"{API}/plans/",
        json={"name": "To Delete", "download_mbps": 10, "upload_mbps": 5, "monthly_price": "500.00"},
        headers=auth_headers,
    )
    plan_id = create.json()["id"]

    response = await client.delete(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = await client.get(f"{API}/plans/{plan_id}", headers=auth_headers)
    assert get_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_plan_not_found(client, auth_headers):
    response = await client.get(f"{API}/plans/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert response.status_code == 404
```

- [ ] **Step 7: Run tests**

```bash
docker compose exec backend pytest tests/test_plans.py -v
```

Expected: All 6 tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/plan.py backend/app/schemas/plan.py backend/app/api/admin/ backend/tests/test_plans.py backend/alembic/
git commit -m "feat: Plan CRUD API with tests"
```

---

### Task 6: Customer Model + CRUD API

**Files:**
- Create: `backend/app/models/customer.py`
- Create: `backend/app/schemas/customer.py`
- Create: `backend/app/api/admin/customers.py`
- Modify: `backend/app/main.py` (register router)
- Modify: `backend/alembic/env.py` (import model)
- Create: `backend/tests/test_customers.py`

- [ ] **Step 1: Create Customer model**

Create `backend/app/models/customer.py`:

```python
import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class CustomerStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    disconnected = "disconnected"
    terminated = "terminated"


class Customer(BaseModel):
    __tablename__ = "customers"

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    pppoe_username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pppoe_password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[CustomerStatus] = mapped_column(
        Enum(CustomerStatus), default=CustomerStatus.active, nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    plan = relationship("Plan", lazy="selectin")
```

- [ ] **Step 2: Create Customer schemas**

Create `backend/app/schemas/customer.py`:

```python
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.customer import CustomerStatus
from app.schemas.plan import PlanResponse


class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str | None = None
    pppoe_username: str
    pppoe_password: str
    plan_id: uuid.UUID


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    address: str | None = None
    pppoe_username: str | None = None
    pppoe_password: str | None = None
    plan_id: uuid.UUID | None = None
    status: CustomerStatus | None = None


class CustomerResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str
    address: str | None
    pppoe_username: str
    status: CustomerStatus
    plan_id: uuid.UUID
    plan: PlanResponse | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int
```

- [ ] **Step 3: Create Customer API endpoints**

Create `backend/app/api/admin/customers.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.customer import Customer, CustomerStatus
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerListResponse, CustomerResponse, CustomerUpdate

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: CustomerStatus | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Customer)
    count_query = select(func.count(Customer.id))

    if status_filter:
        query = query.where(Customer.status == status_filter)
        count_query = count_query.where(Customer.status == status_filter)

    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Customer.full_name.ilike(search_filter))
            | (Customer.email.ilike(search_filter))
            | (Customer.pppoe_username.ilike(search_filter))
        )
        count_query = count_query.where(
            (Customer.full_name.ilike(search_filter))
            | (Customer.email.ilike(search_filter))
            | (Customer.pppoe_username.ilike(search_filter))
        )

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Customer.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)

    return CustomerListResponse(
        items=result.scalars().all(),
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    customer = Customer(**body.model_dump())
    db.add(customer)
    await db.flush()
    await db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: uuid.UUID,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)

    await db.flush()
    await db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    customer.status = CustomerStatus.terminated
    await db.flush()
```

- [ ] **Step 4: Register customer router in main.py**

Add import and include in `backend/app/main.py`:

```python
from app.api.admin.customers import router as customers_router

app.include_router(customers_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 5: Import model in alembic env.py and run migration**

Add to `backend/alembic/env.py`:

```python
import app.models.customer  # noqa: F401
```

Run:

```bash
docker compose exec backend alembic revision --autogenerate -m "create customers table"
docker compose exec backend alembic upgrade head
```

- [ ] **Step 6: Write customer tests**

Create `backend/tests/test_customers.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.plan import Plan

API = settings.API_V1_PREFIX


@pytest_asyncio.fixture
async def test_plan(db_session: AsyncSession) -> Plan:
    plan = Plan(
        name="Test Plan 10Mbps",
        download_mbps=10,
        upload_mbps=5,
        monthly_price=999.00,
        is_active=True,
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


def customer_payload(plan_id: str, suffix: str = "") -> dict:
    return {
        "full_name": f"Juan Cruz{suffix}",
        "email": f"juan{suffix}@example.com",
        "phone": "09171234567",
        "address": "Manila, Philippines",
        "pppoe_username": f"juan{suffix}",
        "pppoe_password": "secret123",
        "plan_id": plan_id,
    }


@pytest.mark.asyncio
async def test_create_customer(client, auth_headers, test_plan):
    response = await client.post(
        f"{API}/customers/",
        json=customer_payload(str(test_plan.id)),
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Juan Cruz"
    assert data["status"] == "active"
    assert data["pppoe_username"] == "juan"
    assert "pppoe_password" not in data  # should not expose password


@pytest.mark.asyncio
async def test_list_customers_paginated(client, auth_headers, test_plan):
    for i in range(5):
        await client.post(
            f"{API}/customers/",
            json=customer_payload(str(test_plan.id), suffix=str(i)),
            headers=auth_headers,
        )
    response = await client.get(f"{API}/customers/?page=1&page_size=3", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 5
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_search_customers(client, auth_headers, test_plan):
    await client.post(
        f"{API}/customers/",
        json=customer_payload(str(test_plan.id), suffix="_search"),
        headers=auth_headers,
    )
    response = await client.get(f"{API}/customers/?search=juan_search", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_customer(client, auth_headers, test_plan):
    create = await client.post(
        f"{API}/customers/",
        json=customer_payload(str(test_plan.id), suffix="_get"),
        headers=auth_headers,
    )
    customer_id = create.json()["id"]

    response = await client.get(f"{API}/customers/{customer_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Juan Cruz_get"


@pytest.mark.asyncio
async def test_update_customer(client, auth_headers, test_plan):
    create = await client.post(
        f"{API}/customers/",
        json=customer_payload(str(test_plan.id), suffix="_upd"),
        headers=auth_headers,
    )
    customer_id = create.json()["id"]

    response = await client.put(
        f"{API}/customers/{customer_id}",
        json={"full_name": "Updated Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_customer_soft(client, auth_headers, test_plan):
    create = await client.post(
        f"{API}/customers/",
        json=customer_payload(str(test_plan.id), suffix="_del"),
        headers=auth_headers,
    )
    customer_id = create.json()["id"]

    response = await client.delete(f"{API}/customers/{customer_id}", headers=auth_headers)
    assert response.status_code == 204

    get_resp = await client.get(f"{API}/customers/{customer_id}", headers=auth_headers)
    assert get_resp.json()["status"] == "terminated"


@pytest.mark.asyncio
async def test_customer_not_found(client, auth_headers):
    response = await client.get(
        f"{API}/customers/00000000-0000-0000-0000-000000000000", headers=auth_headers
    )
    assert response.status_code == 404
```

- [ ] **Step 7: Run tests**

```bash
docker compose exec backend pytest tests/test_customers.py -v
```

Expected: All 7 tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/customer.py backend/app/schemas/customer.py backend/app/api/admin/customers.py backend/tests/test_customers.py backend/alembic/
git commit -m "feat: Customer CRUD API with pagination, search, and tests"
```

---

### Task 7: Staff User Management API

**Files:**
- Create: `backend/app/api/admin/users.py`
- Modify: `backend/app/main.py` (register router)
- Create: `backend/tests/test_users.py`

- [ ] **Step 1: Create user management API endpoints**

Create `backend/app/api/admin/users.py`:

```python
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_role
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/system/users", tags=["users"])


@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    existing = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username or email already exists")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.flush()
```

- [ ] **Step 2: Register users router in main.py**

Add import and include in `backend/app/main.py`:

```python
from app.api.admin.users import router as users_router

app.include_router(users_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 3: Write user management tests**

Create `backend/tests/test_users.py`:

```python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole

API = settings.API_V1_PREFIX


@pytest_asyncio.fixture
async def billing_user(db_session: AsyncSession) -> User:
    user = User(
        username="billing_user",
        email="billing@test.com",
        password_hash=hash_password("billing123"),
        role=UserRole.billing,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def billing_headers(billing_user: User) -> dict:
    token = create_access_token(str(billing_user.id), billing_user.role.value)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_list_users(client, auth_headers, admin_user):
    response = await client.get(f"{API}/system/users/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_create_user(client, auth_headers):
    response = await client.post(
        f"{API}/system/users/",
        json={
            "username": "newuser",
            "email": "new@test.com",
            "password": "newpass123",
            "role": "billing",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "billing"


@pytest.mark.asyncio
async def test_create_user_duplicate(client, auth_headers, admin_user):
    response = await client.post(
        f"{API}/system/users/",
        json={
            "username": "admin",
            "email": "another@test.com",
            "password": "pass",
            "role": "billing",
        },
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_update_user(client, auth_headers):
    create = await client.post(
        f"{API}/system/users/",
        json={"username": "toupdate", "email": "up@test.com", "password": "pass", "role": "technician"},
        headers=auth_headers,
    )
    user_id = create.json()["id"]

    response = await client.put(
        f"{API}/system/users/{user_id}", json={"role": "billing"}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["role"] == "billing"


@pytest.mark.asyncio
async def test_delete_user(client, auth_headers):
    create = await client.post(
        f"{API}/system/users/",
        json={"username": "todelete", "email": "del@test.com", "password": "pass", "role": "technician"},
        headers=auth_headers,
    )
    user_id = create.json()["id"]

    response = await client.delete(f"{API}/system/users/{user_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_cannot_delete_self(client, auth_headers, admin_user):
    response = await client.delete(
        f"{API}/system/users/{admin_user.id}", headers=auth_headers
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_non_admin_cannot_manage_users(client, billing_headers):
    response = await client.get(f"{API}/system/users/", headers=billing_headers)
    assert response.status_code == 403
```

- [ ] **Step 4: Run tests**

```bash
docker compose exec backend pytest tests/test_users.py -v
```

Expected: All 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/admin/users.py backend/tests/test_users.py
git commit -m "feat: staff user management API (admin-only) with tests"
```

---

### Task 8: Remaining Data Models (Invoice, Payment, PPPoE, Activity, etc.)

**Files:**
- Create: `backend/app/models/invoice.py`
- Create: `backend/app/models/payment.py`
- Create: `backend/app/models/pppoe_session.py`
- Create: `backend/app/models/session_traffic.py`
- Create: `backend/app/models/bandwidth_usage.py`
- Create: `backend/app/models/customer_activity.py`
- Create: `backend/app/models/notification.py`
- Create: `backend/app/models/disconnect_log.py`
- Modify: `backend/alembic/env.py` (import all models)

- [ ] **Step 1: Create Invoice model**

Create `backend/app/models/invoice.py`:

```python
import enum
import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class InvoiceStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    void = "void"


class Invoice(BaseModel):
    __tablename__ = "invoices"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.pending, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer = relationship("Customer", lazy="selectin")
    plan = relationship("Plan", lazy="selectin")
    payments = relationship("Payment", back_populates="invoice", lazy="selectin")
```

- [ ] **Step 2: Create Payment model**

Create `backend/app/models/payment.py`:

```python
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    bank = "bank"
    online = "online"


class Payment(BaseModel):
    __tablename__ = "payments"

    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    received_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    invoice = relationship("Invoice", back_populates="payments")
    receiver = relationship("User", lazy="selectin")
```

- [ ] **Step 3: Create PPPoESession model**

Create `backend/app/models/pppoe_session.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PPPoESession(BaseModel):
    __tablename__ = "pppoe_sessions"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    session_id: Mapped[str] = mapped_column(String(100), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    mac_address: Mapped[str] = mapped_column(String(17), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    bytes_in: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_out: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    disconnect_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    customer = relationship("Customer", lazy="selectin")
```

- [ ] **Step 4: Create SessionTraffic model**

Create `backend/app/models/session_traffic.py`:

```python
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class SessionTraffic(BaseModel):
    __tablename__ = "session_traffic"

    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("pppoe_sessions.id"), nullable=False)
    bytes_in: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    bytes_out: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    packets_in: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    packets_out: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    sampled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

- [ ] **Step 5: Create BandwidthUsage model**

Create `backend/app/models/bandwidth_usage.py`:

```python
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BandwidthUsage(BaseModel):
    __tablename__ = "bandwidth_usage"
    __table_args__ = (UniqueConstraint("customer_id", "date", name="uq_bandwidth_customer_date"),)

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_bytes_in: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_bytes_out: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    peak_download_mbps: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    peak_upload_mbps: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)
```

- [ ] **Step 6: Create CustomerActivity model**

Create `backend/app/models/customer_activity.py`:

```python
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ActivityEventType(str, enum.Enum):
    login = "login"
    logout = "logout"
    auth_fail = "auth_fail"
    ip_change = "ip_change"
    plan_change = "plan_change"
    throttled = "throttled"
    disconnected = "disconnected"


class CustomerActivity(BaseModel):
    __tablename__ = "customer_activities"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    event_type: Mapped[ActivityEventType] = mapped_column(Enum(ActivityEventType), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
```

- [ ] **Step 7: Create Notification model**

Create `backend/app/models/notification.py`:

```python
import enum
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel
from datetime import datetime


class NotificationType(str, enum.Enum):
    sms = "sms"
    email = "email"


class NotificationStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Notification(BaseModel):
    __tablename__ = "notifications"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus), default=NotificationStatus.pending, nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 8: Create DisconnectLog model**

Create `backend/app/models/disconnect_log.py`:

```python
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class DisconnectAction(str, enum.Enum):
    throttle = "throttle"
    disconnect = "disconnect"
    reconnect = "reconnect"


class DisconnectReason(str, enum.Enum):
    non_payment = "non_payment"
    manual = "manual"
    expired = "expired"


class DisconnectLog(BaseModel):
    __tablename__ = "disconnect_logs"

    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    action: Mapped[DisconnectAction] = mapped_column(Enum(DisconnectAction), nullable=False)
    reason: Mapped[DisconnectReason] = mapped_column(Enum(DisconnectReason), nullable=False)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    customer = relationship("Customer", lazy="selectin")
    performer = relationship("User", lazy="selectin")
```

- [ ] **Step 9: Import all models in alembic env.py**

Replace the model imports in `backend/alembic/env.py` with:

```python
import app.models.user  # noqa: F401
import app.models.plan  # noqa: F401
import app.models.customer  # noqa: F401
import app.models.invoice  # noqa: F401
import app.models.payment  # noqa: F401
import app.models.pppoe_session  # noqa: F401
import app.models.session_traffic  # noqa: F401
import app.models.bandwidth_usage  # noqa: F401
import app.models.customer_activity  # noqa: F401
import app.models.notification  # noqa: F401
import app.models.disconnect_log  # noqa: F401
```

- [ ] **Step 10: Generate and run migration**

```bash
docker compose exec backend alembic revision --autogenerate -m "create billing and monitoring tables"
docker compose exec backend alembic upgrade head
```

- [ ] **Step 11: Verify all tables exist**

```bash
docker compose exec db psql -U netbill -c "\dt"
```

Expected: `users`, `plans`, `customers`, `invoices`, `payments`, `pppoe_sessions`, `session_traffic`, `bandwidth_usage`, `customer_activities`, `notifications`, `disconnect_logs` tables.

- [ ] **Step 12: Commit**

```bash
git add backend/app/models/ backend/alembic/
git commit -m "feat: add all Phase 1 data models (billing, PPPoE, monitoring)"
```

---

### Task 9: Admin CLI — Create Initial Admin User

**Files:**
- Create: `backend/app/cli.py`

- [ ] **Step 1: Create CLI script**

Create `backend/app/cli.py`:

```python
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole


async def create_admin(username: str, email: str, password: str):
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        existing = await session.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            print(f"User '{username}' already exists.")
            return

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Admin user '{username}' created successfully.")

    await engine.dispose()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python -m app.cli <username> <email> <password>")
        sys.exit(1)

    asyncio.run(create_admin(sys.argv[1], sys.argv[2], sys.argv[3]))
```

- [ ] **Step 2: Test the CLI**

```bash
docker compose exec backend python -m app.cli admin admin@2maxnetbill.com admin123
```

Expected: `Admin user 'admin' created successfully.`

- [ ] **Step 3: Verify login works with new admin**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Expected: JSON response with `access_token` and `refresh_token`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/cli.py
git commit -m "feat: admin CLI to create initial admin user"
```

---

### Task 10: Run Full Test Suite + Push

- [ ] **Step 1: Run all tests**

```bash
docker compose exec backend pytest tests/ -v
```

Expected: All tests pass (auth: 6, plans: 6, customers: 7, users: 7 = ~26 tests).

- [ ] **Step 2: Push to GitHub**

```bash
cd /c/Users/2max/Desktop/2maXnetBill
git push origin main
```

- [ ] **Step 3: Verify on GitHub**

Check https://github.com/2maxtech/2maXnetBill — all files should be there.
