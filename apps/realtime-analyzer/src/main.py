import threading
from flask import Flask, jsonify
from . import config
from .data_store import user_data_store
from .analyzer import analysis_worker_thread
from .consumer import start_consumer_thread

# --- Flask App Initialization ---
app = Flask(__name__)

# --- API Endpoints ---
@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

@app.route("/api/v1/users/<user_id>/analysis", methods=["GET"])
def get_analysis_results(user_id: str):
    """Returns the latest analysis results for a specific user."""
    result = user_data_store.get_analysis_result(user_id)
    if result is None:
        return jsonify({
            "status": "pending",
            "message": "Analysis results are not yet available. Please wait."
        }), 202
    
    return jsonify(result)

# --- Main Execution ---
if __name__ == "__main__":
    # Start the RabbitMQ consumer in a background thread
    consumer_thread = threading.Thread(target=start_consumer_thread, daemon=True)
    consumer_thread.start()
    
    # Start the analysis worker in another background thread
    analyzer_thread = threading.Thread(target=analysis_worker_thread, daemon=True)
    analyzer_thread.start()
    
    # Start the Flask API server
    print(f"🚀 Realtime Analyzer service running at http://0.0.0.0:{config.PORT}")
    app.run(host="0.0.0.0", port=config.PORT)