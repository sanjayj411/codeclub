# TDA Bot - Comprehensive Technical Analysis

**Analysis Date:** November 27, 2025  
**Source Repository:** `/tmp/tda-bot`  
**Total Files Analyzed:** 5 main components  
**Total Code Lines:** ~4,600 lines

---

## Executive Summary

The TDA Bot is a multi-broker automated trading system that supports TD Ameritrade, Alpaca, and Robinhood. It uses technical indicators (RSI, MACD) for trading signal generation and manages multiple bot instances through MongoDB. The system features real-time streaming, Telegram notifications, and a PySide2-based dashboard for visualization.

---

## 1. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                 Main Entry Point (tda_bot.py)           │
└────┬─────────────────────────────────────────────────────┘
     │
     ├── TD Ameritrade Integration
     │   ├── JadhavBot class (td_autotrade.py)
     │   └── TDA Streaming Session
     │
     ├── Alpaca Integration
     │   ├── AlpacaBot class (alpaca_autotrade.py)
     │   └── API REST Client
     │
     ├── Robinhood Integration
     │   └── RHBot class (Implied)
     │
     ├── MongoDB State Management
     │   └── Collections: BOT_SETUP, BOT_Trans, whatsapp
     │
     ├── Notification System
     │   ├── Telegram (telgram_test.py)
     │   └── SMS/WhatsApp (via AppleScript)
     │
     └── Visualization & Dashboard
         └── alpaca_dashboard.py (1823 lines)
             ├── Portfolio Management
             ├── Real-time Data Streaming
             ├── Trading Interface (PySide2/Qt)
             └── Watchlist Management
```

### Data Flow Diagram

```
TDA Streaming Session (WebSocket)
           ↓
   [f() Callback Function]
           ↓
    Indicator Calculation (RSI, MACD, MA)
           ↓
    Signal Generation (Entry/Exit Logic)
           ↓
    ┌──────────────────────────────────────┐
    ├─→ JadhavBot.analyze_entry_exit()    │
    ├─→ AlpacaBot.analyze_entry_exit()    │
    ├─→ RHBot.analyze_entry_exit()        │
    └──────────────────────────────────────┘
           ↓
    Order Placement & Execution
           ↓
    ┌──────────────────────────────────────┐
    ├─→ tda_api() [TDA]                    │
    ├─→ alpaca_api() [Alpaca]             │
    └──────────────────────────────────────┘
           ↓
    MongoDB State Update
           ↓
    Telegram Notification
           ↓
    Dashboard Update (Qt Signals)
```

---

## 2. Indicator Calculation Logic

### 2.1 RSI (Relative Strength Index)

**Location:** `tda_bot.py`, lines ~280-290

```python
# RSI Calculation
if len(closes[symbol]['close']) > RSI_PERIOD:
    np_closes = numpy.array(closes[symbol]['close'])
    rsi = talib.RSI(np_closes, RSI_PERIOD)
    last_rsi = rsi[-1]
    bots[symbol]['rsi'] = last_rsi
```

**Configuration:**
- Uses `talib.RSI()` (TA-Lib library)
- **RSI_PERIOD:** Default value (appears to be 14 based on standard RSI)
- **Thresholds:**
  - RSI < 30: Oversold (buy signal)
  - RSI > 70: Overbought (sell signal)
  - RSI_OVERSOLD constant (td_autotrade.py)
  - RSI_OVERBOUGHT constant (td_autotrade.py)

**Used In:**
- Entry logic: `if self.rsi < self.RSI_OVERSOLD`
- Exit logic: `if self.rsi > self.RSI_OVERBOUGHT`

---

### 2.2 MACD (Moving Average Convergence Divergence)

**Location:** `tda_bot.py`, lines ~291-295

```python
# Calculate MACD
macd, macd_signal, macd_hist = talib.MACD(np_closes)
bots[symbol]['macd'] = macd[-1]
bots[symbol]['macd_signal'] = macd_signal[-1]
bots[symbol]['macd_hist'] = macd_hist[-1]
```

**Configuration:**
- Uses `talib.MACD()` (TA-Lib library)
- Returns: `(macd, signal_line, histogram)`
- **Default Parameters:** 12, 26, 9 (standard MACD)

**Signal Generation (`buy_sell()` function):**
```python
if signal['macd'][i] > signal['macd_signal'][i]:
    # BUY SIGNAL
elif signal['macd'][i] < signal['macd_signal'][i]:
    # SELL SIGNAL
