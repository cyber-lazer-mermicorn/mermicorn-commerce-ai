"""
Mermicorn API — FastAPI REST Endpoints
=======================================
Production API for all verticals.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from stack import MermicornStack


# ════════════════════════════════════════════════════════════════
# MODELS
# ════════════════════════════════════════════════════════════════

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class APIKeyRequest(BaseModel):
    name: str = Field(..., min_length=1)
    permissions: str = "read"

class CoinRequest(BaseModel):
    name: str
    year: int
    grade: str = ""
    price: float = 0

class VehicleRequest(BaseModel):
    year: int
    make: str
    model: str
    price: float = 0
    mileage: int = 0

class DealRequest(BaseModel):
    destination: str
    price: float
    dates: str
    source: str = ""

class ChampionRequest(BaseModel):
    name: str
    tier: str = "B"
    win_rate: float = 50

class GameRequest(BaseModel):
    champion: str
    result: str
    kda: str = "0/0/0"
    items: list[str] = []

class ProductRequest(BaseModel):
    name: str
    price: float
    description: str = ""
    tags: list[str] = []

# ════════════════════════════════════════════════════════════════
# APP
# ════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Mermicorn API",
    description="Production API for Cherry's Mermicorn constellation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stack instances
stacks: dict[str, MermicornStack] = {}


def get_stack(service: str) -> MermicornStack:
    if service not in stacks:
        stacks[service] = MermicornStack(service)
    return stacks[service]


security = HTTPBearer(auto_error=False)

async def verify_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """Verify authentication."""
    stack = get_stack("auth")
    
    # Check API key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = stack.auth.verify_api_key(api_key)
        if user:
            return user
    
    # Check Bearer token
    if credentials:
        user = stack.auth.verify_api_key(credentials.credentials)
        if user:
            return user
    
    # Allow unauthenticated for docs/login
    if request.url.path in ["/", "/docs", "/redoc", "/openapi.json", "/auth/login", "/auth/register"]:
        return {"id": "anonymous", "username": "anonymous", "role": "guest"}
    
    raise HTTPException(status_code=401, detail="Authentication required")


# ════════════════════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/auth/register")
def register(req: CreateUserRequest):
    stack = get_stack("auth")
    try:
        user = stack.auth.create_user(req.username, req.email, req.password)
        return {"success": True, "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
def login(req: LoginRequest):
    stack = get_stack("auth")
    user = stack.auth.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"success": True, "user": user}

@app.post("/auth/api-keys")
def create_api_key(req: APIKeyRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("auth")
    key = stack.auth.create_api_key(user["id"], req.name, req.permissions)
    return {"success": True, "api_key": key}

@app.get("/auth/me")
def get_me(user: dict = Depends(verify_auth)):
    return {"user": user}


# ════════════════════════════════════════════════════════════════
# NUMISMATIC ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/api/coins")
def add_coin(req: CoinRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("numismatic")
    stack.db.execute(
        "INSERT INTO coins (id, name, year, grade, price, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.name, req.year, req.grade, req.price, user["id"], time.time())
    )
    return {"success": True, "coin": req.dict()}

@app.get("/api/coins")
def list_coins(user: dict = Depends(verify_auth)):
    stack = get_stack("numismatic")
    coins = stack.db.fetch_all("SELECT * FROM coins WHERE owner_id = ?", (user["id"],))
    return {"coins": coins}

@app.get("/api/coins/{coin_id}")
def get_coin(coin_id: str, user: dict = Depends(verify_auth)):
    stack = get_stack("numismatic")
    coin = stack.db.fetch_one("SELECT * FROM coins WHERE id = ? AND owner_id = ?", (coin_id, user["id"]))
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return {"coin": coin}

@app.delete("/api/coins/{coin_id}")
def delete_coin(coin_id: str, user: dict = Depends(verify_auth)):
    stack = get_stack("numismatic")
    stack.db.execute("DELETE FROM coins WHERE id = ? AND owner_id = ?", (coin_id, user["id"]))
    return {"success": True}


# ════════════════════════════════════════════════════════════════
# AUTO ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/api/vehicles")
def add_vehicle(req: VehicleRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("auto")
    stack.db.execute(
        "INSERT INTO vehicles (id, year, make, model, price, mileage, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.year, req.make, req.model, req.price, req.mileage, user["id"], time.time())
    )
    return {"success": True, "vehicle": req.dict()}

@app.get("/api/vehicles")
def list_vehicles(user: dict = Depends(verify_auth)):
    stack = get_stack("auto")
    vehicles = stack.db.fetch_all("SELECT * FROM vehicles WHERE owner_id = ?", (user["id"],))
    return {"vehicles": vehicles}

@app.get("/api/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str, user: dict = Depends(verify_auth)):
    stack = get_stack("auto")
    vehicle = stack.db.fetch_one("SELECT * FROM vehicles WHERE id = ? AND owner_id = ?", (vehicle_id, user["id"]))
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return {"vehicle": vehicle}


# ════════════════════════════════════════════════════════════════
# TRAVEL ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/api/deals")
def add_deal(req: DealRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("travel")
    stack.db.execute(
        "INSERT INTO deals (id, destination, price, dates, source, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.destination, req.price, req.dates, req.source, user["id"], time.time())
    )
    return {"success": True, "deal": req.dict()}

@app.get("/api/deals")
def list_deals(user: dict = Depends(verify_auth)):
    stack = get_stack("travel")
    deals = stack.db.fetch_all("SELECT * FROM deals WHERE owner_id = ?", (user["id"],))
    return {"deals": deals}

@app.get("/api/deals/cheapest")
def cheapest_deal(destination: str, user: dict = Depends(verify_auth)):
    stack = get_stack("travel")
    deal = stack.db.fetch_one(
        "SELECT * FROM deals WHERE destination = ? AND owner_id = ? ORDER BY price ASC LIMIT 1",
        (destination, user["id"])
    )
    return {"deal": deal}


# ════════════════════════════════════════════════════════════════
# RIFT ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/api/champions")
def add_champion(req: ChampionRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("rift")
    stack.db.execute(
        "INSERT INTO champions (id, name, tier, win_rate, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.name, req.tier, req.win_rate, user["id"], time.time())
    )
    return {"success": True, "champion": req.dict()}

@app.get("/api/champions")
def list_champions(user: dict = Depends(verify_auth)):
    stack = get_stack("rift")
    champions = stack.db.fetch_all("SELECT * FROM champions WHERE owner_id = ?", (user["id"],))
    return {"champions": champions}

@app.post("/api/games")
def record_game(req: GameRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("rift")
    stack.db.execute(
        "INSERT INTO games (id, champion, result, kda, items, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.champion, req.result, req.kda, json.dumps(req.items), user["id"], time.time())
    )
    return {"success": True, "game": req.dict()}

@app.get("/api/games")
def list_games(user: dict = Depends(verify_auth)):
    stack = get_stack("rift")
    games = stack.db.fetch_all("SELECT * FROM games WHERE owner_id = ?", (user["id"],))
    return {"games": games}


# ════════════════════════════════════════════════════════════════
# COMMERCE ROUTES
# ════════════════════════════════════════════════════════════════

@app.post("/api/products")
def add_product(req: ProductRequest, user: dict = Depends(verify_auth)):
    stack = get_stack("commerce")
    stack.db.execute(
        "INSERT INTO products (id, name, price, description, tags, owner_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (str(time.time()), req.name, req.price, req.description, json.dumps(req.tags), user["id"], time.time())
    )
    return {"success": True, "product": req.dict()}

@app.get("/api/products")
def list_products(user: dict = Depends(verify_auth)):
    stack = get_stack("commerce")
    products = stack.db.fetch_all("SELECT * FROM products WHERE owner_id = ?", (user["id"],))
    return {"products": products}


# ════════════════════════════════════════════════════════════════
# STATS ROUTES
# ════════════════════════════════════════════════════════════════

@app.get("/stats")
def get_stats(user: dict = Depends(verify_auth)):
    stats = {}
    for name in ["numismatic", "auto", "travel", "rift", "commerce"]:
        try:
            stack = get_stack(name)
            stats[name] = stack.get_stats()
        except Exception:
            stats[name] = {"error": "not initialized"}
    return {"stats": stats}


# ════════════════════════════════════════════════════════════════
# HEALTH
# ════════════════════════════════════════════════════════════════

@app.get("/health")
def health():
    return {"status": "healthy", "service": "mermicorn-api", "version": "1.0.0"}

@app.get("/")
def root():
    return {
        "service": "Mermicorn API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth/register, /auth/login, /auth/api-keys",
            "numismatic": "/api/coins",
            "auto": "/api/vehicles",
            "travel": "/api/deals",
            "rift": "/api/champions, /api/games",
            "commerce": "/api/products",
            "stats": "/stats",
        }
    }


# ════════════════════════════════════════════════════════════════
# INIT TABLES
# ════════════════════════════════════════════════════════════════

@app.on_event("startup")
def startup():
    """Initialize database tables."""
    for service in ["numismatic", "auto", "travel", "rift", "commerce", "auth"]:
        stack = get_stack(service)
        
        if service == "numismatic":
            stack.db.execute("""CREATE TABLE IF NOT EXISTS coins (
                id TEXT PRIMARY KEY, name TEXT, year INTEGER, grade TEXT,
                price REAL, owner_id TEXT, created_at REAL)""")
        
        elif service == "auto":
            stack.db.execute("""CREATE TABLE IF NOT EXISTS vehicles (
                id TEXT PRIMARY KEY, year INTEGER, make TEXT, model TEXT,
                price REAL, mileage INTEGER, owner_id TEXT, created_at REAL)""")
        
        elif service == "travel":
            stack.db.execute("""CREATE TABLE IF NOT EXISTS deals (
                id TEXT PRIMARY KEY, destination TEXT, price REAL,
                dates TEXT, source TEXT, owner_id TEXT, created_at REAL)""")
        
        elif service == "rift":
            stack.db.execute("""CREATE TABLE IF NOT EXISTS champions (
                id TEXT PRIMARY KEY, name TEXT, tier TEXT,
                win_rate REAL, owner_id TEXT, created_at REAL)""")
            stack.db.execute("""CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY, champion TEXT, result TEXT,
                kda TEXT, items TEXT, owner_id TEXT, created_at REAL)""")
        
        elif service == "commerce":
            stack.db.execute("""CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY, name TEXT, price REAL,
                description TEXT, tags TEXT, owner_id TEXT, created_at REAL)""")
    
    stacks["auth"].logger.info("All database tables initialized")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
