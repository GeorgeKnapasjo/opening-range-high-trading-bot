import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# -----------------------------
# CONFIGURATION
# -----------------------------
CSV_FILE = "premarket_gainers1.csv"  # Path to your CSV file
ORB_MINUTES = [1, 3, 5, 15]      # Opening Range Breakout timeframes to test
TARGET_PCT = 0.1                # 8% target profit
STOP_PCT = 0.05                  # 4% stop loss
DATA_INTERVAL = "1m"              # Intraday interval from yfinance

# -----------------------------
# FUNCTION: Get intraday data
# -----------------------------
def get_intraday_data(ticker, date):
    """
    Download intraday historical data for a specific ticker and date.
    Uses yfinance to pull 1-minute data for the given date.
    """
    start_dt = datetime.strptime(date, "%Y-%m-%d")
    end_dt = start_dt + timedelta(days=1)
    
    df = yf.download(
        ticker,
        start=start_dt.strftime("%Y-%m-%d"),
        end=end_dt.strftime("%Y-%m-%d"),
        interval=DATA_INTERVAL,
        progress=False
    )

    # Make sure timezone-naive
    df.index = df.index.tz_localize(None)
    return df

# -----------------------------
# FUNCTION: Test ORB strategy
# -----------------------------
def test_orb(df, orb_minutes):
    """
    Test Opening Range Breakout strategy for a given dataframe and time range.
    """
    # Define market open time (UTC 13:30)
    market_open = datetime(df.index[0].year, df.index[0].month, df.index[0].day, 13, 30)
    
    # Slice first N minutes for the opening range
    orb_end = market_open + timedelta(minutes=orb_minutes)
    opening_range = df[(df.index >= market_open) & (df.index < orb_end)]
    
    if opening_range.empty:
        return None
    
    # Determine breakout level
    high = opening_range['High'].max()
    low = opening_range['Low'].min()
    
    # Entry = breakout above high
    after_orb = df[df.index >= orb_end]
    entry_triggered = False
    entry_price = None
    
    for time, row in after_orb.iterrows():
        if not entry_triggered and (row['High'] > high).any():
            entry_price = high
            entry_triggered = True
        
        if entry_triggered:
            # Check target
            if (row['High'] >= entry_price * (1 + TARGET_PCT)).any():
                return True  # Win
            # Check stop
            if (row['Low'] <= entry_price * (1 - STOP_PCT)).any():
                return False  # Loss
    
    return False if entry_triggered else None  # No trade if breakout never happened

# -----------------------------
# MAIN BACKTEST LOOP
# -----------------------------
def run_backtest():
    # Load premarket CSV
    premarket_data = pd.read_csv(CSV_FILE)

    # filter over 25% pre market move
    premarket_data = premarket_data[premarket_data['premarket_change'] > 0.25]
    
    results = {m: {"wins": 0, "losses": 0, "no_trade": 0, "ballance": 10000} for m in ORB_MINUTES}
    
    for _, row in premarket_data.iterrows():
        date = row['date']
        ticker = row['ticker']
        
        # try:
        df = get_intraday_data(ticker, date)
        print(f'returning {df} for P')
        if df.empty:
            continue
        
        for m in ORB_MINUTES:
            outcome = test_orb(df, m)
            if outcome is True:
                results[m]["wins"] += 1
                results[m]["ballance"] = results[m]["ballance"] * (1 + TARGET_PCT)
            elif outcome is False:
                results[m]["losses"] += 1
                results[m]["ballance"] = results[m]["ballance"] * (1 - STOP_PCT)
            else:
                results[m]["no_trade"] += 1
                    
        # except Exception as e:
            # print(f"Error fetching data for {ticker} on {date}: {e}")
    
    # Print win rate summary
    print("\n=== Backtest Results ===")
    for m in ORB_MINUTES:
        wins = results[m]["wins"]
        losses = results[m]["losses"]
        total_trades = wins + losses
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        ballance = results[m]["ballance"]
        print(f"{m}-min ORB → Trades: {total_trades}, Wins: {wins}, Losses: {losses}, Win rate: {win_rate:.2f}%, balance at end = {ballance}")

if __name__ == "__main__":
    run_backtest()


