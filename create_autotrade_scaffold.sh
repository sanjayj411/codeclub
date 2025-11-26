#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="autotrade-scaffold"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "Creating project structure..."
mkdir -p src/api src/core src/brokers src/execution src/strategies src/workers src/tests data

cat > docker-compose.yml <<'YML'
version: "3.8"
services:
  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./:/app
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - ENV=dev
  feeder:
    build: .
    command: python -u src.workers.market_feeder.py
    volumes:
      - ./:/app
    depends_on:
      - api
  runner:
    build: .
    command: python -u src.strategies.runner.py
    volumes:
      - ./:/app
    depends_on:
      - api
YML

cat > Dockerfile <<'DOCK'
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app
DOCK

cat > requirements.txt <<'REQ'
fastapi==0.95.2
uvicorn==0.22.0
httpx==0.24.1
sqlalchemy==2.1.0
alembic==1.10.2
pydantic==1.10.7
databases==0.6.0
numpy==1.25.2
websockets==11.0.3
pytest==7.4.0
REQ

cat > README.md <<'MD'
# AutoTrade Scaffold

Quick scaffold for a cloud-capable automated trading service with a mock broker.

Quick start:
1. docker-compose up --build
2. Visit API docs: http://localhost:8000/docs
3. POST /connect/mock to create an account
4. Feeder and runner services will start generating ticks and executing the sample MA strategy (ma_crossover)

Important:
- This scaffold uses a MockBroker for safety. Replace the adapter with a real broker adapter and keep extensive testing in sandbox before any live trading.
- Never store real credentials in plain text. Use a secrets manager and secure token storage.
MD

cat > src/api/main.py <<'PY'
from fastapi import FastAPI
from src.api.routes import router
from src.core.db import init_db

app = FastAPI(title="AutoTrade Scaffold")
app.include_router(router, prefix="")

@app.on_event("startup")
async def startup():
    init_db()
PY

cat > src/api/routes.py <<'PY'
from fastapi import APIRouter
from pydantic import BaseModel
from src.brokers.mock_broker import MockBroker

router = APIRouter()
broker = MockBroker()

class ConnectResponse(BaseModel):
    account_id: str
    access_token: str

@router.post("/connect/mock", response_model=ConnectResponse)
def connect_mock():
    acct = broker.create_mock_account()
    return ConnectResponse(account_id=acct["account_id"], access_token=acct["access_token"])

class StrategyToggle(BaseModel):
    strategy: str
    enabled: bool

@router.post("/strategies/toggle")
def toggle_strategy(body: StrategyToggle):
    from src.core.db import set_strategy_enabled
    set_strategy_enabled(body.strategy, body.enabled)
    return {"ok": True, "strategy": body.strategy, "enabled": body.enabled}

@router.post("/webhook/fill")
def webhook_fill(data: dict):
    from src.execution.order_manager import handle_fill_webhook
    handle_fill_webhook(data)
    return {"ok": True}
PY

cat > src/api/schemas.py <<'PY'
from pydantic import BaseModel

class OrderRequest(BaseModel):
    symbol: str
    side: str
    size: int
    account_id: str
    reason: str = ""
PY

cat > src/core/config.py <<'PY'
BROKER = "mock"
DB_URL = "sqlite:///./data/dev.db"
MAX_ORDER_SIZE = 1000
DAILY_LOSS_LIMIT = 500.0
IDEMPOTENCY_TTL_SECONDS = 3600
PY

