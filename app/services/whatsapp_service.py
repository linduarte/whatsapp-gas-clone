# app/services/whatsapp_service.py
from multiprocessing import Process, Event


from typing import Any

class WhatsAppService:
    async def send_message(self, phone_number: str, message: str) -> dict[str, Any]:
        """FastAPI wrapper for full WhatsApp automation with greeting, with extra logging for debugging."""
        try:
            # Clean the message to prevent emoji encoding issues
            clean_message = message.encode("ascii", "ignore").decode("ascii")
            if not clean_message.strip():
                clean_message = "Gas consumption data message"

            print(f"[WHATSAPP SERVICE] Starting full WhatsApp workflow for {phone_number}")
            print(f"[WHATSAPP SERVICE] Original message length: {len(message)} chars")
            print(f"[WHATSAPP SERVICE] Cleaned message length: {len(clean_message)} chars")

            # Start process and return immediately (fire and forget)
            from app.services.whatsapp_automation import run_send_whatsapp_with_greeting

            stop_event = Event()
            p = Process(
                target=run_send_whatsapp_with_greeting,
                args=(phone_number, clean_message, stop_event),
            )
            p.start()

            print(f"[WHATSAPP SERVICE] WhatsApp process started with PID: {p.pid}")
            # Wait briefly to check if process is alive
            import time
            time.sleep(2)
            if not p.is_alive():
                print("[WHATSAPP SERVICE][ERROR] WhatsApp process exited early. Check logs for details.")
                return {
                    "status": "error",
                    "message": "WhatsApp process failed to start. Check backend logs for details.",
                    "pid": p.pid,
                }

            return {
                "status": "sent",
                "message": "WhatsApp automation started successfully",
                "pid": p.pid,
            }

        except Exception as e:
            print(f"[WHATSAPP SERVICE][ERROR] Error in send_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "message": f"Exception in send_message: {str(e)}"
            }

    async def send_test_message(self, phone_number: str, message: str) -> dict[str, Any]:
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
            match e:
                case ValueError() as ve:
                    raise Exception(f"Failed to send test WhatsApp (value error): {ve}")
                case _:
                    raise Exception(f"Failed to send test WhatsApp: {str(e)}")
