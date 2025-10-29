git clone <your-repo-url>

# WhatsApp Gas Consumption Automation (Python 3.14, FastAPI, Streamlit, uv)

## 🚀 Overview
Automate the process of reading Excel gas consumption data, formatting it, and sending professional WhatsApp messages to clients or billing offices. Built with Python 3.14, FastAPI, Streamlit, and managed with [uv](https://github.com/astral-sh/uv) for modern dependency management.

## �️ Features
- Upload and process Excel files (`.xlsx`, `.xls`) with gas consumption data
- Filter and preview data by month/year
- Format messages for WhatsApp with professional currency and layout
- Automated WhatsApp Web integration via Selenium (Chrome)
- FastAPI backend with robust async endpoints and Pydantic validation
- Streamlit frontend for easy data upload, preview, and sending
- Modern Python 3.14 codebase with type hints and best practices

## 📦 Prerequisites
- Python 3.14+
- [uv](https://github.com/astral-sh/uv) package manager
- Google Chrome browser (for WhatsApp Web automation)

## ⚡ Quick Start
```bash
# Clone the repository
git clone <your-repo-url>
cd wathsapp-gas-clone

# Pin Python version and create a virtual environment
uv python pin 3.14
uv venv

# Activate the environment (Windows)
.\.venv\Scripts\activate

# Sync all dependencies
uv sync
```

## 🔧 Running the Application

### Option 1: Run Both Services Together
```bash
uv run start.py
```
*Starts FastAPI backend (http://localhost:8000) and Streamlit frontend (http://localhost:8501)*

### Option 2: Run Services Separately (Recommended)

**Terminal 1: FastAPI Backend**
```bash
uv run uvicorn app.main:app --reload --port 8000
```
*API: http://localhost:8000 | Docs: http://localhost:8000/docs | Health: http://localhost:8000/api/v1/health*

**Terminal 2: Streamlit Frontend**
```bash
uv run streamlit run frontend/streamlit_app.py
```
*Web UI: http://localhost:8501*

## 📖 Usage Workflow
1. **Upload Excel**: Use the Streamlit UI to upload your `.xlsx`/`.xls` file.
2. **Select Month/Year**: Filter and preview data for the desired period.
3. **Preview & Validate**: Review apartment, consumption, and billing data.
4. **Send WhatsApp**: Enter the recipient's phone number and send the formatted message. Chrome will open WhatsApp Web for you.

## 🧩 API Endpoints
- `GET /api/v1/health` — Health check
- `POST /api/v1/upload-excel` — Upload/process Excel
- `POST /api/v1/format-message` — Format WhatsApp message
- `POST /api/v1/send-whatsapp` — Send WhatsApp message
- `POST /api/v1/test-whatsapp-simple` — Test WhatsApp automation

## 📁 Project Structure
```
wathsapp-gas-clone/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── models.py
│   │   └── routes.py
│   └── services/
│       ├── excel_service.py
│       ├── whatsapp_service.py
│       ├── whatsapp_automation.py
│       ├── message_service.py
│       └── json_utils.py
├── frontend/
│   ├── streamlit_app.py
│   └── components/
├── start.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

## ⚙️ Excel File Requirements
- Format: `.xlsx` or `.xls`
- Sheet name: `Gas_2025`
- Required columns:
  - `Data Leitura` (DD/MM/YYYY)
  - `Apartamento`
  - `Leitura atual`
  - `Consumo(m³)`
  - `Cálculo`
  - `Valor final(R$)`

## 💬 WhatsApp Automation Setup
- Chrome browser must be installed
- WhatsApp Web will open automatically
- Scan QR code on first use and keep session active

## 🛠️ Troubleshooting
- **FastAPI not starting:** Check port 8000, firewall, or use `netstat`/`taskkill` as needed
- **Streamlit errors:** Ensure backend is running, check API base URL
- **WhatsApp automation:** Update Chrome, clear cache, restart browser

## 🌟 Best Practices & Modernization
- Python 3.14+ with type hints and async/await
- All dependencies managed with `uv` for speed and reproducibility
- Pydantic models for validation and documentation
- Modular code: clear separation of API, services, and frontend
- Robust error handling and logging

## � Extend & Contribute
- Add new endpoints or UI features as needed
- Improve Excel parsing or WhatsApp automation logic
- PRs and issues welcome!

---
**Built with ❤️ using FastAPI, Streamlit, Selenium, and modern Python.**

