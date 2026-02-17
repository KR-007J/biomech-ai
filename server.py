"""
BioMech AI — Render Web Server
Client-side app served via Flask (no OpenCV needed)
"""
import os
from flask import Flask, send_from_directory, send_file

app = Flask(__name__, static_folder='static', template_folder='.')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'BioMech AI', 'version': '2.0'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
