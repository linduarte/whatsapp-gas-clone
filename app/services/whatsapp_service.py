# app/services/whatsapp_service.py
from multiprocessing import Process, Event


class WhatsAppService:
    async def send_message(self, phone_number: str, message: str):
        """FastAPI wrapper for full WhatsApp automation with greeting"""
        try:
            # Clean the message to prevent emoji encoding issues
            clean_message = message.encode("ascii", "ignore").decode("ascii")
            if not clean_message.strip():
                clean_message = "Gas consumption data message"

            print(f"Starting full WhatsApp workflow for {phone_number}")
            print(f"Original message length: {len(message)} chars")
            print(f"Cleaned message length: {len(clean_message)} chars")

            # Start process and return immediately (fire and forget)
            from app.services.whatsapp_automation import run_send_whatsapp_with_greeting

            stop_event = Event()
            p = Process(
                target=run_send_whatsapp_with_greeting,
                args=(phone_number, clean_message, stop_event),
            )
            p.start()

            print(f"WhatsApp process started with PID: {p.pid}")
            return {
                "status": "sent",
                "message": "WhatsApp automation started successfully",
                "pid": p.pid,
            }

        except Exception as e:
            print(f"Error in send_message: {str(e)}")
            import traceback

            traceback.print_exc()
            raise Exception(f"Failed to send WhatsApp: {str(e)}")

    async def send_test_message(self, phone_number: str, message: str):
        """FastAPI wrapper for simple test message (no greeting sequence)"""
        try:
            print(f"Starting test message for {phone_number}")

            # Start process and return immediately (fire and forget)
            from app.services.whatsapp_automation import run_send_simple_test_message

            stop_event = Event()
            p = Process(
                target=run_send_simple_test_message,
                args=(phone_number, message, stop_event),
            )
            p.start()

            print(f"Test process started with PID: {p.pid}")
            return {
                "status": "sent",
                "message": "WhatsApp test started successfully",
                "pid": p.pid,
            }

        except Exception as e:
            print(f"Error in send_test_message: {str(e)}")
            import traceback

            traceback.print_exc()
            raise Exception(f"Failed to send test WhatsApp: {str(e)}")