```

---

### 2.3 Moving Averages

**Location:** `tda_bot.py`, `get_indicators()` function, lines ~729-735

```python
def get_indicators(data):
    # Get MA10 and MA30
    data["ma10"] = talib.MA(data["close"], timeperiod=10)
    data["ma30"] = talib.MA(data["close"], timeperiod=30)
    
    # Get RSI
    data["rsi"] = talib.RSI(data["close"])
    
    # Get engulfing (candlestick pattern)
    engulfing = talib.CDLENGULFING(data['open'], data['high'], 
                                   data['low'], data['close'])
    data['engulfing'] = engulfing
```

**Moving Averages Used:**
- **MA10:** 10-period moving average
- **MA30:** 30-period moving average
- **Purpose:** Trend identification (not actively used in current trading logic, but available)

---

### 2.4 Candlestick Patterns

**Engulfing Pattern Detection:**
- Uses `talib.CDLENGULFING()` for candlestick pattern recognition
- Stores in `data['engulfing']`
- Available but not actively used in trading decisions

---

## 3. Trading Signal Generation Logic

### 3.1 RSI-Based Signals

**Location:** `td_autotrade.py` / `alpaca_autotrade.py`, `analyze_entry_exit()` method

**Buy Signal Generation:**
```python
if self.rsi < self.RSI_OVERSOLD and allow_entry:
    self.analyze_entry(current_price)
```

**Sell Signal Generation:**
```python
if self.rsi > self.RSI_OVERBOUGHT and allow_exit:
    self.analyze_exit(current_price)
```

**Thresholds:**
- `RSI_OVERSOLD`: Typically 30
- `RSI_OVERBOUGHT`: Typically 70
- Loaded from MongoDB BOT_SETUP collection

---

### 3.2 Price-Based Entry/Exit Logic

**Location:** Both `JadhavBot` and `AlpacaBot` classes

#### Entry Logic (`analyze_entry()`)

**Conditions for buy:**
1. ✓ RSI < RSI_OVERSOLD
2. ✓ Position queue not full: `len(self.prices) < self.MAX_ORDERS`
3. ✓ Price check:
   - First buy: Always allowed (good_buy = True)
   - Subsequent buys: Must be at least `BUY_THRESHOLD%` below minimum price
4. ✓ Time check (cooldown): Last buy > Duration threshold
5. ✓ Sudden jump check: Not spiked > 5% from prior close
6. ✓ Cash available: USD balance >= BUY_QTY * current_price
7. ✓ Not in sell_only list (for TDA only)

```python
# Price threshold calculation
min_last_buy = min(self.prices)
min_to_buy = self.calc_price("buy", min_last_buy, self.BUY_THRESHOLD)
# calc_price("BUY", price, 0.05) = (1 - 0.05) * price = 95% of price

if current_price < min_to_buy:
    good_buy = True
```

**Double Discount Logic:**
```python
# If too early but massive discount (2x threshold), still buy
if current_price < min_to_buy * (1 - self.BUY_THRESHOLD):
    good_buy = True  # Override cooldown
```

---

#### Exit Logic (`analyze_exit()`)

**Conditions for sell:**
1. ✓ RSI > RSI_OVERBOUGHT
2. ✓ Prices list not empty
3. ✓ Current price > `SELL_THRESHOLD%` above buy price
4. ✓ PDT (Pattern Day Trading) check: Different day than buy

```python
min_to_sell = self.calc_price("sell", prev_buy, self.SELL_THRESHOLD)
# calc_price("SELL", price, 0.05) = (1 + 0.05) * price = 105% of price

if current_price > min_to_sell and allow_exit:
    self.analyze_exit(current_price)
```

**PDT Prevention:**
```python
if datetime.now().day != max(self.dates).day:
    trigger_roundtrip = True  # Allows different-day exit
```

---

### 3.3 Multi-Bot Signal Routing

**Location:** `tda_bot.py`, main loop callback `f()`

```python
def f(symbol, data, candle_closed):
    # For each symbol, iterate through ALL active bots
    for bot in td_bots:
        if bot.symbol == symbol:
            curr_thread = threading.Thread(
                target=bot.analyze_entry_exit(last_rsi, current_price),
                args=()
            )
            curr_thread.start()
    
    # Also route to Alpaca and RobinHood bots
    alpaca_trade(symbol, current_price, last_rsi)
    robinhood_trade(symbol, current_price, last_rsi)
    tda_taxable_trade(session, symbol, current_price, last_rsi)
```

---

## 4. Order Placement Functions

### 4.1 TD Ameritrade Order Placement

**Location:** `td_autotrade.py`, `tda_api()` method, lines ~112-180

```python
def tda_api(self, action, curr_price, buyprice, buydate):
    action = action.upper()
    if action == 'BUY':
        qty = self.BUY_QTY
    else:
        qty = self.SELL_QTY
    
    data = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [{
            "instruction": action,
            "quantity": qty,
            "instrument": {
                "symbol": self.symbol,
                "assetType": "EQUITY"
            }
        }]
    }
    
    # Place order
    order = self.tdsession.place_order(self.accountno, data)
    
    # Retrieve order details
    response = self.tdsession.get_orders(self.accountno, orderid)
    
    # Extract execution details
    execleg = response['orderActivityCollection'][0]['executionLegs'][0]
    price = execleg['price']
    quantity = execleg['quantity']
