from flask import Flask, jsonify
from flask_cors import CORS
from database import DB
from blockchain import HSKIndexer
from poller import Poller
from threading import Timer
import os
from dotenv import load_dotenv

load_dotenv()
POLLING_INTERVAL = os.getenv("POLLING_INTERVAL")
API_URL = os.getenv("API_URL")
CONTRACT_ADDRESSES = os.getenv("CONTRACT_ADDRESSES").split(",")

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
    try:
        # poller = Poller(db, indexer, CONTRACT_ADDRESSES, POLLING_INTERVAL)
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Unexpected error occurred: {e}. API shutting down")
    finally:
        db.close()
