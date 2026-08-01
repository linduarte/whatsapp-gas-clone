"""
Start both FastAPI backend and Streamlit frontend for WhatsApp Gas Consumption Automation.
"""

import subprocess
import sys
import time
from typing import Optional


def start_services() -> None:
    """
    Launch FastAPI backend and Streamlit frontend as subprocesses.
    Handles graceful shutdown and cleanup on exit.
    """
    api_process: Optional[subprocess.Popen] = None
    frontend_process: Optional[subprocess.Popen] = None
    try:
        # Start FastAPI
        api_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--reload",
                "--port",
                "8000",
            ],
            stdout=None,
            stderr=None,
        )

        print("🚀 FastAPI started on http://localhost:8000")
        time.sleep(3)

        # Start Streamlit
        frontend_process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "frontend/streamlit_app.py",
                "--server.port",
                "8501",
            ],
            stdout=None,
            stderr=None,
        )

        print("🎨 Streamlit started on http://localhost:8501")

        # Wait for processes
        api_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
    finally:
        # Encerra os dois subprocessos ao fechar
        for proc in (api_process, frontend_process):
            if proc is not None and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()

if __name__ == "__main__":
    start_services()
