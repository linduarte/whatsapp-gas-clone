"""Utilities for extracting gas consumption data from JSON files and formatting messages."""

import re
from typing import Optional

import pandas as pd


async def format_message_with_styles(data: pd.DataFrame, target_date: str) -> str:
    """Format dataframe records into a clean, structured WhatsApp message."""
    print(f"DataFrame columns received by backend: {list(data.columns)}")

    # Normaliza o nome das colunas eliminando espaços e aplicando letras minúsculas
    data = data.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

    # Como as chaves já vêm saneadas pelo Pydantic, o mapa fica direto e sem risco de erro
    col_map: dict[str, Optional[str]] = {
        "apartamento": "apartamento",
        "leitura_atual": "leitura_atual",
        "consumo_m3": "consumo_m3",
        "valor_final_rs": "valor_final_rs",
    }

    for col in data.columns:
        for key in col_map:
            if col == key:
                col_map[key] = col

    # Validação rigorosa das colunas obrigatórias
    for key, val in col_map.items():
        if val is None:
            raise ValueError(
                f"Missing expected column: '{key}' in DataFrame columns: {list(data.columns)}"
            )

    # Montagem do cabeçalho estruturado da mensagem
    message = (
        "🤖 Esta é uma mensagem automática do sistema de consumo de gás.\n\n"
        f"*Consumo de gás e valor a pagar - {target_date}*\n\n"
    )

    # Varre as linhas remontando a string final com as máscaras visuais
    for _, row in data.iterrows():
        col_apt = col_map["apartamento"]
        col_leitura = col_map["leitura_atual"]
        col_consumo = col_map["consumo_m3"]
        col_valor = col_map["valor_final_rs"]

        if not (col_apt and col_leitura and col_consumo and col_valor):
            continue

        apt = str(row[col_apt]).encode("ascii", "ignore").decode("ascii")
        leitura = str(row[col_leitura]).encode("ascii", "ignore").decode("ascii")
        consumo = str(row[col_consumo]).encode("ascii", "ignore").decode("ascii")

        # Tratamento e conversão da moeda nacional (R$ xx,yy)
        try:
            valor_float = float(row[col_valor])
            valor = (
                f"R$ {valor_float:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except (ValueError, TypeError):
            valor = str(row[col_valor])

        # Incrementa o corpo do texto de forma incremental
        message += f"🏠 Apartamento: *{apt}*\n"
        message += f"📊 Leitura atual: {leitura}\n"
        message += f"⚡ Consumo: _{consumo}_ m³\n"
        message += f"💰 Valor final: *{valor}*\n"
        message += f"{'─' * 25}\n\n"

    message += f"_Relatório gerado em {target_date}_\n"
    message += f"_Total de apartamentos: {len(data)}_"

    # Função interna isolada para higienização de caracteres especiais de emojis
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "["
            r"\U0001F600-\U0001F64F"  # emoticons
            r"\U0001F300-\U0001F5FF"  # symbols & pictographs
            r"\U0001F680-\U0001F6FF"  # transport & map symbols
            r"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            r"\U00002700-\U000027BF"  # Dingbats
            r"\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub(r"", text)

    clean_message = remove_emojis(message)
    print(f"✅ Message formatted successfully. Total length: {len(clean_message)}")
    return clean_message
