"""
Integration Tests — Full API Flow
==================================
Tests the complete request lifecycle.
"""

import os
import sys
import time
import threading
import urllib.request
import json
import pytest

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent / "src"))

API_BASE = "http://127.0.0.1:9876"


@pytest.fixture(scope="module")
def api_server():
    """Start API server for tests."""
    import subprocess
    proc = subprocess.Popen(
        [sys.executable, "api.py"],
        cwd=str(__import__("pathlib").Path(__file__).parent.parent.parent),
        env={**os.environ, "PORT": "9876"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(3)
    yield API_BASE
    proc.terminate()
    proc.wait()


def api_call(method, path, body=None, headers=None):
    """Make API call."""
    url = API_BASE + path
    opts = {"method": method, "headers": headers or {}}
    opts["headers"]["Content-Type"] = "application/json"
    if body:
        opts["body"] = json.dumps(body).encode()
    req = urllib.request.Request(url, **opts)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code


class TestHealthEndpoint:
    def test_health_returns_200(self, api_server):
        data, status = api_call("GET", "/health")
        assert status == 200
        assert data["status"] == "healthy"

    def test_health_has_version(self, api_server):
        data, _ = api_call("GET", "/health")
        assert "version" in data


class TestAuthFlow:
    def test_register(self, api_server):
        data, status = api_call("POST", "/auth/register", {
            "username": f"test_{int(time.time())}",
            "email": f"test_{int(time.time())}@test.com",
            "password": "testpass123",
        })
        assert status == 200
        assert data["success"] is True
        assert "api_key" in data["user"]

    def test_login(self, api_server):
        uname = f"login_{int(time.time())}"
        api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        data, status = api_call("POST", "/auth/login", {
            "username": uname, "password": "pass123"
        })
        assert status == 200
        assert data["success"] is True

    def test_unauthorized_access(self, api_server):
        data, status = api_call("GET", "/api/coins")
        assert status == 401

    def test_me_endpoint(self, api_server):
        uname = f"me_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        key = reg["user"]["api_key"]
        data, status = api_call("GET", "/auth/me", headers={"X-API-Key": key})
        assert status == 200
        assert data["user"]["username"] == uname


class TestCRUDCoins:
    @pytest.fixture(autouse=True)
    def setup(self, api_server):
        uname = f"coins_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        self.key = reg["user"]["api_key"]
        self.headers = {"X-API-Key": self.key}

    def test_add_coin(self, api_server):
        data, status = api_call("POST", "/api/coins", {
            "name": "Morgan Dollar", "year": 1889, "grade": "VF-30", "price": 52
        }, headers=self.headers)
        assert status == 200
        assert data["success"] is True

    def test_list_coins(self, api_server):
        api_call("POST", "/api/coins", {
            "name": "Peace Dollar", "year": 1922, "grade": "MS-63", "price": 45
        }, headers=self.headers)
        data, _ = api_call("GET", "/api/coins", headers=self.headers)
        assert len(data["coins"]) >= 1

    def test_coin_fields(self, api_server):
        api_call("POST", "/api/coins", {
            "name": "Buffalo Nickel", "year": 1913, "grade": "G-6", "price": 8
        }, headers=self.headers)
        data, _ = api_call("GET", "/api/coins", headers=self.headers)
        coin = data["coins"][0]
        assert "name" in coin
        assert "year" in coin
        assert "grade" in coin
        assert "price" in coin


class TestCRUDVehicles:
    @pytest.fixture(autouse=True)
    def setup(self, api_server):
        uname = f"cars_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        self.key = reg["user"]["api_key"]
        self.headers = {"X-API-Key": self.key}

    def test_add_vehicle(self, api_server):
        data, status = api_call("POST", "/api/vehicles", {
            "year": 2020, "make": "Honda", "model": "Civic", "price": 18500, "mileage": 45000
        }, headers=self.headers)
        assert status == 200
        assert data["success"] is True

    def test_list_vehicles(self, api_server):
        api_call("POST", "/api/vehicles", {
            "year": 2021, "make": "Toyota", "model": "Camry", "price": 25000, "mileage": 30000
        }, headers=self.headers)
        data, _ = api_call("GET", "/api/vehicles", headers=self.headers)
        assert len(data["vehicles"]) >= 1


class TestCRUDDeals:
    @pytest.fixture(autouse=True)
    def setup(self, api_server):
        uname = f"deals_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        self.key = reg["user"]["api_key"]
        self.headers = {"X-API-Key": self.key}

    def test_add_deal(self, api_server):
        data, status = api_call("POST", "/api/deals", {
            "destination": "Hawaii", "price": 299, "dates": "Aug 15-22", "source": "Skyscanner"
        }, headers=self.headers)
        assert status == 200
        assert data["success"] is True

    def test_list_deals(self, api_server):
        api_call("POST", "/api/deals", {
            "destination": "Paris", "price": 599, "dates": "Dec 1-7", "source": "Google"
        }, headers=self.headers)
        data, _ = api_call("GET", "/api/deals", headers=self.headers)
        assert len(data["deals"]) >= 1


class TestCRUDChampions:
    @pytest.fixture(autouse=True)
    def setup(self, api_server):
        uname = f"rift_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        self.key = reg["user"]["api_key"]
        self.headers = {"X-API-Key": self.key}

    def test_add_champion(self, api_server):
        data, status = api_call("POST", "/api/champions", {
            "name": "Ahri", "tier": "S+", "win_rate": 54.2
        }, headers=self.headers)
        assert status == 200
        assert data["success"] is True


class TestCRUDProducts:
    @pytest.fixture(autouse=True)
    def setup(self, api_server):
        uname = f"shop_{int(time.time())}"
        reg, _ = api_call("POST", "/auth/register", {
            "username": uname, "email": f"{uname}@t.com", "password": "pass123"
        })
        self.key = reg["user"]["api_key"]
        self.headers = {"X-API-Key": self.key}

    def test_add_product(self, api_server):
        data, status = api_call("POST", "/api/products", {
            "name": "Neon Top", "price": 89.99, "description": "UV reactive", "tags": ["rave"]
        }, headers=self.headers)
        assert status == 200
        assert data["success"] is True


class TestDashboardRoutes:
    def test_dashboard_serves(self, api_server):
        data, status = api_call("GET", "/dashboard")
        assert status == 200

    def test_app_serves(self, api_server):
        data, status = api_call("GET", "/app")
        assert status == 200

    def test_vertical_dashboards(self, api_server):
        for v in ["commerce", "numismatic", "auto", "travel", "rift"]:
            _, status = api_call("GET", f"/dash/{v}")
            assert status == 200


class TestRateLimiting:
    def test_rate_limit_header(self, api_server):
        _, status = api_call("GET", "/health")
        assert status == 200
