# start_template.py - Generic FastAPI + Streamlit Launcher
import subprocess
import sys
import time

class ServiceLauncher:
    def __init__(self, config=None):
        """
        Generic launcher for FastAPI + Streamlit applications
        
        Args:
            config (dict): Configuration options
        """
        # Default configuration
        self.config = {
            "fastapi_module": "app.main:app",
            "fastapi_port": 8000,
            "streamlit_file": "frontend/streamlit_app.py", 
            "streamlit_port": 8501,
            "startup_delay": 3,
            "auto_reload": True
        }
        
        # Update with custom config
        if config:
            self.config.update(config)
    
    def start_services(self):
        """Start both FastAPI and Streamlit services"""
        try:
            print(f"🚀 Starting {self.config['fastapi_module']} on port {self.config['fastapi_port']}...")
            
            # Build FastAPI command
            fastapi_cmd = [
                sys.executable, "-m", "uvicorn",
                self.config['fastapi_module'],
                "--port", str(self.config['fastapi_port'])
            ]
            
            if self.config['auto_reload']:
                fastapi_cmd.append("--reload")
            
            # Start FastAPI
            # pyrefly: ignore  # implicitly-defined-attribute, no-matching-overload
            self.api_process = subprocess.Popen(fastapi_cmd)
            print(f"✅ FastAPI started on http://localhost:{self.config['fastapi_port']}")
            
            # Wait for FastAPI to initialize
            # pyrefly: ignore  # bad-argument-type
            time.sleep(self.config['startup_delay'])
            
            print(f"🎨 Starting Streamlit from {self.config['streamlit_file']}...")
            
            # Start Streamlit
            # pyrefly: ignore  # implicitly-defined-attribute, no-matching-overload
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run",
                self.config['streamlit_file'],
                "--server.port", str(self.config['streamlit_port'])
            ])
            
            print(f"✅ Streamlit started on http://localhost:{self.config['streamlit_port']}")
            print("\n🎉 Both services are running!")
            print("📖 Press Ctrl+C to stop all services")
            
            # Wait for processes
            self.api_process.wait()
            self.frontend_process.wait()
            
        except KeyboardInterrupt:
            self.shutdown_services()
        except Exception as e:
            print(f"❌ Error starting services: {e}")
            self.shutdown_services()
    
    def shutdown_services(self):
        """Gracefully shutdown both services"""
        print("\n🛑 Shutting down services...")
        
        try:
            if hasattr(self, 'api_process'):
                self.api_process.terminate()
                print("✅ FastAPI stopped")
        except Exception:
            pass
            
        try:
            if hasattr(self, 'frontend_process'):
                self.frontend_process.terminate()
                print("✅ Streamlit stopped")
        except Exception:
            pass
        
        print("👋 All services stopped successfully!")

# Example usage configurations for different projects:

# Configuration 1: Default (current project)
DEFAULT_CONFIG = {
    "fastapi_module": "app.main:app",
    "fastapi_port": 8000,
    "streamlit_file": "frontend/streamlit_app.py",
    "streamlit_port": 8501,
    "startup_delay": 3
}

# Configuration 2: Different structure
CUSTOM_CONFIG = {
    "fastapi_module": "backend.server:app",
    "fastapi_port": 8080,
    "streamlit_file": "ui/dashboard.py",
    "streamlit_port": 8502,
    "startup_delay": 5
}

# Configuration 3: Simple structure
SIMPLE_CONFIG = {
    "fastapi_module": "main:app",
    "fastapi_port": 3000,
    "streamlit_file": "app.py",
    "streamlit_port": 3001,
    "startup_delay": 2,
    "auto_reload": False
}

def main():
    """Main function - customize as needed"""
    # Choose configuration based on your project
    launcher = ServiceLauncher(DEFAULT_CONFIG)
    launcher.start_services()

if __name__ == "__main__":
    main()
