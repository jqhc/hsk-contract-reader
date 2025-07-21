from flask import Flask, jsonify
from flask_cors import CORS
from database import DB
from blockchain import HSKIndexer
from poller import Poller
import time
from threading import Thread
import os
from dotenv import load_dotenv

load_dotenv()
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL" "60"))
API_URL = os.getenv("API_URL")
CONTRACT_ADDRESSES = os.getenv("CONTRACT_ADDRESSES").split(",") if os.getenv

app = Flask(__name__)
CORS(app)

@app.get("/metrics")
def read_metrics():
    """Return aggregated metrics for all tracked contracts."""
    metrics, user_count = db.get_all_metrics()
    return jsonify({"per_contract_metrics": metrics, "total_user_count": user_count})

if __name__ == '__main__':
    db = DB()
    indexer = HSKIndexer(API_URL)
    poller = Poller(db, indexer, CONTRACT_ADDRESSES, POLLING_INTERVAL)

    def run_poller():
        while True:
            poller.poll()
            time.sleep(POLLING_INTERVAL)

    poller_thread = Thread(target=run_poller, daemon=True)
    poller_thread.start()

    try:
        # poller = Poller(db, indexer, CONTRACT_ADDRESSES, POLLING_INTERVAL)
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Unexpected error occurred: {e}. API shutting down")
    finally:
        db.close()