```

**Order Parameters:**
- **Order Type:** MARKET
- **Session:** NORMAL (regular hours)
- **Duration:** DAY (intraday)
- **Strategy:** SINGLE (one-leg only)

---

### 4.2 Alpaca Order Placement

**Location:** `alpaca_autotrade.py`, `alpaca_api()` method, lines ~56-110

```python
def alpaca_api(self, action, curr_price, buyprice, buydate):
    action = action.lower()
    
    if action == 'buy':
        amount = self.BUY_AMT  # Dollar amount, not qty
    else:
        amount = self.SELL_AMT
    
    # Fractionable symbols support
    if self.symbol in self.fractionable_symbols:
        order = self.session.submit_order(
            symbol=self.symbol,
            notional=amount,  # Dollar amount
            side=action
        )
    else:
        # Non-fractionable: convert to quantity
        qty = round(amount/curr_price, 0)
        if curr_price > 100:
            tradeable = False
        elif qty > 0:
            order = self.session.submit_order(
                symbol=self.symbol,
                qty=qty,
                side=action
            )
    
    # Check order status
    order = self.session.get_order(order.id)
    order_id = order.id
    order_state = order.status
    price = float(order.filled_avg_price)
```

**Key Differences from TDA:**
- Uses **notional amount** (dollars) for fractionable assets
- Supports **fractional shares**
- Uses **submit_order()** instead of place_order()
- Retrieves **filled_avg_price** instead of execution legs

---

### 4.3 Order Persistence

**Location:** Both implementations, `save_order()` method

**MongoDB Storage (BOT_Trans collection):**
```python
order = {
    'trans_date': datetime.now(),
    'action': action,
    'price': price,
    'buyprice': buyprice,
    'buydate': buydate,
    'botid': self.ID,
    'symbol': self.symbol,
    'orderid': order_id,
    'status': order_state,
    # ... additional fields specific to broker
}
db['BOT_Trans'].insert_one(order)
```

---

## 5. Telegram Notification Functions

### 5.1 Basic Telegram Setup

**Location:** `telgram_test.py`

```python
import telegram_send

telegram_send.send(
    messages=["Good Morning"],
    conf="/Users/sanjayj/connfig/tdabot.conf"
)
```

**Configuration File:** `/Users/sanjayj/connfig/tdabot.conf`

---

### 5.2 Message Formats

**Location:** `tda_bot.py` and bot classes

#### Application Startup/Shutdown
```python
telegram_send.send(messages=["TDA Bot starting"])
telegram_send.send(messages=["Loading history..."])
telegram_send.send(messages=["TDA Bot running..."])
telegram_send.send(messages=["TDA Bot stopped. Done for the day!"])
```

#### Buy Signal
```python
text_msg = f'{self.ID}:{action} @{price} {len(self.prices)}'
# Example: "BOT_001:BUY @125.43 2"
```

#### Sell Signal
```python
text_msg = f'{self.ID}:{action} {price} {len(self.prices)}'
# Example: "BOT_001:SELL 125.50 1"
```

#### Daily Report
```python
msg = f"{symbol}({quantity:.1f})=${gain:.2f}"
# Example: "TSLA(10.0)=$125.50"

msg = f"\nTotal gain for today = *${total:.2f}*"
# Example: "Total gain for today = *$1250.75*"
```

#### Alpaca Specific
```python
text_msg = f'A_{self.symbol}:{action} {amount} {price}'
# Example: "A_TSLA:BUY 500 125.43"
```

---

### 5.3 Notification Queue

**Location:** `tda_bot.py`, worker thread, lines ~642-670

```python
q = queue.Queue()  # Global queue

def worker(browser):
    db = client['ODS']
    collection = db['whatsapp']
    
    while True:
        item = q.get()
        
        try:
            telegram_send.send(
                messages=[item],
                conf="/Users/sanjayj/connfig/tdabot.conf"
            )
        except Exception as e:
            print(f"Can't send telegram messages {str(e)}")
        
        q.task_done()

# Daemon thread startup
t = threading.Thread(target=worker, args=(browser,), daemon=True).start()
```

**Queue Usage:**
- Messages are put into `q` when trades occur
- Background daemon thread processes messages asynchronously
- Prevents blocking of trading logic

---

## 6. State Tracking Mechanisms

### 6.1 In-Memory State

**Location:** `tda_bot.py`, global dictionaries, lines ~96-106

```python
bots = {}           # Main bot state dictionary
closes = {}         # Closing prices by symbol
price_data = []     # Historical price data
last_checkin = datetime.now()

