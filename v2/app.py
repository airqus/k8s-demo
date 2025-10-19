from flask import Flask
import psutil

app = Flask(__name__)

@app.route('/')
def system_info():
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory().percent
    return f"CPU Usage: {cpu}%<br>Memory Usage: {mem}%"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
