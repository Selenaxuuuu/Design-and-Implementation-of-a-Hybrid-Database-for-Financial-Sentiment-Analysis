# Design-and-Implementation-of-a-Hybrid-Database-for-Financial-Sentiment-Analysis
python pgsql

QuantIntel: Design and Implementation of a Hybrid Database for Financial Sentiment Analysis

1. Research Objective

This project builds an event-driven analytics system integrating structured financial time-series data with unstructured NLP embeddings. Moving beyond pure price-based black-box models, it leverages rigorous relational modeling and vector retrieval to quantify news sentiment and semantics, exploring statistical correlations between media sentiment and asset performance. The system features high robustness, effectively handling cold starts, data sparsity, and real-time extreme event alerts.

- System Workflow

An end-to-end pipeline from external API ingestion to advanced internal SQL analytics:

Data Ingestion: Python scripts periodically fetch asset trading histories, metadata, and financial news.

Data Enrichment: An asynchronous upsert mechanism (ON CONFLICT DO UPDATE) patches missing metadata (e.g., Sector classifications) to ensure eventual consistency.

NLP Processing: Calculates news sentiment scores (-1.0 to 1.0) and encodes text into 384-dimensional dense vector embeddings.

Active Database: Database triggers automatically generate high-priority alerts upon the insertion of extreme negative sentiment.

Analytical Layer: Utilizes advanced SQL features (CTEs, sliding window calculations) for sector-level sentiment aggregation and time-series retrieval.

- Tech Stack & Libraries
Data Pipeline (Python)

yfinance: Fetches historical prices (OHLCV) and corporate metadata.

pandas: Handles in-memory data cleaning, alignment, and preprocessing.

psycopg2 / SQLAlchemy: Manages connection pooling and parameterized SQL execution (preventing SQL injection).

sentence-transformers: Encodes unstructured news text into high-dimensional embeddings.

Database (PostgreSQL)

pgvector: PostgreSQL extension for storing dense vectors and executing similarity searches via Cosine Distance.

-Applied Database Concepts
3NF Normalization: Strictly decouples entities. Heavy sentiment scores and vector data are separated from the main News table, maintaining referential integrity via Foreign Keys.

CTEs & Dynamic Aggregation: Extensively uses WITH clauses alongside GREATEST/LEAST scalar functions and MIN() aggregations to build dynamic sliding windows. This prevents division-by-zero errors and statistical bias during the "cold start" phase of newly listed assets.

Handling Data Sparsity: Uses LEFT JOIN with COALESCE to resolve missing values in multi-table queries, eliminating information blind spots.

Database Triggers: Employs PL/pgSQL triggers to implement true event-driven logic, automatically logging anomalous sentiment into the Alerts table to reduce application-layer polling overhead.

Performance & Indexing
Composite B-Tree Index: Created on (ticker_symbol, publish_time DESC). Validated via EXPLAIN ANALYZE, this triggers a Bitmap Index Scan on large datasets, drastically improving I/O efficiency for time-series aggregations.

HNSW Vector Index: Implemented the Hierarchical Navigable Small World graph index for 384-dimensional semantic search. It delivers sub-second Approximate Nearest Neighbor (ANN) query responses while maintaining high precision.

- User Scenarios
Sector Sentiment Aggregation: Multi-dimensional grouping based on GICS standards to calculate the average market sentiment index.

Risk & Alert Tracking: Real-time monitoring and display of CRITICAL negative market news driven by database triggers.

Fuzzy Semantic Search: Bypasses traditional LIKE keyword limitations, using vector calculations to directly retrieve news clusters based on abstract concepts (e.g., "AI Innovation").

Anomaly Burst Detection: Dynamically compares "past 24h news volume" against the "historical observation average" to precisely capture abnormal asset volatility signals.