# Per-symbol state structure
bots[symbol] = {
    "close": 0.0,              # Last closing price
    "candle": False,           # Candle closed flag
    "rsi": 50,                 # Current RSI value
    "cci": 50,                 # Current CCI value (unused)
    "Take_Profit": True,       # Profit-taking enabled
    "prices": [],              # List of buy prices
    "dates": []                # List of buy dates
}

closes[symbol] = {
    'close': [],               # Array of closing prices
    'high': [],                # Array of highs
    'low': [],                 # Array of lows
    'volume': [],              # Array of volumes
    'datetime': []             # Array of timestamps
}
```

---

### 6.2 Database State (MongoDB)

**Location:** All bot classes

**Collections:**

1. **BOT_SETUP Collection**
   ```json
   {
       "BOT_ID": "BOT_001",
       "symbol": "TSLA",
       "Active": true,
       "BUY_QTY": 5,
       "SELL_QTY": 5,
       "BUY_AMT": 500,
       "SELL_AMT": 525,
       "BUY_THRESHOLD": 0.03,
       "SELL_THRESHOLD": 0.05,
       "RSI_OVERSOLD": 30,
       "RSI_OVERBOUGHT": 70,
       "MAX_ORDERS": 5,
       "Duration": 30,
       "Trade": true,
       "prices": [125.23, 124.50, 123.75],
       "dates": ["2025-11-27 10:30:00", ...],
       "checkin": "2025-11-27 10:35:00"
   }
   ```

2. **BOT_Trans Collection** (Transaction History)
   ```json
   {
       "trans_date": "2025-11-27 10:35:00",
       "action": "BUY",
       "price": 125.43,
       "buyprice": 125.43,
       "buydate": "2025-11-27 10:35:00",
       "botid": "BOT_001",
       "symbol": "TSLA",
       "orderid": "12345678",
       "status": "FILLED",
       "quantity": 5
   }
   ```

---

### 6.3 Bot State Updates

**Checkin Mechanism (Heartbeat):**
```python
# Every 5 minutes, update checkin timestamp
checkintime = datetime.now()
five_min_ago = checkintime - timedelta(seconds=300)

if bot.last_checkin < five_min_ago:
    result = bot.db['BOT_SETUP'].update_one(
        {'BOT_ID': bot.attribs[0].get('BOT_ID')},
        {"$set": {"checkin": checkintime}}
    )
    bot.last_checkin = checkintime
    bot.tdsession = TDSession  # Reset session
    bot.save(bot.attribs[0].get('BOT_ID'))  # Persist state
    bot.setup(bot.attribs[0].get('BOT_ID'))  # Reload config
```

**Persistence (`save()` method):**
```python
def save(self, bot_id):
    fields = {
        'prices': self.prices,
        'dates': self.dates
    }
    doc = {"$set": fields}
    filt = {'BOT_ID': bot_id}
    response = self.db['BOT_SETUP'].update_one(filt, doc)
```

---

## 7. Risk Management & Position Sizing

### 7.1 Position Limits

**Location:** Bot configuration (MongoDB BOT_SETUP)

```python
# Maximum concurrent positions
self.MAX_ORDERS = 5  # Can hold up to 5 buy orders

# Position size controls
self.BUY_QTY = 5              # For TDA: quantity per order
self.SELL_QTY = 5             # For TDA: quantity per order
self.BUY_AMT = 500            # For Alpaca: dollar amount per buy
self.SELL_AMT = 525           # For Alpaca: dollar amount per sell
```

---

### 7.2 Position Queue Management

**Location:** Both bot implementations

```python
def analyze_entry(self, current_price):
    # Only buy if not at max position
    if len(self.prices) < self.MAX_ORDERS:
        # ... buy logic
    else:
        self.log.debug(f"Already in position for {len(self.prices)} orders")

def addBuyTrade(self, dates, prices, date, price):
    # FIFO removal when max reached
    if len(dates) > self.MAX_ORDERS:
        dates.pop(0)
        prices.pop(0)
    
    dates.append(date)
    prices.append(price)
    return True

def removeBuyTrade(self, dates, prices, date):
    # Remove specific trade when sold
    for i in range(len(dates)):
        if dates[i] == date:
            dates.pop(i)
            price = prices[i]
            prices.pop(i)
            return price
    return 0
```

---

### 7.3 Cash Flow Controls

**Pre-trade Cash Check:**
```python
# TD Ameritrade
acct = self.tdsession.get_accounts(self.accountno)
usdbal = float(acct['securitiesAccount']['currentBalances']['cashBalance'])

if usdbal < self.BUY_QTY * current_price:
    good_buy = False
    self.log.info(f"Buy signal, but not enough cash {usdbal}")

