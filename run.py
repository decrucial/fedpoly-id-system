from app import create_app
from datetime import datetime

app = create_app('development')

@app.context_processor
def inject_globals():
    return dict(now=datetime.utcnow())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
