import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import schedule
import time
import re

URL = "https://www.tradingview.com/markets/stocks-usa/market-movers-pre-market-gainers/"
CSV_FILE = "premarket_gainers1.csv"

def normalize_volume(vol_str):
    """Convert volume string like '1.2M' into int"""
    vol_str = vol_str.replace(",", "").strip()
    if vol_str.endswith("M"):
        return int(float(vol_str[:-1]) * 1_000_000)
    elif vol_str.endswith("K"):
        return int(float(vol_str[:-1]) * 1_000)
    elif vol_str.isdigit():
        return int(vol_str)
    return None

def normalize_change(change_str):
    """Convert change string like '+35.12%' into float"""
    try:
        return float(change_str.strip('%+')) / 100.0
    except:
        return None

def split_ticker_name(text):
    """Split combined ticker + company name into separate fields"""
    match = re.match(r"^([A-Z\.]+)(.*)$", text.strip())
    if match:
        ticker = match.group(1).strip()
        name = match.group(2).strip()
        return ticker, name
    return text, ""  # fallback

def scrape_tradingview():
    print(f"[{datetime.now()}] Starting scrape...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                      " AppleWebKit/537.36 (KHTML, like Gecko)"
                      " Chrome/115.0 Safari/537.36"
    }

    response = requests.get(URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("tr.row-RdUXZpkv.listRow")  # table rows of gainers
    data = []
    date = datetime.now() - timedelta(days=1)
    formattedDate = date.strftime("%Y-%m-%d")

    for row in rows:
        try:
            cols = row.find_all("td")
            if len(cols) < 5:
                continue

            symbol_cell = cols[0]
            ticker = symbol_cell.find("a").get_text(strip=True)  # ticker is usually in an <a>
            company_name = symbol_cell.find("sup").get_text(strip=True)

            change = normalize_change(cols[1].get_text(strip=True))
            volume = normalize_volume(cols[4].get_text(strip=True))

            data.append({
                "date": formattedDate,
                "ticker": ticker,
                "company_name": company_name,
                "premarket_change": change,
                "premarket_volume": volume
            })
        except Exception as e:
            print(f"Row parse error: {e}")
            continue

    if not data:
        print("No data found.")
        return

    df = pd.DataFrame(data)

    try:
        old_df = pd.read_csv(CSV_FILE)
        df = pd.concat([old_df, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_csv(CSV_FILE, index=False)
    print(f"[{datetime.now()}] Saved {len(data)} rows to {CSV_FILE}")

def main():
    scrape_tradingview()
    # schedule.every().day.at("23:00").do(scrape_tradingview)
    # print("Scheduler started. Waiting for 23:00 daily job...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)

if __name__ == "__main__":
    main()