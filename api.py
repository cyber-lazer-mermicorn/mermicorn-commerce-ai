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

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent / "src"))

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

from commerce_ai.stack import MermicornStack


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


# ════════════════════════════════════════════════════════════════
# DASHBOARD ROUTES
# ════════════════════════════════════════════════════════════════

@app.get("/app", response_class=HTMLResponse)
def mobile_app():
    """Mobile-first PWA app."""
    from pathlib import Path
    return Path(__file__).parent.joinpath("app.html").read_text()


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Main dashboard — all verticals."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mermicorn — Cherry's Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0a0a0f; color: #e0e0e0; font-family: 'Inter', sans-serif; }
        .neon { text-shadow: 0 0 10px currentColor; }
        .card { background: #12121a; border: 1px solid #2a2a3a; border-radius: 12px; }
        .glow-purple { box-shadow: 0 0 20px rgba(168,85,247,0.3); }
        .glow-pink { box-shadow: 0 0 20px rgba(236,72,153,0.3); }
        .glow-cyan { box-shadow: 0 0 20px rgba(6,182,212,0.3); }
        .glow-green { box-shadow: 0 0 20px rgba(34,197,94,0.3); }
        .glow-yellow { box-shadow: 0 0 20px rgba(234,179,8,0.3); }
        .btn { transition: all 0.2s; }
        .btn:hover { transform: translateY(-2px); }
    </style>
</head>
<body class="min-h-screen p-6">
    <div class="max-w-7xl mx-auto">
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold neon text-purple-400 mb-2">MERMICORN</h1>
            <p class="text-gray-400 text-lg">Cherry's AI-Powered Business Empire</p>
        </div>
        
        <div class="grid grid-cols-5 gap-4 mb-8">
            <a href="/dash/commerce" class="card p-6 text-center glow-purple hover:scale-105 transition-transform">
                <div class="text-3xl mb-2">🛍️</div>
                <div class="font-bold text-purple-400">Commerce</div>
                <div class="text-xs text-gray-500">Products & Sales</div>
            </a>
            <a href="/dash/numismatic" class="card p-6 text-center glow-yellow hover:scale-105 transition-transform">
                <div class="text-3xl mb-2">🪙</div>
                <div class="font-bold text-yellow-400">Numismatic</div>
                <div class="text-xs text-gray-500">Coin Intelligence</div>
            </a>
            <a href="/dash/auto" class="card p-6 text-center glow-cyan hover:scale-105 transition-transform">
                <div class="text-3xl mb-2">🚗</div>
                <div class="font-bold text-cyan-400">Auto</div>
                <div class="text-xs text-gray-500">Vehicle Matching</div>
            </a>
            <a href="/dash/travel" class="card p-6 text-center glow-green hover:scale-105 transition-transform">
                <div class="text-3xl mb-2">✈️</div>
                <div class="font-bold text-green-400">Travel</div>
                <div class="text-xs text-gray-500">Deal Hunting</div>
            </a>
            <a href="/dash/rift" class="card p-6 text-center glow-pink hover:scale-105 transition-transform">
                <div class="text-3xl mb-2">⚔️</div>
                <div class="font-bold text-pink-400">Rift</div>
                <div class="text-xs text-gray-500">Gaming Intel</div>
            </a>
        </div>
        
        <div class="card p-8">
            <h2 class="text-2xl font-bold mb-4">🚀 Quick Start</h2>
            <div class="grid grid-cols-3 gap-6">
                <div>
                    <h3 class="font-bold text-purple-400 mb-2">1. Register</h3>
                    <code class="text-xs bg-gray-800 p-2 rounded block">curl -X POST /auth/register -d '{"username":"cherry","email":"cherry@m.com","password":"pass"}'</code>
                </div>
                <div>
                    <h3 class="font-bold text-pink-400 mb-2">2. Get API Key</h3>
                    <code class="text-xs bg-gray-800 p-2 rounded block">Response: {"api_key": "mk_..."}</code>
                </div>
                <div>
                    <h3 class="font-bold text-cyan-400 mb-2">3. Start Using</h3>
                    <code class="text-xs bg-gray-800 p-2 rounded block">curl -H "X-API-Key: mk_..." /api/products</code>
                </div>
            </div>
        </div>
        
        <div class="text-center mt-8 text-gray-600 text-sm">
            <p>API: <a href="/docs" class="text-purple-400">/docs</a> | Health: <a href="/health" class="text-green-400">/health</a></p>
        </div>
    </div>
</body>
</html>"""


@app.get("/dash/{vertical}", response_class=HTMLResponse)
def vertical_dashboard(vertical: str):
    """Vertical-specific dashboard."""
    dashboards = {
        "commerce": _commerce_dashboard,
        "numismatic": _numismatic_dashboard,
        "auto": _auto_dashboard,
        "travel": _travel_dashboard,
        "rift": _rift_dashboard,
    }
    handler = dashboards.get(vertical)
    if handler:
        return handler()
    return HTMLResponse("<h1>Dashboard not found</h1>", status_code=404)


def _commerce_dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Commerce</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#0a0a0f;color:#e0e0e0;font-family:Inter,sans-serif}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px}
input,select,textarea{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:8px 12px;color:#e0e0e0;width:100%}
button{padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;transition:all .2s}
button:hover{transform:translateY(-1px)}</style></head>
<body class="p-6"><div class="max-w-4xl mx-auto">
<h1 class="text-3xl font-bold text-purple-400 mb-6">🛍️ Commerce Dashboard</h1>
<a href="/dashboard" class="text-gray-400 text-sm mb-4 inline-block">← Back to Hub</a>
<div class="card p-6 mb-6">
<h2 class="text-xl font-bold mb-4">Add Product</h2>
<div class="grid grid-cols-2 gap-4 mb-4">
<input id="name" placeholder="Product name">
<input id="price" type="number" placeholder="Price">
<textarea id="desc" placeholder="Description" rows="2"></textarea>
<input id="tags" placeholder="Tags (comma separated)">
</div>
<button onclick="add()" class="bg-purple-600 w-full">Add Product</button>
</div>
<div id="list" class="space-y-2"></div>
</div>
<script>
const K=sessionStorage.getItem('api_key')||prompt('Enter API Key:');
sessionStorage.setItem('api_key',K);
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json','X-API-Key':K}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
async function add(){await api('POST','/api/products',{name:document.getElementById('name').value,price:+document.getElementById('price').value,description:document.getElementById('desc').value,tags:document.getElementById('tags').value.split(',')});load()}
async function load(){const d=await api('GET','/api/products');document.getElementById('list').innerHTML=(d.products||[]).map(p=>'<div class="bg-gray-800 p-3 rounded">'+p.name+' — $'+p.price+'</div>').join('')}
load();
</script></body></html>"""


def _numismatic_dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Numismatic</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#0a0a0f;color:#e0e0e0;font-family:Inter,sans-serif}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px}
input,select{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:8px 12px;color:#e0e0e0;width:100%}
button{padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;transition:all .2s}
button:hover{transform:translateY(-1px)}</style></head>
<body class="p-6"><div class="max-w-4xl mx-auto">
<h1 class="text-3xl font-bold text-yellow-400 mb-6">🪙 Coin Intelligence</h1>
<a href="/dashboard" class="text-gray-400 text-sm mb-4 inline-block">← Back to Hub</a>
<div class="card p-6 mb-6">
<h2 class="text-xl font-bold mb-4">Add Coin</h2>
<div class="grid grid-cols-4 gap-4 mb-4">
<input id="name" placeholder="Coin name">
<input id="year" type="number" placeholder="Year">
<input id="grade" placeholder="Grade (VF-30)">
<input id="price" type="number" placeholder="Price">
</div>
<button onclick="add()" class="bg-yellow-600 w-full">Add Coin</button>
</div>
<div id="list" class="space-y-2"></div>
</div>
<script>
const K=sessionStorage.getItem('api_key')||prompt('Enter API Key:');
sessionStorage.setItem('api_key',K);
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json','X-API-Key':K}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
async function add(){await api('POST','/api/coins',{name:document.getElementById('name').value,year:+document.getElementById('year').value,grade:document.getElementById('grade').value,price:+document.getElementById('price').value});load()}
async function load(){const d=await api('GET','/api/coins');document.getElementById('list').innerHTML=(d.coins||[]).map(c=>'<div class="bg-gray-800 p-3 rounded">'+c.name+' ('+c.year+') '+c.grade+' — $'+c.price+'</div>').join('')}
load();
</script></body></html>"""


def _auto_dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Auto</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#0a0a0f;color:#e0e0e0;font-family:Inter,sans-serif}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px}
input{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:8px 12px;color:#e0e0e0;width:100%}
button{padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;transition:all .2s}
button:hover{transform:translateY(-1px)}</style></head>
<body class="p-6"><div class="max-w-4xl mx-auto">
<h1 class="text-3xl font-bold text-cyan-400 mb-6">🚗 Auto Matchmaker</h1>
<a href="/dashboard" class="text-gray-400 text-sm mb-4 inline-block">← Back to Hub</a>
<div class="card p-6 mb-6">
<h2 class="text-xl font-bold mb-4">Add Vehicle</h2>
<div class="grid grid-cols-3 gap-4 mb-4">
<input id="year" type="number" placeholder="Year">
<input id="make" placeholder="Make">
<input id="model" placeholder="Model">
<input id="price" type="number" placeholder="Price">
<input id="mileage" type="number" placeholder="Mileage">
</div>
<button onclick="add()" class="bg-cyan-600 w-full">Add Vehicle</button>
</div>
<div id="list" class="space-y-2"></div>
</div>
<script>
const K=sessionStorage.getItem('api_key')||prompt('Enter API Key:');
sessionStorage.setItem('api_key',K);
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json','X-API-Key':K}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
async function add(){await api('POST','/api/vehicles',{year:+document.getElementById('year').value,make:document.getElementById('make').value,model:document.getElementById('model').value,price:+document.getElementById('price').value,mileage:+document.getElementById('mileage').value});load()}
async function load(){const d=await api('GET','/api/vehicles');document.getElementById('list').innerHTML=(d.vehicles||[]).map(v=>'<div class="bg-gray-800 p-3 rounded">'+v.year+' '+v.make+' '+v.model+' — $'+v.price.toLocaleString()+'</div>').join('')}
load();
</script></body></html>"""


def _travel_dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Travel</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#0a0a0f;color:#e0e0e0;font-family:Inter,sans-serif}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px}
input{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:8px 12px;color:#e0e0e0;width:100%}
button{padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;transition:all .2s}
button:hover{transform:translateY(-1px)}</style></head>
<body class="p-6"><div class="max-w-4xl mx-auto">
<h1 class="text-3xl font-bold text-green-400 mb-6">✈️ Travel Deals</h1>
<a href="/dashboard" class="text-gray-400 text-sm mb-4 inline-block">← Back to Hub</a>
<div class="card p-6 mb-6">
<h2 class="text-xl font-bold mb-4">Add Deal</h2>
<div class="grid grid-cols-4 gap-4 mb-4">
<input id="dest" placeholder="Destination">
<input id="price" type="number" placeholder="Price">
<input id="dates" placeholder="Aug 15-22">
<input id="source" placeholder="Source">
</div>
<button onclick="add()" class="bg-green-600 w-full">Add Deal</button>
</div>
<div id="list" class="space-y-2"></div>
</div>
<script>
const K=sessionStorage.getItem('api_key')||prompt('Enter API Key:');
sessionStorage.setItem('api_key',K);
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json','X-API-Key':K}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
async function add(){await api('POST','/api/deals',{destination:document.getElementById('dest').value,price:+document.getElementById('price').value,dates:document.getElementById('dates').value,source:document.getElementById('source').value});load()}
async function load(){const d=await api('GET','/api/deals');document.getElementById('list').innerHTML=(d.deals||[]).map(x=>'<div class="bg-gray-800 p-3 rounded">'+x.destination+' '+x.dates+' — $'+x.price+'</div>').join('')}
load();
</script></body></html>"""


def _rift_dashboard():
    return """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Rift</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{background:#0a0a0f;color:#e0e0e0;font-family:Inter,sans-serif}
.card{background:#12121a;border:1px solid #2a2a3a;border-radius:12px}
input,select{background:#1f2937;border:1px solid #374151;border-radius:8px;padding:8px 12px;color:#e0e0e0;width:100%}
button{padding:10px 20px;border-radius:8px;font-weight:bold;cursor:pointer;transition:all .2s}
button:hover{transform:translateY(-1px)}</style></head>
<body class="p-6"><div class="max-w-4xl mx-auto">
<h1 class="text-3xl font-bold text-pink-400 mb-6">⚔️ Rift Lab</h1>
<a href="/dashboard" class="text-gray-400 text-sm mb-4 inline-block">← Back to Hub</a>
<div class="card p-6 mb-6">
<h2 class="text-xl font-bold mb-4">Add Champion</h2>
<div class="grid grid-cols-3 gap-4 mb-4">
<input id="name" placeholder="Champion name">
<select id="tier"><option>S+</option><option>S</option><option>A</option><option>B</option><option>C</option><option>D</option></select>
<input id="wr" type="number" placeholder="Win Rate %" step="0.1">
</div>
<button onclick="add()" class="bg-pink-600 w-full">Add Champion</button>
</div>
<div id="list" class="space-y-2"></div>
</div>
<script>
const K=sessionStorage.getItem('api_key')||prompt('Enter API Key:');
sessionStorage.setItem('api_key',K);
async function api(m,p,b){const o={method:m,headers:{'Content-Type':'application/json','X-API-Key':K}};if(b)o.body=JSON.stringify(b);return(await fetch(p,o)).json()}
async function add(){await api('POST','/api/champions',{name:document.getElementById('name').value,tier:document.getElementById('tier').value,win_rate:+document.getElementById('wr').value});load()}
async function load(){const d=await api('GET','/api/champions');document.getElementById('list').innerHTML=(d.champions||[]).map(c=>'<div class="bg-gray-800 p-3 rounded">'+c.name+' ['+c.tier+'] '+c.win_rate+'%</div>').join('')}
load();
</script></body></html>"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
