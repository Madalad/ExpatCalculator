"""Live currency exchange rates with a hardcoded fallback."""
import json
import urllib.request

_FALLBACK_CURRENCY_TO_USD = {
    "USD": 1.0,
    "GBP": 1.266,
}

def fetch_currency_rates(timeout: int = 5) -> dict:
    """Fetch live rates from open.er-api.com (free, no API key, 160+ currencies).
    Returns {currency_code: usd_value}. Falls back to hardcoded rates on any failure."""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
        if data.get("result") != "success":
            return _FALLBACK_CURRENCY_TO_USD.copy()
        # API gives USD→other; invert to get other→USD
        return {code: 1.0 / rate for code, rate in data["rates"].items() if rate > 0}
    except Exception:
        return _FALLBACK_CURRENCY_TO_USD.copy()
