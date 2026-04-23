import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
import requests
from datetime import datetime, timedelta
import random
import time
from io import StringIO
import numpy as np

DB_CONFIG = {
    "dbname": "postgres",
    "user": "***",
    "password": "", 
    "host": "***",
    "port": "***"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
