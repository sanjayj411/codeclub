#!/usr/bin/env bash
set -euo pipefail

ROOT="autotrade-scaffold"
if [ ! -d "$ROOT" ]; then
  echo "ERROR: Directory '$ROOT' not found in $(pwd)"
  exit 2
fi

echo "Checking project at: $ROOT"
echo

# expected top-level files and a subset of key src files
declare -a expected=(
  "docker-compose.yml"
  "Dockerfile"
  "requirements.txt"
  "README.md"
  "src/api/main.py"
  "src/api/routes.py"
  "src/core/config.py"
  "src/core/db.py"
  "src/core/logger.py"
  "src/brokers/mock_broker.py"
  "src/execution/order_manager.py"
  "src/execution/risk_manager.py"
  "src/strategies/ma_crossover.py"
  "src/strategies/runner.py"
  "src/workers/market_feeder.py"
  "tests/test_strategy.py"
  "tests/test_order_flow.py"
)

missing=()
echo "Verifying expected files..."
for f in "${expected[@]}"; do
  if [ -f "$ROOT/$f" ]; then
    size=$(stat -f%z "$ROOT/$f" 2>/dev/null || stat -c%s "$ROOT/$f" 2>/dev/null)
    echo "OK  - $f (size: ${size} bytes)"
  else
    echo "MISS - $f"
    missing+=("$f")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo
  echo "Missing files (${#missing[@]}):"
  for m in "${missing[@]}"; do
    echo "  - $m"
  done
else
  echo
  echo "All expected files present."
fi

# show tree summary
echo
echo "Project tree (top 4 levels):"
if command -v tree >/dev/null 2>&1; then
  tree -L 4 "$ROOT"
else
  find "$ROOT" -maxdepth 4 -type f | sed "s|^$ROOT/|  |" | sort
fi

# show first 30 lines of problematic files if missing any key files
if printf '%s\n' "${missing[@]}" | grep -E 'tests/' >/dev/null 2>&1; then
  echo
  echo "Creating minimal test files for missing tests..."
  mkdir -p "$ROOT/tests"
  if [[ " ${missing[*]} " == *" tests/test_strategy.py "* ]]; then
    cat > "$ROOT/tests/test_strategy.py" <<'PY'
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
    echo "Wrote $ROOT/tests/test_strategy.py"
  fi
  if [[ " ${missing[*]} " == *" tests/test_order_flow.py "* ]]; then
    cat > "$ROOT/tests/test_order_flow.py" <<'PY'
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
    echo "Wrote $ROOT/tests/test_order_flow.py"
  fi
fi

# attempt to run pytest if available
echo
if command -v pytest >/dev/null 2>&1; then
  echo "Running pytest -q in $ROOT ..."
  (cd "$ROOT" && pytest -q) || echo "pytest reported failures (exit code $?)"
else
  echo "pytest not found on PATH. To run tests install pytest (pip install pytest) and run:"
  echo "  cd $ROOT && pytest -q"
fi

echo
echo "Diagnostic complete."
