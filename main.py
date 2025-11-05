import os
import asyncio
import threading
from flask import Flask, jsonify
from pyzeebe import ZeebeClient, ZeebeWorker, create_camunda_cloud_channel
from dotenv import load_dotenv
from workers import register_tasks

load_dotenv()

app = Flask(__name__)
zeebe_loop = asyncio.new_event_loop()
client = None

@app.route("/")
def index():
    return jsonify({"message": "Worker Flask is running!"})

@app.route("/start")
def start_process():
    global client
    if client is None:
        return jsonify({"error": "Zeebe client not ready"}), 503

    process_id = "Process_0yffers"  # ID de ton diagram BPMN
    async def _start():
        return await client.run_process(process_id)

    future = asyncio.run_coroutine_threadsafe(_start(), zeebe_loop)
    result = future.result()
    instance_key = result.process_instance_key

    return jsonify({
        "message": f"Process {process_id} started",
        "process_instance_key": instance_key
    })

def run_worker():
    global client
    asyncio.set_event_loop(zeebe_loop)

    channel = create_camunda_cloud_channel(
        client_id=os.environ["ZEEBE_CLIENT_ID"],
        client_secret=os.environ["ZEEBE_CLIENT_SECRET"],
        cluster_id=os.environ["ZEEBE_ADDRESS"].split(".")[0],
        region="bru-2"  # adapte selon ton cluster
    )

    client = ZeebeClient(channel)
    worker = ZeebeWorker(channel)

    register_tasks(worker)

    print("Zeebe worker started")
    zeebe_loop.run_until_complete(worker.work())

if __name__ == "__main__":
    threading.Thread(target=run_worker, daemon=True).start()
    app.run(port=5000)
