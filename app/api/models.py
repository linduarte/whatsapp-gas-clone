# app/api/models.py
from pydantic import BaseModel
from typing import List, Optional
# from datetime import datetime

class GasConsumptionData(BaseModel):
    data_leitura: str
    apartamento: str
    leitura_atual: float
    consumo_m3: float
    calculo: float
    valor_final_rs: float

class GasConsumptionResponse(BaseModel):
    target_date: Optional[str]
    data: List[GasConsumptionData]

class WhatsAppMessage(BaseModel):
    phone_number: str
    message: str

class WhatsAppResponse(BaseModel):
    status: str
    message: str