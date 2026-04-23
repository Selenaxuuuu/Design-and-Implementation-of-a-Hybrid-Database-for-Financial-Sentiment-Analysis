def sync_market_data(tickers):
    """
    Sync market prices for a rolling 30-day window.
    Enhanced to fetch real metadata (Sector, Name) when adding new assets.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Calculate dynamic rolling window
    start_fetch = (datetime.now() - timedelta(days=35)).strftime('%Y-%m-%d')
    print(f"Starting sync from {start_fetch}...")

    for symbol in tickers:
        print(f"Syncing {symbol}...")
        
        # --- NEW METADATA LOGIC START ---
        # Check if asset already exists with valid metadata
        cur.execute("SELECT sector FROM Assets WHERE ticker_symbol = %s", (symbol,))
        asset_exists = cur.fetchone()

        # If asset doesn't exist or is a placeholder, fetch real info
        if not asset_exists or asset_exists[0] in ["US Equity", "Auto-Detected"]:
            try:
                t = yf.Ticker(symbol)
                info = t.info
                # Get real values from yf, fallback to placeholders if API fails
                real_name = info.get('longName', f"{symbol} Co")
                real_sector = info.get('sector', "Financial Services") # Default to a common sector if missing
                
                cur.execute("""
                    INSERT INTO Assets (ticker_symbol, company_name, sector) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (ticker_symbol) DO UPDATE 
                    SET company_name = EXCLUDED.company_name, sector = EXCLUDED.sector
                """, (symbol, real_name, real_sector))
            except Exception as e:
                print(f"Metadata fetch failed for {symbol}: {e}")
                # Fallback to minimize crash risk
                cur.execute("INSERT INTO Assets (ticker_symbol, company_name, sector) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING", 
                            (symbol, f"{symbol} Co", "Auto-Detected"))
        # --- NEW METADATA LOGIC END ---

        # Download rolling window data (Prices)
        df = yf.download(symbol, start=start_fetch, progress=False)
        
        if not df.empty:
            market_values = []
            for idx, r in df.iterrows():
                try:
                    # Robust extraction of OHLCV data
                    o = r['Open'].iloc[0] if hasattr(r['Open'], 'iloc') else r['Open']
                    c = r['Close'].iloc[0] if hasattr(r['Close'], 'iloc') else r['Close']
                    h = r['High'].iloc[0] if hasattr(r['High'], 'iloc') else r['High']
                    l = r['Low'].iloc[0] if hasattr(r['Low'], 'iloc') else r['Low']
                    v = r['Volume'].iloc[0] if hasattr(r['Volume'], 'iloc') else r['Volume']
                    
                    market_values.append((symbol, idx.date(), float(o), float(c), float(h), float(l), int(v)))
                except:
                    continue

            if market_values:
                # Use ON CONFLICT DO NOTHING to avoid duplicate key errors on trade_date
                execute_values(cur, """
                    INSERT INTO MarketData (ticker_symbol, trade_date, open_price, close_price, high_price, low_price, volume) 
                    VALUES %s ON CONFLICT (ticker_symbol, trade_date) DO NOTHING""", market_values)
    
    conn.commit()
    cur.close()
    conn.close()
    print("Market data synchronization complete.")
