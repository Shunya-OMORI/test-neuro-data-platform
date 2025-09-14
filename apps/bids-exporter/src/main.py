import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, jsonify, request, send_from_directory
from . import config
from .worker import run_bids_export_task

# --- App Initialization ---
app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)
# In a real-world scenario, you would use Redis or a DB for this
export_tasks = {}

# --- API Endpoints ---
@app.route("/api/v1/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"})

@app.route("/api/v1/experiments/<experiment_id>/export", methods=["POST"])
def start_export(experiment_id: str):
    """Starts a new BIDS export task in the background."""
    task_id = str(uuid.uuid4())
    export_tasks[task_id] = {"status": "pending", "message": "Task is queued."}
    executor.submit(run_bids_export_task, task_id, experiment_id, export_tasks)
    
    return jsonify({
        "status": "accepted",
        "task_id": task_id,
        "message": "BIDS export task has been started."
    }), 202

@app.route("/api/v1/export-tasks/<task_id>", methods=["GET"])
def get_export_status(task_id: str):
    """Retrieves the status of an export task."""
    task = export_tasks.get(task_id)
    if not task:
        return jsonify({"error": "Task ID not found."}), 404
    return jsonify(task)

@app.route("/api/v1/downloads/<path:filename>", methods=["GET"])
def download_file(filename: str):
    """Downloads a completed BIDS zip file."""
    return send_from_directory(
        config.BIDS_OUTPUT_DIR, 
        filename, 
        as_attachment=True
    )

# --- Main Execution ---
if __name__ == "__main__":
    if not os.path.exists(config.BIDS_OUTPUT_DIR):
        os.makedirs(config.BIDS_OUTPUT_DIR)
    
    app.run(host="0.0.0.0", port=config.PORT)