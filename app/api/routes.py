# app/api/routes.py
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import json
import os
import pandas as pd
from app.services.whatsapp_service import WhatsAppService
from app.services.excel_service import ExcelService
from app.services.json_utils import format_message_with_styles

router = APIRouter()

# Data models for API requests
class WhatsAppRequest(BaseModel):
    phone_number: str
    message: str

class MessageFormatRequest(BaseModel):
    target_date: str
    data: list

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "WhatsApp Gas API"}

@router.post("/test-whatsapp-simple")
async def test_whatsapp_simple(
    phone_number: str = Query(default="+5531988292853", description="Your phone number"),
    message: str = Query(default="Test message from FastAPI - No emojis!", description="Test message")
):
    """
    Simple WhatsApp test - sends a basic message to test the automation
    """
    try:
        print(f"Testing WhatsApp automation with phone: {phone_number}")
        
        # Clean the message to remove any problematic characters
        clean_message = message.encode('ascii', 'ignore').decode('ascii')
        if not clean_message.strip():
            clean_message = "Test message from FastAPI"
        
        print(f"Original message: {message}")
        print(f"Cleaned message: {clean_message}")
        
        whatsapp_service = WhatsAppService()
        result = await whatsapp_service.send_test_message(phone_number, clean_message)
        
        return {
            "status": "success",
            "message": "WhatsApp test completed",
            "phone_number": phone_number,
            "original_message": message,
            "sent_message": clean_message,
            "whatsapp_result": result
        }
        
    except Exception as e:
        print(f"Error in WhatsApp test: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-main-json-from-existing")
async def test_main_json_from_existing(
    phone_number: str = Query(default="+5531988292853", description="Your phone number")
):
    """
    Test using your existing output.json file with full WhatsApp automation
    """
    try:
        print(f"Starting full JSON to WhatsApp workflow for phone: {phone_number}")
        
        # Path to your existing output.json
        file_path = r"D:\reposground\work\whatsapp_auto-gas\output.json"
        
        # Check if file exists first
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"File not found: {file_path}",
                "phone_number": phone_number
            }
        
        # Step 1: Read and parse JSON data
        try:
            with open(file_path, "r", encoding="utf-8") as json_file:
                json_data = json.load(json_file)
            
            print(f"JSON loaded successfully. Target date: {json_data.get('target_date', 'unknown')}")
            print(f"Data entries: {len(json_data.get('data', []))}")
            
        except Exception as file_error:
            return {
                "status": "error", 
                "message": f"Error reading JSON file: {str(file_error)}",
                "phone_number": phone_number
            }
        
        # Step 2: Process data with pandas
        try:
            import pandas as pd
            from app.services.json_utils import format_message_with_styles
            
            # Convert to DataFrame for processing
            df = pd.DataFrame(json_data.get("data", []))
            target_date = json_data.get("target_date", "Data desconhecida")
            
            print(f"DataFrame created with {len(df)} rows")
            if not df.empty:
                print(f"DataFrame columns: {list(df.columns)}")
                print(f"First row sample: {df.iloc[0].to_dict() if len(df) > 0 else 'No data'}")
            
        except Exception as df_error:
            return {
                "status": "error",
                "message": f"Error processing DataFrame: {str(df_error)}",
                "phone_number": phone_number
            }
        
        # Step 3: Format message
        try:
            formatted_message = await format_message_with_styles(df, target_date)
            print(f"Message formatted successfully. Length: {len(formatted_message)} chars")
            
        except Exception as format_error:
            return {
                "status": "error",
                "message": f"Error formatting message: {str(format_error)}",
                "phone_number": phone_number
            }
        
        # Step 4: Send WhatsApp message
        try:
            whatsapp_service = WhatsAppService()
            result = await whatsapp_service.send_message(phone_number, formatted_message)
            
            return {
                "status": "success",
                "message": "Full WhatsApp workflow completed successfully",
                "phone_number": phone_number,
                "target_date": target_date,
                "data_count": len(df),
                "message_length": len(formatted_message),
                "whatsapp_result": result
            }
            
        except Exception as whatsapp_error:
            return {
                "status": "error",
                "message": f"Error sending WhatsApp: {str(whatsapp_error)}",
                "phone_number": phone_number,
                "data_processing": "successful",
                "message_formatting": "successful"
            }
        
    except Exception as e:
        print(f"Error in full test_main_json workflow: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-excel")
async def upload_excel(
    file: UploadFile = File(...),
    target_month: str = Query(None, description="Filter by month (e.g., '01/2025', '02/2025')")
):
    """
    Upload and process Excel file for gas consumption data
    Optional: Filter by specific month
    """
    try:
        print(f"Processing uploaded file: {file.filename}")
        if target_month:
            print(f"Filtering for month: {target_month}")
        
        # Check file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Read file content
        contents = await file.read()
        
        # Process with ExcelService
        excel_service = ExcelService()
        result = excel_service.process_excel_content(contents, file.filename, target_month)
        
        print(f"Excel processed successfully. Data entries: {len(result.get('data', []))}")
        
        return result
        
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/format-message")
async def format_message(request: MessageFormatRequest):
    """
    Format gas consumption data into WhatsApp message
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
            "data_count": len(request.data)
        }
        
    except Exception as e:
        print(f"Error formatting message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/send-whatsapp")
async def send_whatsapp(request: WhatsAppRequest):
    """
    Send WhatsApp message
    """
    try:
        print(f"Sending WhatsApp to: {request.phone_number}")
        
        # Clean message to be ASCII-safe
        clean_message = request.message.encode('ascii', 'ignore').decode('ascii')
        if not clean_message.strip():
            raise HTTPException(status_code=400, detail="Message is empty after cleaning")
        
        whatsapp_service = WhatsAppService()
        result = await whatsapp_service.send_message(request.phone_number, clean_message)
        
        return {
            "status": "success",
            "message": "WhatsApp message sent successfully",
            "phone_number": request.phone_number,
            "whatsapp_result": result
        }
        
    except Exception as e:
        print(f"Error sending WhatsApp: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/get-available-months")
async def get_available_months(file: UploadFile = File(...)):
    """
    Get list of available months from Excel file
    """
    try:
        print(f"Getting available months from: {file.filename}")
        
        # Check file type
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are allowed")
        
        # Read file content
        contents = await file.read()
        
        # Process with ExcelService to get all data
        excel_service = ExcelService()
        result = excel_service.process_excel_content(contents, file.filename, target_month=None)
        
        # Extract unique months from the data
        available_months = set()
        for item in result.get('data', []):
            data_leitura = item.get('data_leitura', '')
            if data_leitura and '/' in data_leitura:
                try:
                    # Parse date DD/MM/YYYY
                    parts = data_leitura.split('/')
                    if len(parts) == 3:
                        month = parts[1]
                        year = parts[2]
                        available_months.add(f"{month}/{year}")
                except Exception:
                    continue
        
        months_list = sorted(list(available_months))
        print(f"Available months: {months_list}")
        
        return {
            "status": "success",
            "available_months": months_list,
            "total_records": len(result.get('data', []))
        }
        
    except Exception as e:
        print(f"Error getting available months: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))