# 1% stop 5% tp
# 1-min ORB → Trades: 36, Wins: 15, Losses: 21, Win rate: 41.67%, balance at end = 16833.660828998687
# 3-min ORB → Trades: 29, Wins: 12, Losses: 17, Win rate: 41.38%, balance at end = 15138.04866315821
# 5-min ORB → Trades: 27, Wins: 6, Losses: 21, Win rate: 22.22%, balance at end = 10851.127862958832
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 9293.448707057792

# 2% stop 5% tp
# 1-min ORB → Trades: 36, Wins: 17, Losses: 19, Win rate: 47.22%, balance at end = 15613.976534415011
# 3-min ORB → Trades: 29, Wins: 13, Losses: 16, Win rate: 44.83%, balance at end = 13648.285510507527
# 5-min ORB → Trades: 27, Wins: 6, Losses: 21, Win rate: 22.22%, balance at end = 8767.653619435901
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 7820.27247214162

# 1% stop 6% tp
# 1-min ORB → Trades: 36, Wins: 12, Losses: 24, Win rate: 33.33%, balance at end = 15809.387829306012
# 3-min ORB → Trades: 29, Wins: 6, Losses: 23, Win rate: 20.69%, balance at end = 11257.5702910788
# 5-min ORB → Trades: 27, Wins: 2, Losses: 25, Win rate: 7.41%, balance at end = 8739.600794208816
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 9471.309720861806

# 2% stop 6% tp
# 1-min ORB → Trades: 36, Wins: 15, Losses: 21, Win rate: 41.67%, balance at end = 15679.621273985722
# 3-min ORB → Trades: 29, Wins: 8, Losses: 21, Win rate: 27.59%, balance at end = 10427.84366716832
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 7334.042332676961
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 7969.939364805735

# 1% stop 7% tp
# 1-min ORB → Trades: 36, Wins: 9, Losses: 27, Win rate: 25.00%, balance at end = 14015.359862128198
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 11019.54236162324
# 5-min ORB → Trades: 27, Wins: 2, Losses: 25, Win rate: 7.41%, balance at end = 8905.276743760833
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 9650.856621052579

# 2% stop 7% tp
# 1-min ORB → Trades: 36, Wins: 12, Losses: 24, Win rate: 33.33%, balance at end = 13868.552945332114
# 3-min ORB → Trades: 30, Wins: 6, Losses: 24, Win rate: 20.00%, balance at end = 9241.202410709648
# 5-min ORB → Trades: 28, Wins: 3, Losses: 25, Win rate: 10.71%, balance at end = 7392.70242962529
# 15-min ORB → Trades: 20, Wins: 2, Losses: 18, Win rate: 10.00%, balance at end = 7958.6044029821705

# 3% stop 7% tp
# 1-min ORB → Trades: 36, Wins: 13, Losses: 23, Win rate: 36.11%, balance at end = 11960.215311633026
# 3-min ORB → Trades: 29, Wins: 8, Losses: 21, Win rate: 27.59%, balance at end = 9063.097269468908
# 5-min ORB → Trades: 27, Wins: 4, Losses: 23, Win rate: 14.81%, balance at end = 6505.564676568782
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 7524.871383988889

# 1% stop 8% tp
# 1-min ORB → Trades: 36, Wins: 8, Losses: 28, Win rate: 22.22%, balance at end = 13969.32728967612
# 3-min ORB → Trades: 29, Wins: 4, Losses: 25, Win rate: 13.79%, balance at end = 10582.173723147318
# 5-min ORB → Trades: 27, Wins: 2, Losses: 25, Win rate: 7.41%, balance at end = 9072.508336031648
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 9832.089407630121

# 2% stop 8% tp
# 1-min ORB → Trades: 36, Wins: 10, Losses: 26, Win rate: 27.78%, balance at end = 12767.783882902859
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 9047.83337574141
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 7757.058792645243
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 8273.529080731054

# 3% stop 8% tp
# 1-min ORB → Trades: 36, Wins: 10, Losses: 26, Win rate: 27.78%, balance at end = 9779.184633397232
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 7073.598408099517
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 6064.470514488614
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 7737.826983107869