# Alpaca
details = self.session.get_account()
usdbal = float(details.cash)

if usdbal < self.BUY_AMT:
    good_buy = False
    self.log.info(f"Buy signal, but not enough cash {usdbal}")
```

---

### 7.4 Pattern Day Trader (PDT) Protection

**Location:** `alpaca_autotrade.py`, `analyze_exit()` method

```python
# PDT Rule: Avoid round-trip trades (buy & sell same day)
for i in range(len(self.dates)):
    prev_buy = self.prices[i]
    
    pdt_allowed = True  # Currently disabled
    trigger_roundtrip = False
    
    if datetime.now().day != max(self.dates).day:
        trigger_roundtrip = True  # Different day = allowed
    
    if pdt_allowed or not trigger_roundtrip:
        if current_price > min_to_sell:
            # Proceed with sell
```

---

### 7.5 Sell-Only Symbols (TDA)

**Location:** `td_autotrade.py`, `analyze_entry()`, lines ~228-234

```python
sell_only = [
    'APXT', 'BABA', 'CCL', 'MRNA', 'NVAX', 'DDD', 'ROOT', 
    'PLTR', 'NIO', 'INO', 'ONVO', 'NKLA', 'PTON', 'ROKU', 
    'SNDL', 'NCLH', 'NMTC', 'DT', 'RKT', 'DOCU', 'FUBO', 
    'RUN', 'DIDI', 'GOEV', 'RCL', 'PFE', 'BNTX', 'BAC'
]

if self.symbol.upper() in sell_only:
    good_buy = False
    self.log.info(f"{self.symbol} Sell Only not buying")
```

---

### 7.6 Sudden Jump Detection

**Location:** Both implementations

```python
def sudden_jump(symbol, current_price):
    spike = False  # Currently disabled (placeholder for future logic)
    # Check last day's close price or last few hours price here...
    return spike
```

**Intended Logic:** Monitor for > 5% gap moves to prevent buying into spikes.

---

## 8. Backtesting Approaches

**Status:** **NOT IMPLEMENTED** in current codebase

**Observations:**
- No backtesting module found
- No historical data replay mechanism
- Functions like `get_indicators()` and `buy_sell()` are defined but not actively used
- Appears to be paper trading capability only through broker APIs
- Daily profit reporting exists but post-trade only

**Recommendations for Implementation:**
1. Create offline OHLCV data loader
2. Simulate indicator calculations on historical data
3. Implement order matching engine with realistic slippage
4. Track P&L with transaction costs
5. Generate performance statistics (Sharpe, Sortino, max drawdown)

---

## 9. Data Caching & Storage Strategies

### 9.1 In-Memory Caching (Per-Session)

**Historical Price Storage:**
```python
closes[symbol] = {
    'close': [...],    # Unlimited array (grows with session)
    'high': [...],
    'low': [...],
    'volume': [...],
    'datetime': [...]
}

bots[symbol]['prices'] = [125.23, 124.50, 123.75]
bots[symbol]['dates'] = [datetime, datetime, datetime]
```

**Size Management:** 
- No automatic cleanup
- Arrays grow indefinitely during session
- Cleared on restart

---

### 9.2 MongoDB Persistence

**Strategy:** 
- Save **prices** and **dates** arrays every 5 minutes (checkin)
- Persist trade transactions for historical analysis
- Retrieve on bot initialization for state recovery

**Collections:**
```
tdameritrade (Live Account)
├── BOT_SETUP (current configuration + positions)
└── BOT_Trans (all trades)

TDABot (Taxable Account)
├── BOT_SETUP
└── BOT_Trans

Alpaca
├── BOT_SETUP
└── BOT_Trans

ODS (Operations)
└── whatsapp (notification queue - unused)
```

---

### 9.3 Polygon Data API (alpaca_dashboard.py)

**Historical Data Retrieval:**
```python
def getHistory(self, symbol, multiplier, timeframe, fromdate, todate):
    return self.api.polygon.historic_agg_v2(
        symbol, multiplier, timeframe, fromdate, todate
    ).df

def getMinutesHistory(self, symbol, minutes):
    return self.api.polygon.historic_agg(
        size="minute", symbol=symbol, limit=minutes
    ).df