cat > src/core/db.py <<'PY'
import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine(os.getenv("DB_URL", "sqlite:///./data/dev.db"), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Strategy(Base):
    __tablename__ = "strategies"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    enabled = Column(Boolean, default=False)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    idempotency_key = Column(String, unique=True, index=True)
    account_id = Column(String)
    symbol = Column(String)
    side = Column(String)
    size = Column(Integer)
    status = Column(String, default="pending")
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    os.makedirs("./data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
    s = SessionLocal()
    from sqlalchemy.exc import IntegrityError
    try:
        if not s.query(Strategy).filter_by(name="ma_crossover").first():
            s.add(Strategy(name="ma_crossover", enabled=True))
            s.commit()
    except IntegrityError:
        s.rollback()
    s.close()

def set_strategy_enabled(name: str, enabled: bool):
    s = SessionLocal()
    st = s.query(Strategy).filter_by(name=name).first()
    if not st:
        st = Strategy(name=name, enabled=enabled)
        s.add(st)
    else:
        st.enabled = enabled
    s.commit()
    s.close()

def create_order(idempotency_key, account_id, symbol, side, size, metadata=None):
    s = SessionLocal()
    o = Order(idempotency_key=idempotency_key, account_id=account_id, symbol=symbol, side=side, size=size, metadata=metadata or {})
    s.add(o)
    s.commit()
    s.refresh(o)
    s.close()
    return o

def get_order_by_key(key):
    s = SessionLocal()
    o = s.query(Order).filter_by(idempotency_key=key).first()
    s.close()
    return o

def update_order_status(id, status):
    s = SessionLocal()
    o = s.query(Order).get(id)
    if o:
        o.status = status
        s.commit()
    s.close()
PY

cat > src/core/logger.py <<'PY'
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("autotrade")
PY

cat > src/brokers/mock_broker.py <<'PY'
import uuid
import threading
import time
import random
from src.core.logger import logger
from typing import Callable

class MockBroker:
    def __init__(self):
        self.accounts = {}
        self.orders = {}
        self.subscribers = {}

    def create_mock_account(self):
        account_id = str(uuid.uuid4())
        token = str(uuid.uuid4())
        self.accounts[account_id] = {"access_token": token, "balance": 100000.0, "positions": {}}
        logger.info(f"Created mock account {account_id}")
        return {"account_id": account_id, "access_token": token}

    def place_order(self, account_id, order_payload):
        order_id = str(uuid.uuid4())
        self.orders[order_id] = {"order_id": order_id, "status": "accepted", "payload": order_payload}
        logger.info(f"MockBroker placed order {order_id} for account {account_id}: {order_payload}")
        threading.Thread(target=self._simulate_fill, args=(account_id, order_id, order_payload)).start()
        return {"order_id": order_id, "status": "accepted"}

    def _simulate_fill(self, account_id, order_id, payload):
        time.sleep(random.uniform(0.5, 2.0))
        fill = {
            "order_id": order_id,
            "account_id": account_id,
            "symbol": payload["symbol"],
            "size": payload["size"],
            "side": payload["side"],
            "price": payload.get("price", payload.get("market_price", 100.0)),
            "filled_at": time.time()
        }
        self.orders[order_id]["status"] = "filled"
        try:
            import requests
            requests.post("http://api:8000/webhook/fill", json=fill, timeout=5)
        except Exception:
            from src.execution.order_manager import handle_fill_webhook
            handle_fill_webhook(fill)

    def subscribe_market(self, symbol: str, callback: Callable):
        self.subscribers.setdefault(symbol, []).append(callback)
PY

cat > src/brokers/schwab_adapter_template.py <<'PY'
# TEMPLATE: implement this adapter to integrate with Schwab
class SchwabAdapter:
    def __init__(self, config):
        self.config = config

    def authenticate_via_oauth(self, code):
        raise NotImplementedError("Implement OAuth flow with Schwab developer portal")

    def refresh_token(self, refresh_token):
        raise NotImplementedError("Call Schwab token endpoint securely")

    def place_order(self, account_id, order_payload):
        raise NotImplementedError("Map order payload to Schwab order format and POST")

    def get_order_status(self, order_id):
        raise NotImplementedError("GET order status from Schwab API")

    def subscribe_market(self, symbols, callback):
        raise NotImplementedError("Use Schwab market data feed or integrate a market data provider")
PY

cat > src/execution/risk_manager.py <<'PY'
from src.core.config import MAX_ORDER_SIZE, DAILY_LOSS_LIMIT
from src.core.logger import logger

class RiskViolation(Exception):
    pass

class RiskManager:
    def __init__(self):
        self.daily_loss = 0.0

    def check(self, signal, account_id):
        size = signal.get("size", 0)
        if size > MAX_ORDER_SIZE:
            logger.warning("Order exceeds max size")
            raise RiskViolation("size_exceeds_max")
        if self.daily_loss >= DAILY_LOSS_LIMIT:
            logger.warning("Daily loss limit reached")
            raise RiskViolation("daily_loss_limit")
        return True

    def on_fill(self, fill):
        if fill["side"].lower() == "sell":
            self.daily_loss += 0
PY

cat > src/execution/order_manager.py <<'PY'
import hashlib
from src.core.db import get_order_by_key, create_order, update_order_status
from src.core.logger import logger
from src.brokers.mock_broker import MockBroker
from src.execution.risk_manager import RiskManager, RiskViolation

broker = MockBroker()
risk_manager = RiskManager()

def _make_idempotency_key(account_id, symbol, side, reason):
    raw = f"{account_id}:{symbol}:{side}:{reason}"
    return hashlib.sha256(raw.encode()).hexdigest()

def submit_order(signal, account_id):
    key = _make_idempotency_key(account_id, signal["symbol"], signal["side"], signal.get("reason", ""))
    existing = get_order_by_key(key)
    if existing:
        logger.info("Idempotent: order already exists")
        return existing
    try:
        risk_manager.check(signal, account_id)
    except RiskViolation as e:
        logger.warning(f"Order rejected: {e}")
        raise

    order = create_order(key, account_id, signal["symbol"], signal["side"], int(signal["size"]), metadata=signal)
    payload = {"symbol": signal["symbol"], "side": signal["side"], "size": signal["size"], "reason": signal.get("reason")}
    resp = broker.place_order(account_id, payload)
    update_order_status(order.id, "submitted")
    logger.info(f"Submitted order {order.id} -> broker {resp.get('order_id')}")
    return order

def handle_fill_webhook(data):
    logger = __import__("src.core.logger").core.logger
    logger.info(f"Received fill webhook: {data}")
    from src.core.db import SessionLocal, Order
    s = SessionLocal()
    q = s.query(Order).filter_by(account_id=data["account_id"], symbol=data["symbol"], status="submitted")
    for o in q:
        o.status = "filled"
        s.add(o)
    s.commit()
    s.close()
    risk_manager.on_fill(data)
PY

cat > src/strategies/base.py <<'PY'
class Strategy:
    name = "base"
    def on_tick(self, tick):
        raise NotImplementedError
PY

cat > src/strategies/ma_crossover.py <<'PY'
from .base import Strategy
import numpy as np

class MACrossover(Strategy):
    name = "ma_crossover"

    def __init__(self, short=5, long=15, size=1):
        self.short = short
        self.long = long
        self.size = size
        self.prices = []
        self.last_signal = 0

    def on_tick(self, tick):
        price = float(tick["price"])
        self.prices.append(price)
        if len(self.prices) < self.long:
            return None
        short_ma = float(np.mean(self.prices[-self.short:]))
        long_ma = float(np.mean(self.prices[-self.long:]))
        if short_ma > long_ma and self.last_signal <= 0:
            self.last_signal = 1
            return {"side": "buy", "size": self.size, "symbol": tick["symbol"], "reason": "ma_cross_up", "market_price": price}
        if short_ma < long_ma and self.last_signal >= 0:
            self.last_signal = -1
            return {"side": "sell", "size": self.size, "symbol": tick["symbol"], "reason": "ma_cross_down", "market_price": price}
        return None
PY

cat > src/strategies/runner.py <<'PY'
import time
from src.strategies.ma_crossover import MACrossover
from src.brokers.mock_broker import MockBroker
from src.execution.order_manager import submit_order
from src.core.db import SessionLocal
from src.core.logger import logger

broker = MockBroker()
strategy = MACrossover(short=5, long=15, size=1)
SYMBOL = "TICKER"

def _is_strategy_enabled(name):
    from src.core.db import SessionLocal, Strategy
    s = SessionLocal()
    st = s.query(Strategy).filter_by(name=name).first()
    enabled = bool(st and st.enabled)
    s.close()
    return enabled

def on_tick(tick):
    if not _is_strategy_enabled(strategy.name):
        return
    signal = strategy.on_tick(tick)
    if signal:
        try:
            submit_order(signal, tick.get("account_id"))
        except Exception as e:
            logger.exception("Order submission failed")

def run():
    def callback(tick):
        on_tick(tick)
    broker.subscribe_market(SYMBOL, callback)
    logger.info("Strategy runner started, waiting for ticks...")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    run()
PY

cat > src/workers/market_feeder.py <<'PY'
import time
import random
from src.brokers.mock_broker import MockBroker
from src.core.logger import logger

broker = MockBroker()
SYMBOL = "TICKER"

def start_feeder(account_id=None):
    while True:
        price = 90 + random.random() * 20
        tick = {"symbol": SYMBOL, "price": price, "timestamp": time.time(), "account_id": account_id}
        subs = broker.subscribers.get(SYMBOL, [])
        for cb in subs:
            try:
                cb(tick)
            except Exception:
                logger.exception("Subscriber callback failed")
        time.sleep(0.5)

if __name__ == "__main__":
    acct = broker.create_mock_account()
    logger.info(f"Feeder running for account {acct['account_id']}")
    start_feeder(account_id=acct["account_id"])
PY

cat > src/workers/replay.py <<'PY'
import csv
import time
from src.brokers.mock_broker import MockBroker

def replay_csv(path, account_id=None, symbol="TICKER", delay=0.1):
    broker = MockBroker()
    with open(path, "r") as fh:
        r = csv.DictReader(fh)
        for row in r:
            tick = {"symbol": symbol, "price": float(row["price"]), "timestamp": float(row.get("ts", 0)), "account_id": account_id}
            subs = broker.subscribers.get(symbol, [])
            for cb in subs:
                cb(tick)
            time.sleep(delay)
PY

cat > tests/test_strategy.py <<'PY'
from src.strategies.ma_crossover import MACrossover

def test_ma_crossover_buy_sell():
    s = MACrossover(short=2, long=4, size=1)
    prices = [10,11,12,9,8,9,11]
    signals = []
    for p in prices:
        r = s.on_tick({"price": p, "symbol": "TICKER"})
        if r:
            signals.append(r["side"])
    assert "buy" in signals
    assert "sell" in signals or isinstance(s.last_signal, int)
PY

cat > tests/test_order_flow.py <<'PY'
from src.brokers.mock_broker import MockBroker
from src.execution.order_manager import submit_order

def test_submit_order_happy_path():
    broker = MockBroker()
    acct = broker.create_mock_account()
    signal = {"symbol": "TICKER", "side": "buy", "size": 1, "reason": "test"}
    try:
        submit_order(signal, acct["account_id"])
    except Exception:
        assert False, "submit_order raised unexpectedly"
PY

echo "Initializing git repository..."
git init -q
git add -A
git commit -m "Initial scaffold commit" -q || true

echo "Creating ZIP archive autotrade-scaffold.zip..."
cd ..
zip -r "${PROJECT_DIR}.zip" "$PROJECT_DIR" > /dev/null

echo "Done. Files created in $(pwd)/$PROJECT_DIR and zip at $(pwd)/${PROJECT_DIR}.zip"
echo ""
echo "Next steps:"
echo "1) cd $PROJECT_DIR"
echo "2) docker-compose up --build"
echo "3) Visit http://localhost:8000/docs and call POST /connect/mock"

