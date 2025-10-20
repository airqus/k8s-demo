from flask import Flask, request
import psycopg2
import datetime
import os

app = Flask(__name__)

@app.route('/')
def log_access():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "demo"),
            user=os.getenv("DB_USER", "demo"),
            password=os.getenv("DB_PASS", "demo"),
            host=os.getenv("DB_HOST", "postgres"),   # 👈 default to Service name
            port=os.getenv("DB_PORT", "5432")
        )
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
        return f"Logging failed: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