```

**Timeframes Supported:**
- Minute (real-time ticks)
- 5-minute (backtesting)
- 15-minute (backtesting)
- Daily (backtesting)

---

## 10. Key Functions Reference

### Core Trading Functions

| Function | File | Lines | Purpose |
|----------|------|-------|---------|
| `f()` | tda_bot.py | ~240-450 | Main callback for streaming data |
| `tda_trade()` | tda_bot.py | ~466-490 | Route trades to TDA bots |
| `alpaca_trade()` | tda_bot.py | ~492-510 | Route trades to Alpaca bots |
| `robinhood_trade()` | tda_bot.py | ~512-530 | Route trades to RH bots |
| `tda_taxable_trade()` | tda_bot.py | ~452-464 | Route trades to taxable account |

### Indicator Functions

| Function | File | Purpose |
|----------|------|---------|
| `get_indicators()` | tda_bot.py | Calculate RSI, MACD, MA, engulfing |
| `buy_sell_rsi()` | tda_bot.py | RSI-based signal generation |
| `buy_sell()` | tda_bot.py | MACD-based signal generation |

### Bot Analysis Functions

| Function | Class | Purpose |
|----------|-------|---------|
| `analyze_entry_exit()` | JadhavBot / AlpacaBot | Main trading logic orchestrator |
| `analyze_entry()` | JadhavBot / AlpacaBot | Entry condition evaluation |
| `analyze_exit()` | JadhavBot / AlpacaBot | Exit condition evaluation |

### Order Execution Functions

| Function | Class | Purpose |
|----------|-------|---------|
| `tda_api()` | JadhavBot | TD Ameritrade order placement |
| `alpaca_api()` | AlpacaBot | Alpaca order placement |
| `save_order()` | Both | Persist order to MongoDB |

### Notification Functions

| Function | Purpose |
|----------|---------|
| `worker()` | Process queue and send Telegram messages |
| `dailyReport()` | Calculate and send daily P&L |
| `sendText()` | Send SMS via AppleScript |

### Dashboard Functions

| Class | File | Purpose |
|-------|------|---------|
| `Portfolio` | alpaca_dashboard.py | Portfolio management & data retrieval |
| `StreamingData` | alpaca_dashboard.py | Real-time data streaming handler |
| `MinuteHistory` | alpaca_dashboard.py | Historical minute data loader |
| `WatchLists` | alpaca_dashboard.py | Watchlist persistence (pickle) |
| `Env` | alpaca_dashboard.py | Environment setup (Live/Paper) |

---

## 11. Trading Strategy Details

### 11.1 Strategy Overview

**Type:** Mean reversion + momentum hybrid

**Primary Indicators:**
1. **RSI (Relative Strength Index)** - Momentum/Overbought-Oversold
2. **MACD** - Trend confirmation (available but not primary)
3. **Price action** - Threshold-based entry/exit

---

### 11.2 Entry Strategy

**Conditions (ALL must be true):**
1. RSI < RSI_OVERSOLD (default: 30)
2. Position queue not full (len < MAX_ORDERS)
3. Price check:
   - Initial: Always buy
   - Subsequent: Price must be ≥ BUY_THRESHOLD% cheaper than min
4. Cooldown check: Last buy > Duration minutes ago
5. No recent spike (> 5% gap from prior close)
6. Sufficient cash for order
7. Symbol not in sell_only list (TDA only)

**Result:** 
- Add to `prices[]` and `dates[]`
- Place market order
- Send Telegram notification
- Save to MongoDB

---

### 11.3 Exit Strategy

**Conditions (ANY can trigger exit):**
1. RSI > RSI_OVERBOUGHT (default: 70) - Technical exit
2. Price > SELL_THRESHOLD% above buy price - Profit target
3. Different day than buy (PDT rule)

**Logic:**
- For each held position, check if profit target reached
- If yes, place sell market order
- Remove from `prices[]` and `dates[]`
- Send Telegram notification
- Save to MongoDB

---

### 11.4 Position Management

**Queue Behavior:**
- **MAX_ORDERS:** Configurable limit (default: 5)
- **FIFO:** New entries append, oldest removed if limit exceeded
- **Buy/Sell Pairs:** Matched by timestamp

**Pyramid/Scale-in:**
- Each buy adds to the position
- Sell prices adjust based on min cost (lowest buy price)
- All positions target same profit threshold

---

### 11.5 Dynamic Threshold Adjustment (TDA only)

**Location:** `td_autotrade.py`, `analyze_entry_exit()`, lines ~192-207

```python
if self.bump_up:
    bump_up = self.bump_up
else:
    bump_up = 0

if bump_up > 0:
    blen = len(self.prices) + 1
    slen = blen - 1
    
    # Increase thresholds as position grows
    if len(self.prices) > 0:
        self.BUY_THRESHOLD = bump_up * blen   # Each buy bumps threshold
        self.SELL_THRESHOLD = (bump_up * slen) + bump_up
    else:
        self.BUY_THRESHOLD = bump_up
        self.SELL_THRESHOLD = bump_up * 2
