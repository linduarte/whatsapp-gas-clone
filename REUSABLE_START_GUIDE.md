# How to Use start.py as a Reusable Tool

## 🚀 **Yes! Your start.py is Perfect for Other Projects!**

### **Option 1: Simple Copy & Modify**
Copy your `start.py` to any FastAPI + Streamlit project and modify these lines:

```python
# Change these paths to match your project structure:
"app.main:app"                    # Your FastAPI module
"frontend/streamlit_app.py"       # Your Streamlit file
```

### **Option 2: Use the Generic Template**
Use `start_template.py` for more flexibility:

```python
# Example: Different project structure
from start_template import ServiceLauncher

config = {
    "fastapi_module": "backend.server:app",  # Different module path
    "fastapi_port": 8080,                    # Different port
    "streamlit_file": "ui/dashboard.py",     # Different file location
    "streamlit_port": 8502,                  # Different port
    "startup_delay": 5                       # Longer startup delay
}

launcher = ServiceLauncher(config)
launcher.start_services()
```

## 📁 **Works with ANY Project Structure:**

### **Structure 1: Your Current Project**
```
project/
├── app/main.py          # FastAPI app
├── frontend/streamlit_app.py
└── start.py
```

### **Structure 2: Simple Structure**
```
project/
├── main.py              # FastAPI app
├── app.py               # Streamlit app
└── start.py
```

### **Structure 3: Backend/Frontend Split**
```
project/
├── backend/server.py    # FastAPI app
├── ui/dashboard.py      # Streamlit app
└── start.py
```

## 🛠️ **Quick Setup for New Projects:**

1. **Copy `start.py` to your new project**
2. **Modify the paths:**
   ```python
   "app.main:app"           → "your_module:app"
   "frontend/streamlit_app.py" → "your_streamlit_file.py"
   ```
3. **Run:** `python start.py`

## 🎯 **Benefits for Any Project:**

- ✅ **One command** to start both services
- ✅ **No terminal juggling** 
- ✅ **Consistent development workflow**
- ✅ **Easy onboarding** for team members
- ✅ **Cross-platform** (Windows, Mac, Linux)

## 📝 **Template for New Projects:**

```python
# start.py - Customize these variables
FASTAPI_MODULE = "app.main:app"           # ← Change this
FASTAPI_PORT = 8000
STREAMLIT_FILE = "frontend/app.py"        # ← Change this  
STREAMLIT_PORT = 8501

# Rest of the code stays the same!
```

Your `start.py` is essentially a **micro-framework** for launching full-stack Python web applications! 🎉

