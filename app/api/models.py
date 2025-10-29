
"""
Pydantic models for WhatsApp Gas Consumption API.
"""
from pydantic import BaseModel
from typing import List, Optional


class GasConsumptionData(BaseModel):
    """
    Model representing a single apartment's gas consumption record.
    """
    data_leitura: str
    apartamento: str
    leitura_atual: float
    consumo_m3: float
    calculo: float
    valor_final_rs: float


class GasConsumptionResponse(BaseModel):
    """
    Response model for a list of gas consumption records for a given date.
    """
    target_date: Optional[str]
    data: List[GasConsumptionData]


class WhatsAppMessage(BaseModel):
    """
    Model for sending a WhatsApp message to a phone number.
    """
    phone_number: str
    message: str


class WhatsAppResponse(BaseModel):
    """
    Model for WhatsApp automation response status.
    """
    status: str
    message: str
