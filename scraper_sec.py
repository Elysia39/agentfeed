import os
import json
import requests

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
from paths import SOURCES_FILE
CIK_CACHE_FILE = os.path.join(CURRENT_DIR, "sec_cik_cache.json")
UA = "DailyIntelBriefApp (research_admin@domain.com)"

# Common Pre-seeded CIKs
STATIC_TICKER_CIK = {
    "NVDA": "0001045810",
    "AAPL": "0000320193",
    "MSFT": "0000789019",
    "TSLA": "0001318605",
    "GOOGL": "0001652044",
    "GOOG": "0001652044",
    "AMZN": "0001018724",
    "META": "0001326801",
    "TSM": "0001046179",
    "BABA": "0001577552",
    "PLTR": "0001321655",
    "ARM": "0001973239",
    "AMD": "0000002488",
    "SMCI": "0001375365",
    "COIN": "0001679788",
    "ASML": "0000937966"
}

def load_cik_map():
    if os.path.exists(CIK_CACHE_FILE):
        try:
            with open(CIK_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return STATIC_TICKER_CIK

def get_cik_for_ticker(ticker):
    ticker = ticker.upper().strip()
    cik_map = load_cik_map()
    if ticker in cik_map:
        return str(cik_map[ticker]).zfill(10)
    
    # Try fetching official SEC company_tickers.json
    try:
        url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": UA, "Accept": "application/json"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            new_map = {}
            for item in data.values():
                t = item.get("ticker", "").upper()
                c = str(item.get("cik_str", "")).zfill(10)
                if t and c:
                    new_map[t] = c
            with open(CIK_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(new_map, f)
            return new_map.get(ticker)
    except Exception as e:
        print(f"⚠️ CIK lookup error: {e}")
    return None

def fetch_sec_filings_for_ticker(ticker, target_forms=None, limit=3):
    if not target_forms:
        target_forms = ["8-K", "10-Q", "10-K", "4", "13F-HR", "6-K"]
    
    cik = get_cik_for_ticker(ticker)
    if not cik:
        return []
    
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    headers = {"User-Agent": UA, "Accept": "application/json"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return []
        
        data = resp.json()
        recent = data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        accession_nums = recent.get("accessionNumber", [])
        primary_docs = recent.get("primaryDocument", [])
        doc_descs = recent.get("primaryDocDescription", [])
        
        results = []
        for i in range(min(20, len(forms))):
            form = forms[i]
            if form in target_forms or not target_forms:
                fdate = filing_dates[i]
                acc_num = accession_nums[i].replace("-", "")
                doc_name = primary_docs[i]
                desc = doc_descs[i] if i < len(doc_descs) else ""
                
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_num}/{doc_name}"
                results.append({
                    "ticker": ticker.upper(),
                    "form": form,
                    "date": fdate,
                    "description": desc or f"{ticker} {form} 官方披露",
                    "url": filing_url
                })
                if len(results) >= limit:
                    break
        return results
    except Exception as e:
        print(f"⚠️ SEC Fetch error for {ticker}: {e}")
        return []

def fetch_all_sec_filings(tickers=None, target_forms=None):
    if tickers is None:
        if os.path.exists(SOURCES_FILE):
            try:
                with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                    sdata = json.load(f)
                    sec_cfg = sdata.get("sec_filings", {})
                    tickers = sec_cfg.get("tickers", ["NVDA", "TSLA", "AAPL"])
                    target_forms = sec_cfg.get("target_forms", ["8-K", "10-Q", "4"])
            except Exception:
                pass
        if not tickers:
            tickers = ["NVDA", "TSLA", "AAPL"]
    
    all_filings = []
    for t in tickers:
        filings = fetch_sec_filings_for_ticker(t, target_forms=target_forms, limit=3)
        all_filings.extend(filings)
    return all_filings

if __name__ == "__main__":
    res = fetch_sec_filings_for_ticker("PLTR", ["8-K", "10-Q", "4"])
    print(f"PLTR Filings: {res}")
