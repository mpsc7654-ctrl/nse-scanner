"""
Load tests for NSE Scanner API.
Install: pip install locust
Run:     locust -f tests/load_test.py --host=http://localhost:8000 --users=50 --spawn-rate=5 --run-time=60s --headless
"""
from locust import HttpUser, task, between
import random

SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK",
    "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC", "LT",
]

class ScannerUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def get_all_signals(self):
        with self.client.get("/api/v1/scanner/signals", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"status {r.status_code}")

    @task(3)
    def get_symbol(self):
        sym = random.choice(SYMBOLS)
        with self.client.get(f"/api/v1/scanner/symbol/{sym}", catch_response=True) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"status {r.status_code}")

    @task(2)
    def get_market_breadth(self):
        with self.client.get("/api/v1/market/breadth", catch_response=True) as r:
            if r.status_code == 200:
                r.success()
            else:
                r.failure(f"status {r.status_code}")

    @task(1)
    def get_stock_detail(self):
        sym = random.choice(SYMBOLS)
        with self.client.get(f"/api/v1/stock/{sym}/detail", catch_response=True) as r:
            if r.status_code in (200, 404):
                r.success()
            else:
                r.failure(f"status {r.status_code}")

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(1)
    def get_symbols(self):
        self.client.get("/api/v1/symbols")

    @task(1)
    def get_watchlists(self):
        self.client.get("/api/v1/watchlists")