# 4% stop 8% tp
# 1-min ORB → Trades: 36, Wins: 13, Losses: 23, Win rate: 36.11%, balance at end = 10635.237217869517
# 3-min ORB → Trades: 29, Wins: 6, Losses: 23, Win rate: 20.69%, balance at end = 6205.558767961242
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 4729.125718610912
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 6555.5780903745135

# 5% stop 8% tp
# 1-min ORB → Trades: 36, Wins: 14, Losses: 22, Win rate: 38.89%, balance at end = 9502.80665530257
# 3-min ORB → Trades: 29, Wins: 7, Losses: 22, Win rate: 24.14%, balance at end = 5544.7964114021315
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 3678.220778278439
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 5544.32846020653

# 1% stop 9% tp
# 1-min ORB → Trades: 36, Wins: 5, Losses: 31, Win rate: 13.89%, balance at end = 11267.395068042462
# 3-min ORB → Trades: 29, Wins: 4, Losses: 25, Win rate: 13.79%, balance at end = 10979.583267930362
# 5-min ORB → Trades: 27, Wins: 2, Losses: 25, Win rate: 7.41%, balance at end = 9241.295571021266
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 10015.008080594436

# 2% stop 9% tp
# 1-min ORB → Trades: 36, Wins: 7, Losses: 29, Win rate: 19.44%, balance at end = 10175.170159420008
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 9474.543767092515
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 7974.533934090154
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 8427.451903992256

# 3% stop 9% tp
# 1-min ORB → Trades: 36, Wins: 7, Losses: 29, Win rate: 19.44%, balance at end = 7557.284629081565
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 7407.20069934787
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 6234.492634751171
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 7954.762945901283

# 5% stop 9% tp
# 1-min ORB → Trades: 36, Wins: 11, Losses: 25, Win rate: 30.56%, balance at end = 7157.833790399754
# 3-min ORB → Trades: 29, Wins: 7, Losses: 22, Win rate: 24.14%, balance at end = 5914.319771084464
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 3781.3425420041617
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 5699.767995774273

# 1% stop 10% tp
# 1-min ORB → Trades: 36, Wins: 5, Losses: 31, Win rate: 13.89%, balance at end = 11793.818998621042
# 3-min ORB → Trades: 29, Wins: 4, Losses: 25, Win rate: 13.79%, balance at end = 11388.082522962908
# 5-min ORB → Trades: 27, Wins: 2, Losses: 25, Win rate: 7.41%, balance at end = 9411.638448729676
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 10199.612639945512

# 2% stop 10% tp
# 1-min ORB → Trades: 36, Wins: 7, Losses: 29, Win rate: 19.44%, balance at end = 10846.883887371594
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 9917.20389751236
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 8196.036278935835
# 15-min ORB → Trades: 19, Wins: 2, Losses: 17, Win rate: 10.53%, balance at end = 8582.793370785814

# 3% stop 10% tp
# 1-min ORB → Trades: 36, Wins: 7, Losses: 29, Win rate: 19.44%, balance at end = 8056.178677226012
# 3-min ORB → Trades: 29, Wins: 5, Losses: 24, Win rate: 17.24%, balance at end = 7753.2725006105
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 6407.66322364504
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 8175.716127588347

# 4% stop 10% tp
# 1-min ORB → Trades: 36, Wins: 11, Losses: 25, Win rate: 30.56%, balance at end = 10282.538936948076
# 3-min ORB → Trades: 30, Wins: 7, Losses: 23, Win rate: 23.33%, balance at end = 7620.56472357941
# 5-min ORB → Trades: 28, Wins: 3, Losses: 25, Win rate: 10.71%, balance at end = 4796.880301380223
# 15-min ORB → Trades: 20, Wins: 3, Losses: 17, Win rate: 15.00%, balance at end = 6649.500410218322

# 5% stop 10% tp
# 1-min ORB → Trades: 36, Wins: 11, Losses: 25, Win rate: 30.56%, balance at end = 7914.248251746258
# 3-min ORB → Trades: 29, Wins: 7, Losses: 22, Win rate: 24.14%, balance at end = 6304.753515138863
# 5-min ORB → Trades: 27, Wins: 3, Losses: 24, Win rate: 11.11%, balance at end = 3886.3739139490604
# 15-min ORB → Trades: 19, Wins: 3, Losses: 16, Win rate: 15.79%, balance at end = 5858.085959754999