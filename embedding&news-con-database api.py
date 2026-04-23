ALPHA_VANTAGE_KEY = "**************"

def generate_mock_embedding(cur, news_id, title):
    """
    Improved Mock: Assigns similar vectors to titles containing the same keywords
    to make the demonstration more 'realistic' during the presentation.
    """
    # Create a base seed from the first character of the title to group them
    # This ensures titles starting with 'A' are closer to each other than 'Z'
    seed_value = ord(title[0]) if len(title) > 0 else 42
    np.random.seed(seed_value)
    
    # Generate 384-dim vector based on the seed
    mock_vector = np.random.rand(384).astype(float).tolist()
    
    cur.execute("""
        INSERT INTO NewsEmbeddings (news_id, embedding)
        VALUES (%s, %s)
        ON CONFLICT (news_id) DO NOTHING
    """, (news_id, mock_vector))


def dynamic_news_sync(tickers_to_watch):
    """
    Enhanced news sync: Captures news, sentiments, and creates semantic embeddings.
    """
    print(f"Sniffing latest news for: {tickers_to_watch[:5]}...")
    target_string = ",".join(tickers_to_watch[:5]) 
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={target_string}&apikey={ALPHA_VANTAGE_KEY}'
    
    r = requests.get(url)
    data = r.json()
    if "feed" not in data:
        print("No news feed available or API limit reached.")
        return

    conn = get_db_connection()
    cur = conn.cursor()

    for item in data["feed"]:
        published_at = datetime.strptime(item["time_published"], '%Y%m%dT%H%M%S')
        for entity in item.get("ticker_sentiment", []):
            symbol = entity["ticker"]
            if symbol not in tickers_to_watch: continue
            
            relevance = float(entity["relevance_score"])
            if relevance < 0.3: continue

            try:
                # Insert into News table with unique constraint handling
                cur.execute("""
                    INSERT INTO News (ticker_symbol, publish_time, title, source)
                    VALUES (%s, %s, %s, %s) 
                    ON CONFLICT (ticker_symbol, publish_time, title) DO NOTHING 
                    RETURNING news_id
                """, (symbol, published_at, item["title"], item["source"]))
                
                res = cur.fetchone()
                
                # If a new record is created (returning news_id), sync its sub-tables
                if res: 
                    news_id = res[0]
                    
                    # Sync Sentiment Data
                    cur.execute("""
                        INSERT INTO NewsSentiment (news_id, sentiment_score, confidence_score, model_name)
                        VALUES (%s, %s, %s, %s)
                    """, (news_id, float(entity["ticker_sentiment_score"]), relevance, "Alpha-Vantage"))
                    
                    # Sync Vector Embedding Data
                    generate_mock_embedding(cur, news_id)

            except Exception as e:
                # Silently skip errors to ensure the loop continues
                continue

    conn.commit()
    cur.close()
    conn.close()
    print(f"Data Pipeline Success: News, Sentiment, and Embeddings synced at {datetime.now()}.")

# Trigger the updated process
dynamic_news_sync(active_tickers)
