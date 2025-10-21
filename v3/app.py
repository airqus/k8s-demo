from flask import Flask, request, jsonify
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

def get_real_ip():
    """Get the real client IP address from headers"""
    # Check X-Forwarded-For header (set by GCP Load Balancer)
    if request.headers.get('X-Forwarded-For'):
        # X-Forwarded-For can contain multiple IPs: "client, proxy1, proxy2"
        # The first IP is the real client IP
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # Fallback to X-Real-IP
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    
    # Last resort: use remote_addr (will be internal IP)
    return request.remote_addr

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
        
        # Get real client IP
        client_ip = get_real_ip()
        
        cur.execute(
            "INSERT INTO access_log (ip, timestamp) VALUES (%s, %s)",
            (client_ip, datetime.datetime.now())
        )
        conn.commit()
        cur.close()
        conn.close()
        return f"Access logged to PostgreSQL from IP: {client_ip}"
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

@app.route('/logs')
def view_logs():
    """View all access logs"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, ip, timestamp FROM access_log ORDER BY timestamp DESC LIMIT 100")
        logs = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([
            {"id": log[0], "ip": log[1], "timestamp": str(log[2])}
            for log in logs
        ])
    except Exception as e:
        return f"Failed to fetch logs: {e}", 500

@app.route('/stats')
def stats():
    """View access statistics"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Total count
        cur.execute("SELECT COUNT(*) FROM access_log")
        total = cur.fetchone()[0]
        
        # By IP
        cur.execute("""
            SELECT ip, COUNT(*) as count 
            FROM access_log 
            GROUP BY ip 
            ORDER BY count DESC 
            LIMIT 10
        """)
        by_ip = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({
            "total_accesses": total,
            "top_ips": [{"ip": row[0], "count": row[1]} for row in by_ip]
        })
    except Exception as e:
        return f"Failed to fetch stats: {e}", 500

@app.route('/debug')
def debug():
    """Debug endpoint to see all headers and IPs"""
    return jsonify({
        "remote_addr": request.remote_addr,
        "x_forwarded_for": request.headers.get('X-Forwarded-For'),
        "x_real_ip": request.headers.get('X-Real-IP'),
        "detected_real_ip": get_real_ip(),
        "all_headers": dict(request.headers)
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
