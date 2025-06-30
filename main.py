# app/main.py - FastAPI Application
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from app.services.excel_service import ExcelService
from app.services.whatsapp_service import WhatsAppService
from app.api.models import GasConsumptionResponse

app = FastAPI(title="WhatsApp Gas Consumption API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload-excel", response_model=GasConsumptionResponse)
async def upload_excel(file: UploadFile = File(...)):
    excel_service = ExcelService()
    data = await excel_service.process_excel(file)
    return GasConsumptionResponse(data=data)


@app.post("/send-whatsapp")
async def send_whatsapp(phone: str, message: str):
    whatsapp_service = WhatsAppService()
    result = await whatsapp_service.send_message(phone, message)
    return {"status": "sent", "result": result}
