# app/services/message_service.py
from app.services.json_utils import format_message_with_styles
import pandas as pd


class MessageService:
    """
    Service for formatting messages using DataFrame and a target date.
    """
    async def format_message_with_styles(
        self, filtered_df: pd.DataFrame, target_date: str
    ) -> str:
        """FastAPI wrapper for your existing json_utils.py"""
        return await format_message_with_styles(filtered_df, target_date)
