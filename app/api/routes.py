"""
API routes for WhatsApp Gas Consumption FastAPI backend.
"""

import asyncio
import platform
import threading
from concurrent.futures import Future
from typing import Any, Dict

import pandas as pd  # type: ignore
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pydantic import BaseModel

from app.services.excel_service import ExcelService
from app.services.json_utils import format_message_with_styles
from app.services.whatsapp_automation import send_whatsapp_with_playwright

router = APIRouter()


# Modelos Pydantic consistentes com o contrato de dados
class WhatsAppRequest(BaseModel):
    """Request model for sending a WhatsApp message."""

    phone_number: str
    message: str


class MessageFormatRequest(BaseModel):
    """Request model for formatting a WhatsApp message from data."""

    target_date: str
    data: list


class WhatsAppResponse(BaseModel):
    """Response model for WhatsApp automation status."""

    status: str
    message: str


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Return the health status of the WhatsApp Gas API service."""
    return {"status": "healthy", "service": "WhatsApp Gas API"}


@router.post("/send-whatsapp", response_model=WhatsAppResponse)
async def send_whatsapp(request: WhatsAppRequest) -> WhatsAppResponse:
    """
    Send WhatsApp message using the stable Playwright automation engine.
    Runs inside an isolated, dedicated background thread with a Proactor loop
    to bypass Windows/Uvicorn event loop subprocess restrictions.
    """
    try:
        print(
            f"🚀 [Backend] Iniciando disparo de WhatsApp para: {request.phone_number}"
        )

        # threading, platform and Future are imported at module level

        # Usamos uma Future para capturar o retorno da nossa thread isolada
        future: Future[bool] = Future()

        def thread_target():
            # Criamos um loop novinho e isolado para esta thread
            # Criamos um loop novinho e isolado para esta thread
            if platform.system() == "Windows":
                # Evita classes obsoletas instanciando o loop diretamente
                loop = asyncio.ProactorEventLoop()
            else:
                loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)
            try:
                # Executa o Playwright de forma síncrona e segura dentro da thread
                sucesso = loop.run_until_complete(
                    send_whatsapp_with_playwright(
                        phone=request.phone_number, message=request.message
                    )
                )
                future.set_result(sucesso)
            except Exception as thread_err:  # pylint: disable=broad-exception-caught
                # Access any error raised during thread execution and propagate it
                if isinstance(thread_err, (KeyboardInterrupt, SystemExit)):
                    raise
                future.set_exception(thread_err)
            finally:
                loop.close()

        # Dispara a execução em segundo plano
        t = threading.Thread(target=thread_target)
        t.start()

        # Aguarda a conclusão da thread de forma assíncrona sem travar o FastAPI
        while t.is_alive():
            await asyncio.sleep(0.2)

        sucesso = future.result()

        if sucesso:
            return WhatsAppResponse(
                status="success",
                message="Mensagem enviada com sucesso pelo Playwright!",
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="A automação foi executada, mas não concluiu o envio.",
            )

    except Exception as e:
        print(f"❌ [Backend] Erro na rota send-whatsapp: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    target_month: str = Query(
        None, description="Filter by month (e.g., '01/2026', '02/2026')"
    ),
) -> Dict[str, Any]:
    """
    Upload and process Excel file for gas consumption data.
    Optionally filter by specific month.
    """
    try:
        print(f"Processing uploaded file: {file.filename}")
        if target_month:
            print(f"Filtering for month: {target_month}")

        filename = file.filename if file.filename else ""
        if (
            not filename
            or not isinstance(filename, str)
            or not filename.endswith((".xlsx", ".xls"))
        ):
            raise HTTPException(
                status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed"
            )

        contents = await file.read()

        # Process with the updated ExcelService
        excel_service = ExcelService()
        try:
            resultado_excel = excel_service.process_excel_content(
                contents, target_month=target_month
            )
            lista_dados = resultado_excel.get("data", [])
        except Exception as e:
            print(f"ExcelService error: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Excel processing error: {e}",
            ) from e

        print(f"Excel processed successfully. Data entries: {len(lista_dados)}")
        return {"data": lista_dados}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing Excel file: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/format-message")
async def format_message(request: MessageFormatRequest) -> Dict[str, Any]:
    """
    Format gas consumption data into WhatsApp message using normalized json_utils
    """
    try:
        print(f"Formatting message for date: {request.target_date}")
        print(f"Data entries: {len(request.data)}")

        # Convert to DataFrame
        df = pd.DataFrame(request.data)

        # Format message
        formatted_message = await format_message_with_styles(df, request.target_date)

        return {
            "status": "success",
            "formatted_message": formatted_message,
            "data_count": len(request.data),
        }

    except Exception as e:
        print(f"Error formatting message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/get-available-months")
async def get_available_months(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Get list of available months from Excel file
    """
    try:
        print(f"Getting available months from: {file.filename}")

        filename = file.filename if file.filename else ""
        if (
            not filename
            or not isinstance(filename, str)
            or not filename.endswith((".xlsx", ".xls"))
        ):
            raise HTTPException(
                status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed"
            )

        contents = await file.read()

        excel_service = ExcelService()
        result = excel_service.process_excel_content(contents)

        if isinstance(result, dict):
            data_records = result.get("data", []) or []
        else:
            data_records = []

        # Extract unique months from the data
        available_months = set()
        for item in data_records:
            data_leitura = ""
            if isinstance(item, dict):
                data_leitura = item.get("data_leitura", "")
            if isinstance(data_leitura, str) and "/" in data_leitura:
                parts = data_leitura.split("/")
                if len(parts) == 3:
                    month = parts[1]
                    year = parts[2]
                    available_months.add(f"{month}/{year}")

        months_list = sorted(list(available_months))
        print(f"Available months: {months_list}")

        return {
            "status": "success",
            "available_months": months_list,
            "total_records": len(data_records),
        }

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        print(f"Error getting available months: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) from e
