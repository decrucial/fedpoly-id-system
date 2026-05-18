from app import create_app
from datetime import datetime
import os

app = create_app('production')

@app.context_processor
def inject_globals():
    return dict(now=datetime.utcnow())

if __name__ == '__main__':
    app.run()
