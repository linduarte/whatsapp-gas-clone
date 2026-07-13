# app/services/message_service.py
"""MessageService: helpers to format messages for the application.

This module provides an async wrapper around the json_utils.format_message_with_styles
function so it can be used from FastAPI endpoints.
"""

import pandas as pd

from app.services.json_utils import format_message_with_styles


class MessageService:
    """
    Service for formatting messages using DataFrame and a target date.
    """

    async def format_message_with_styles(
        self, filtered_df: pd.DataFrame, target_date: str
    ) -> str:
        """FastAPI wrapper for your existing json_utils.py"""
        return await format_message_with_styles(filtered_df, target_date)
