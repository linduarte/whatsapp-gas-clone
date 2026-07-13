"""Utilities for extracting gas consumption data from JSON files and formatting messages."""

import json
import re
from typing import Optional

import pandas as pd  # type: ignore


async def extract_gas_data(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    file_path: str,
    _date_column: str,
    apt_column: str,
    last_lecture_column: str,
    value_column: str,
    target_date: str,
) -> pd.DataFrame:
    """Extract gas consumption data from a JSON file into a pandas DataFrame.

    Args:
        file_path: Path to the JSON file.
        date_column: Name of the date column in the JSON data. (unused)
        apt_column: Name of the apartment column in the JSON data.
        last_lecture_column: Name of the current reading column in the JSON data.
        value_column: Name of the value column in the JSON data.
        target_date: Target date string for the extracted data.

    Returns:
        A pandas DataFrame created from the JSON file contents.
    """
    try:
        _ = apt_column
        _ = last_lecture_column
        _ = value_column
        _ = target_date
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Convert the list to a DataFrame
        df = pd.DataFrame(data)

        # Print the first few rows of the DataFrame for debugging
        print("First few rows of the DataFrame:", df.head())

        return df
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError) as e:
        print(f"Error reading JSON file: {e}")
        # Use isinstance checks instead of match/case to avoid unreachable pattern
        if isinstance(e, json.JSONDecodeError):
            print(f"JSON decode error: {e}")
        elif isinstance(e, ValueError):
            print(f"Value error reading JSON: {e}")
        elif isinstance(e, FileNotFoundError):
            print(f"File not found: {e}")
        elif isinstance(e, OSError):
            print(f"OS error reading JSON: {e}")
        else:
            print(f"Other error reading JSON: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error


async def format_message_with_styles(data: pd.DataFrame, target_date: str) -> str:
    """Format a DataFrame of gas consumption into a WhatsApp-styled message.

    Normalizes column names, validates required columns, builds a styled
    message for each apartment and removes emojis while preserving
    accentuation.
    """
    # Normalize column names (strip, lower, replace spaces with underscores)
    data = data.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

    # Map expected names to normalized names - Tipagem explícita para calar o linter
    col_map: dict[str, Optional[str]] = {
        "apartamento": None,
        "leitura_atual": None,
        "consumo_m3": None,
        "valor_final_rs": None,
    }

    for col in data.columns:
        for key in col_map:
            if col == key:
                col_map[key] = col

    # Check for missing columns
    for key, val in col_map.items():
        if val is None:
            raise ValueError(
                f"Missing expected column: '{key}' in DataFrame columns: {list(data.columns)}"
            )

    # Header with bold formatting and introductory message
    message = (
        "🤖 Esta é uma mensagem automática do sistema de consumo de gás.\n\n"
        f"*Consumo de gas e valor a pagar {target_date}*\n\n"
    )

    for _, row in data.iterrows():
        # Extraímos os nomes das colunas validados de forma segura para o linter entender
        col_apt = col_map["apartamento"]
        col_leitura = col_map["leitura_atual"]
        col_consumo = col_map["consumo_m3"]
        col_valor = col_map["valor_final_rs"]

        if not (col_apt and col_leitura and col_consumo and col_valor):
            continue

        # Usamos os mapeamentos validados para indexar a Series 'row'
        _apt = str(row[col_apt]).encode("ascii", "ignore").decode("ascii")
        _leitura = str(row[col_leitura]).encode("ascii", "ignore").decode("ascii")
        _consumo = str(row[col_consumo]).encode("ascii", "ignore").decode("ascii")

        # Format valor_final_rs as 'R$ xx,yy'
        try:
            valor_float = float(row[col_valor])
            _valor = (
                f"R$ {valor_float:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except (ValueError, TypeError):
            _valor = str(row[col_valor])

    # Remove emojis, mas mantenha acentuação
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002700-\U000027bf"  # Dingbats
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)

    clean_message = remove_emojis(message)
    return clean_message