```

**Effect:** 
- Wider spreads required as position size grows
- Reduces exit frequency on volatile days
- Encourages larger winners

---

## 12. Architecture Patterns Used

### 12.1 Design Patterns

| Pattern | Usage | Location |
|---------|-------|----------|
| **State Pattern** | Bot configuration state | MongoDB BOT_SETUP |
| **Observer** | Qt Signals for UI updates | alpaca_dashboard.py |
| **Producer-Consumer** | Notification queue | `q = queue.Queue()` |
| **Strategy Pattern** | Broker-specific order execution | JadhavBot vs AlpacaBot classes |
| **Singleton** | MongoDB client connection | Global `client = MongoClient()` |
| **Callback** | Streaming data handler | `f()` function |
| **Template Method** | Common bot interface | analyze_entry_exit() |

---

### 12.2 Multi-Threading Model

```python
# Main thread: Streaming and signal generation
TDStreamingClient.stream()  # Blocking call with callbacks

# Worker thread: Notification queue processor
threading.Thread(target=worker, daemon=True)

# Analysis threads: Per-signal analysis
threading.Thread(target=bot.analyze_entry_exit(), args=())

# Dashboard threads: UI rendering
MinuteHistoryThread (QThread)
WatchListSelectorThread (QThread)
ScannerSelectorThread (QThread)
PortfolioThread (QThread)
```

---

### 12.3 Broker Abstraction

**Common Interface:**
```
┌─────────────────┐
│  BaseBot (abstract) │
├─────────────────┤
│ + setup()       │
│ + save()        │
│ + analyze_*()   │
│ + *_api()       │
└─────────────────┘
        △
        │
    ┌───┴────┬─────────┬──────────┐
    │        │         │          │
JadhavBot  AlpacaBot  RHBot    (Others)
```

**Implementation Differences:**
- **Order types:** Market (all) vs Limit (Alpaca)
- **Position sizing:** Quantity (TDA/RH) vs Notional (Alpaca)
- **Fractionals:** Not supported (TDA/RH) vs Supported (Alpaca)
- **Account types:** Multiple (TDA) vs Single (Alpaca)

---

## 13. Data Flow Diagrams (Text Format)

### 13.1 Real-Time Trading Flow

```
TD Ameritrade WebSocket
         ↓
   [Streaming Data Event]
         ↓
  f(symbol, data, candle_closed)
         ↓
  Is candle_closed? NO → return
         ↓
         YES
         ↓
  Initialize/Update bots[symbol] state
         ↓
  Append OHLCV to closes[symbol]
         ↓
  Check RSI_PERIOD threshold met?
         ↓
  Calculate: RSI, MACD, MA indicators
         ↓
  Check checkin (5-min heartbeat)
         ↓
  For each bot with matching symbol:
      ├─ Spawn thread
      ├─ Call analyze_entry_exit(rsi, price)
      ├─ Determine action: BUY/SELL/HOLD
      ├─ If action: Call *_api()
      ├─ Store order in MongoDB
      └─ Queue notification message
         ↓
  Log metrics to console/file
```

### 13.2 Order Placement Flow

```
analyze_entry() OR analyze_exit()
         ↓
  Validate all conditions
         ↓
  good_buy = true?
         ↓
  NO: Log reason, return
  YES: Proceed
         ↓
  {BUY}
    ├─ tda_api('BUY', price, None, None)
    │  ├─ Build TDA order JSON
    │  ├─ Place via tdsession.place_order()
    │  ├─ Retrieve order status
    │  └─ Return filled price
    ├─ addBuyTrade(dates, prices, now, price)
    ├─ send to queue: "BOT_ID:BUY @price {len}"
    └─ save() to MongoDB
         ↓
  {SELL}
    ├─ For each held position:
    │  ├─ tda_api('SELL', price, buyprice, buydate)
    │  ├─ Build TDA order JSON
    │  ├─ Place via tdsession.place_order()
    │  └─ Return filled price
    ├─ removeBuyTrade(dates, prices, date)
    ├─ send to queue: "BOT_ID:SELL price {len}"
    └─ save() to MongoDB
         ↓
  Queue message consumed by worker thread
         ↓
  telegram_send.send(messages=[msg])
```

### 13.3 MongoDB State Synchronization

```
Bot Startup
    ↓
bot.setup(BOT_ID)
    ├─ Query BOT_SETUP collection
    ├─ Load all attributes (BUY_QTY, SELL_QTY, etc.)
    ├─ Load prices[] and dates[] arrays
    └─ Set instance variables via __setattr__
    ↓
Every 5 minutes (checkin)
    ├─ Update timestamp in BOT_SETUP
    ├─ Reset TDSession (token refresh)
    ├─ bot.save(BOT_ID) → persist prices/dates
    └─ bot.setup(BOT_ID) → reload any manual changes
    ↓
Order executed
    ├─ save_order() → insert into BOT_Trans
    ├─ addBuyTrade() / removeBuyTrade() → update arrays
    └─ bot.save() → persist updated prices/dates
    ↓
