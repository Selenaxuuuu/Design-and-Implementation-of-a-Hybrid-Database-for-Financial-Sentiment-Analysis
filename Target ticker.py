def get_top_volume_tickers(limit=100):
    """Fetch S&P 500 tickers and filter the top N by current market volume."""
    print(f"Fetching S&P 500 list and analyzing top {limit} by volume...")
    headers = {"User-Agent": "Mozilla/5.0"}
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    
    response = requests.get(url, headers=headers)
    table = pd.read_html(StringIO(response.text))
    df_sp500 = table[0]
    # Handle ticker symbols for yfinance compatibility
    all_tickers = [t.replace('.', '-') for t in df_sp500['Symbol'].tolist()]

    # Quick download to get the latest trading volume
    summary_data = yf.download(all_tickers, period="1d", group_by='ticker', threads=True, progress=False)
    
    volume_list = []
    for ticker in all_tickers:
        try:
            vol_data = summary_data[ticker]['Volume']
            # Handle cases where yfinance returns a DataFrame instead of a Series
            vol = vol_data.iloc[-1] if isinstance(vol_data, pd.Series) else vol_data
            if not pd.isna(vol):
                volume_list.append({'ticker': ticker, 'volume': float(vol)})
        except:
            continue
    
    return pd.DataFrame(volume_list).sort_values(by='volume', ascending=False)['ticker'].head(limit).tolist()

# Get the list for today
active_tickers = get_top_volume_tickers(limit=100)

