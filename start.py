# start.py
import subprocess
import sys
import time


def start_services():
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
            ]
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
            ]
        )

        print("🎨 Streamlit started on http://localhost:8501")

        # Wait for processes
        api_process.wait()
        frontend_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Shutting down services...")
        api_process.terminate()
        frontend_process.terminate()


if __name__ == "__main__":
    start_services()
