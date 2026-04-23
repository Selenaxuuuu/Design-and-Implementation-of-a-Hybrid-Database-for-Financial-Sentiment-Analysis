CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE Assets(
ticker_symbol VARCHAR(10) PRIMARY KEY,
company_name VARCHAR(100) NOT  NULL,
sector VARCHAR(50),
exchange VARCHAR(20)
);

CREATE TABLE MarketData(
ticker_symbol VARCHAR(10) REFERENCES Assets(ticker_symbol),
trade_date DATE NOT NULL,
open_price DECIMAL(15, 4),
close_price DECIMAL(15, 4),
high_price DECIMAL(15, 4),
low_price DECIMAL(15, 4),
volume BIGINT,
PRIMARY KEY (ticker_symbol, trade_date)
);
CREATE INDEX idx_watchlist_user_id ON Watchlist(user_id);

CREATE TABLE News(
news_id SERIAL PRIMARY KEY,
ticker_symbol VARCHAR(10) REFERENCES Assets(ticker_symbol),
publish_time TIMESTAMPTZ NOT NULL,
title TEXT NOT NULL,
content TEXT,
source VARCHAR(50)
);

CREATE TABLE NewsEmbeddings(
news_id INTEGER PRIMARY KEY REFERENCES News(news_id) ON DELETE CASCADE,
embedding vector(384)
);

CREATE TABLE Watchlist(
event_id SERIAL PRIMARY KEY,
user_id INTEGER NOT NULL,
user_name VARCHAR(50) NOT NULL,
ticker_symbol VARCHAR(10) REFERENCES Assets(ticker_symbol),
action_type VARCHAR(10) CHECK (action_type IN ('ADD', 'REMOVE')),
event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_watchlist_user_id ON Watchlist(user_id);

CREATE TABLE NewsSentiment(
news_id INTEGER PRIMARY KEY REFERENCES News(news_id) ON DELETE CASCADE,
sentiment_score DECIMAL(3, 2),
confidence_score DECIMAL(3, 2),
model_name VARCHAR(50),
CONSTRAINT check_sentiment_range CHECK (sentiment_score >= -1 AND sentiment_score <= 1)
);

CREATE TABLE Alerts(
alert_id SERIAL PRIMARY KEY,
news_id INTEGER REFERENCES News(news_id) ON DELETE CASCADE,
alert_level VARCHAR(20),
message TEXT,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE News ADD CONSTRAINT unique_news_entry UNIQUE (ticker_symbol, publish_time, title);
CREATE INDEX idx_marketdata_lookup ON MarketData (ticker_symbol, trade_date DESC);
CREATE INDEX idx_news_lookup ON News (ticker_symbol, publish_time DESC);
CREATE INDEX ON NewsEmbeddings USING hnsw (embedding vector_cosine_ops);

CREATE OR REPLACE FUNCTION check_sentiment_and_alert()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.sentiment_score < -0.8 THEN
        INSERT INTO Alerts (news_id, alert_level, message)
        VALUES (
            NEW.news_id, 
            'CRITICAL', 
            'Extremely negative news detected for asset ' || 
            (SELECT ticker_symbol FROM News WHERE news_id = NEW.news_id)
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_negative_sentiment_alert
AFTER INSERT ON NewsSentiment
FOR EACH ROW
EXECUTE FUNCTION check_sentiment_and_alert();

CREATE INDEX idx_news_ticker_time ON News (ticker_symbol, publish_time DESC);

CREATE INDEX idx_news_embeddings_hnsw ON NewsEmbeddings  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