Shutdown
    └─ Final bot.save() for cleanly persisted state
```

---

## 14. Summary Statistics

### Code Metrics

| File | Lines | Classes | Functions | Purpose |
|------|-------|---------|-----------|---------|
| tda_bot.py | 920 | 0 | 13 | Main orchestrator |
| td_autotrade.py | 433 | 1 | 10 | TDA bot implementation |
| alpaca_autotrade.py | 434 | 1 | 10 | Alpaca bot implementation |
| telgram_test.py | 2 | 0 | 1 | Telegram test |
| alpaca_dashboard.py | 1823 | 12 | 80+ | Dashboard UI & data |
| **TOTAL** | **~3,612** | **13** | **110+** | |

### Key Metrics

- **Supported Brokers:** 3 (TD Ameritrade, Alpaca, Robinhood)
- **Account Types:** 4 (Regular TDA, Taxable TDA, Alpaca, Robinhood)
- **Indicators:** 3 active (RSI, MACD, MA) + patterns
- **Order Types:** MARKET (all brokers)
- **Threading Model:** Multi-threaded (streaming + workers + analysis)
- **Database:** MongoDB (4+ collections)
- **Notifications:** Telegram + SMS/WhatsApp
- **Dashboard:** PySide2/Qt with real-time charting

---

## 15. Important Configuration Keys (BOT_SETUP)

```json
{
  "BOT_ID": "unique_identifier",
  "symbol": "TICKER",
  "Active": true,
  "Trade": true,                    // True = live, False = test
  "Take_Profit": true,              // Enable profit-taking
  
  "BUY_QTY": 5,                     // TDA quantity per order
  "SELL_QTY": 5,
  "BUY_AMT": 500.0,                 // Alpaca dollar amount
  "SELL_AMT": 525.0,
  
  "BUY_THRESHOLD": 0.03,            // 3% cheaper required
  "SELL_THRESHOLD": 0.05,           // 5% profit target
  
  "RSI_OVERSOLD": 30,               // Buy threshold
  "RSI_OVERBOUGHT": 70,             // Sell threshold
  
  "MAX_ORDERS": 5,                  // Max concurrent positions
  "Duration": 30,                   // Cooldown minutes
  "bump_up": 0,                     // Dynamic threshold adjustment
  
  "prices": [],                     // Held positions
  "dates": [],                      // Hold timestamps
  "checkin": ""                     // Last heartbeat
}
```

---

## 16. Critical Dependencies

```python
# Core Trading
import talib                    # Technical indicators (RSI, MACD)
from tda import auth, client    # TD Ameritrade API
import alpaca_trade_api         # Alpaca Broker API
import robin_stocks as rs       # Robinhood API

# Data Management
from pymongo import MongoClient # State persistence
import pandas as df             # Data manipulation
import numpy                    # Numerical computing

# Notifications
import telegram_send            # Telegram messaging

# Streaming
from tda.streaming import StreamingClient  # TDA WebSocket

# Dashboard
from PySide2.QtCore import *    # Qt framework
from PySide2.QtCharts import *  # Charting

# Utilities
from datetime import datetime, timedelta
from pytz import timezone
import threading
import queue
```

---

## 17. Known Limitations & TODOs

### Limitations
1. ❌ No backtesting framework
2. ❌ Candlestick patterns loaded but unused
3. ❌ `sudden_jump()` not implemented (always False)
4. ❌ MACD signals not actively used
5. ❌ No stop-loss orders
6. ❌ PDT check currently disabled in Alpaca
7. ❌ No position averaging down logic
8. ❌ No trailing stops

### TODOs in Code
```python
# Line 148 (tda_bot.py): TDA API call
# TODO        

# Line 152 (alpaca_autotrade.py): Sudden spike check
spike = False    # False for now until we put business logic
# Check last day's close price or last few hours price here...
```

---

## 18. Conclusion

The TDA Bot is a **sophisticated multi-broker trading system** leveraging:

✅ **Technical Analysis:** RSI-based mean reversion strategy  
✅ **Risk Management:** Position sizing, PDT prevention, cash checks  
✅ **State Persistence:** MongoDB for recovery and audit trail  
✅ **Real-Time Streaming:** TD Ameritrade WebSocket integration  
✅ **Broker Abstraction:** Unified interface across 3 brokers  
✅ **Notifications:** Telegram alerts for all trade activity  
✅ **Visualization:** Live dashboard with charting  

**Recommended Enhancements:**
1. Implement historical backtesting engine
2. Add stop-loss order logic
3. Enable MACD as confirmation signal
4. Implement position averaging
5. Add P&L analytics and statistics
6. Create risk-reward ratio validation
7. Add market regime detection

