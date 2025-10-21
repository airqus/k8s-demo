from flask import Flask, request
import psycopg2
import datetime
import os
import time

app = Flask(__name__)

def get_db_connection(max_retries=5, retry_delay=2):
    """Try to connect to database with retries"""
    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME", "demo"),
                user=os.getenv("DB_USER", "demo"),
                password=os.getenv("DB_PASS", "demo"),
                host=os.getenv("DB_HOST", "postgres"),
                port=os.getenv("DB_PORT", "5432"),
                connect_timeout=3
            )
            return conn
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                raise e

@app.route('/')
def log_access():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id SERIAL PRIMARY KEY,
                ip TEXT,
                timestamp TIMESTAMP
            )
        """)
        cur.execute(
            "INSERT INTO access_log (ip, timestamp) VALUES (%s, %s)",
            (request.remote_addr, datetime.datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        return "Access logged to PostgreSQL"
    except Exception as e:
        return f"Logging failed: {e}", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        conn = get_db_connection(max_retries=1, retry_delay=0)
        conn.close()
        return "OK", 200
    except:
        return "Database not ready", 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
