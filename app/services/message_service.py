# app/services/message_service.py
from app.services.json_utils import format_message_with_styles
import pandas as pd

class MessageService:
    async def format_message_with_styles(self, filtered_df: pd.DataFrame, target_date: str):
        """FastAPI wrapper for your existing json_utils.py"""
        # Direct call to your existing function
        return await format_message_with_styles(filtered_df, target_date)