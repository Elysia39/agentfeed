import os
import json

try:
    import yfinance as yf
except ImportError:
    yf = None

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE

DEFAULT_MACRO_LIST = [
    { "id": "m-1", "name": "美债 10 年期收益率", "symbol": "^TNX", "unit": "%", "enabled": True },
    { "id": "m-2", "name": "美债 2 年期收益率", "symbol": "2YY=F", "unit": "%", "enabled": True },
    { "id": "m-3", "name": "美元指数 (DXY)", "symbol": "DX-Y.NYB", "unit": "", "enabled": True },
    { "id": "m-4", "name": "伦敦现货黄金", "symbol": "GC=F", "unit": "$", "enabled": True },
    { "id": "m-5", "name": "WTI 纽约原油", "symbol": "CL=F", "unit": "$", "enabled": True },
    { "id": "m-6", "name": "美股恐慌指数 (VIX)", "symbol": "^VIX", "unit": "", "enabled": True },
    { "id": "m-7", "name": "离岸人民币 (USD/CNH)", "symbol": "USDCNH=X", "unit": "", "enabled": True },
    { "id": "m-8", "name": "比特币现货 (BTC)", "symbol": "BTC-USD", "unit": "$", "enabled": True }
]

def fetch_single_macro_indicator(item):
    sym = item.get("symbol", "").strip()
    name = item.get("name", sym)
    unit = item.get("unit", "")
    
    if yf is None:
        return {
            "name": name,
            "symbol": sym,
            "price": "--",
            "change_pct": "0.00%",
            "status": "up"
        }
    
    try:
        ticker = yf.Ticker(sym)
        fast_info = ticker.fast_info
        curr_price = fast_info.last_price
        prev_close = fast_info.previous_close or curr_price
        
        if curr_price is not None:
            chg = curr_price - prev_close
            pct_chg = (chg / prev_close * 100) if prev_close else 0
            
            if unit == "%":
                val_str = f"{curr_price:.2f}%"
                chg_str = f"{chg:+.2f}%"
            elif unit == "$":
                val_str = f"${curr_price:,.2f}" if curr_price < 1000 else f"${curr_price:,.0f}"
                chg_str = f"{pct_chg:+.2f}%"
            else:
                val_str = f"{curr_price:.2f}" if curr_price < 100 else f"{curr_price:,.2f}"
                chg_str = f"{pct_chg:+.2f}%"
                
            return {
                "name": name,
                "symbol": sym,
                "value": val_str,
                "change": chg_str,
                "status": "up" if chg > 0 else ("down" if chg < 0 else "flat"),
                "ok": True
            }
    except Exception as e:
        print(f"⚠️ yfinance fetch error for {sym}: {e}")
        
    return {
        "name": name,
        "symbol": sym,
        "value": "--",
        "change": "--",
        "status": "flat",
        "ok": False
    }

def fetch_macro_indicators(custom_list=None):
    if custom_list is None:
        if os.path.exists(SOURCES_FILE):
            try:
                with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                    custom_list = sdata.get("macro_indicators", DEFAULT_MACRO_LIST)
            except Exception:
                pass
    if not custom_list:
        custom_list = DEFAULT_MACRO_LIST

    results = []
    for item in custom_list:
        if item.get("enabled", True):
            quote = fetch_single_macro_indicator(item)
            if quote.get("ok"):
                results.append(quote)
    return results

if __name__ == "__main__":
    res = fetch_macro_indicators()
    print(f"Fetched {len(res)} Macro Indicators:")
    for r in res:
        print(f"  {r['name']} ({r['symbol']}): {r['value']} ({r['change']})")
