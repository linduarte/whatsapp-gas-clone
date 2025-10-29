# start_template.py - Generic FastAPI + Streamlit Launcher

import subprocess
import sys
import time
from typing import Optional, Dict, Any



class ServiceLauncher:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """
        Generic launcher for FastAPI + Streamlit applications.

        Args:
            config: Optional dictionary of configuration options.
        """
        self.config: Dict[str, Any] = {
            "fastapi_module": "app.main:app",
            "fastapi_port": 8000,
            "streamlit_file": "frontend/streamlit_app.py",
            "streamlit_port": 8501,
            "startup_delay": 3,
            "auto_reload": True,
        }
        if config:
            self.config.update(config)


    def start_services(self) -> None:
        """
        Start both FastAPI and Streamlit services as subprocesses.
        Handles graceful shutdown and error reporting.
        """
        self.api_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        try:
            print(f"🚀 Starting {self.config['fastapi_module']} on port {self.config['fastapi_port']}...")

            fastapi_cmd = [
                sys.executable,
                "-m",
                "uvicorn",
                self.config["fastapi_module"],
                "--port",
                str(self.config["fastapi_port"]),
            ]
            if self.config["auto_reload"]:
                fastapi_cmd.append("--reload")

            self.api_process = subprocess.Popen(fastapi_cmd)
            print(f"✅ FastAPI started on http://localhost:{self.config['fastapi_port']}")

            time.sleep(self.config["startup_delay"])

            print(f"🎨 Starting Streamlit from {self.config['streamlit_file']}...")
            self.frontend_process = subprocess.Popen([
                sys.executable,
                "-m",
                "streamlit",
                "run",
                self.config["streamlit_file"],
                "--server.port",
                str(self.config["streamlit_port"]),
            ])

            print(f"✅ Streamlit started on http://localhost:{self.config['streamlit_port']}")
            print("\n🎉 Both services are running!")
            print("📖 Press Ctrl+C to stop all services")

            self.api_process.wait()
            self.frontend_process.wait()

        except KeyboardInterrupt:
            self.shutdown_services()
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            self.shutdown_services()


    def shutdown_services(self) -> None:
        """
        Gracefully shutdown both FastAPI and Streamlit services.
        """
        print("\n🛑 Shutting down services...")
        try:
            if hasattr(self, "api_process") and self.api_process:
                self.api_process.terminate()
                print("✅ FastAPI stopped")
        except Exception:
            pass
        try:
            if hasattr(self, "frontend_process") and self.frontend_process:
                self.frontend_process.terminate()
                print("✅ Streamlit stopped")
        except Exception:
            pass
        print("👋 All services stopped successfully!")



# Example usage configurations for different projects:
DEFAULT_CONFIG: Dict[str, Any] = {
    "fastapi_module": "app.main:app",
    "fastapi_port": 8000,
    "streamlit_file": "frontend/streamlit_app.py",
    "streamlit_port": 8501,
    "startup_delay": 3,
}

CUSTOM_CONFIG: Dict[str, Any] = {
    "fastapi_module": "backend.server:app",
    "fastapi_port": 8080,
    "streamlit_file": "ui/dashboard.py",
    "streamlit_port": 8502,
    "startup_delay": 5,
}

SIMPLE_CONFIG: Dict[str, Any] = {
    "fastapi_module": "main:app",
    "fastapi_port": 3000,
    "streamlit_file": "app.py",
    "streamlit_port": 3001,
    "startup_delay": 2,
    "auto_reload": False,
}



def main() -> None:
    """
    Main function to launch services. Customize as needed.
    """
    launcher = ServiceLauncher(DEFAULT_CONFIG)
    launcher.start_services()


if __name__ == "__main__":
    main()
