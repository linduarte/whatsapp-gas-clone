import pandas as pd
import json




async def extract_gas_data(
    file_path: str,
    date_column: str,
    apt_column: str,
    last_lecture_column: str,
    value_column: str,
    target_date: str
) -> pd.DataFrame:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Convert the list to a DataFrame
        df = pd.DataFrame(data)

        # Print the first few rows of the DataFrame for debugging
        print("First few rows of the DataFrame:", df.head())

        return df
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        match e:
            case ValueError() as ve:
                print(f"Value error reading JSON: {ve}")
            case _:
                print(f"Other error reading JSON: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error


async def format_message_with_styles(data: pd.DataFrame, target_date: str) -> str:
    # Print columns for debugging
    print(f"DataFrame columns: {list(data.columns)}")
    # Normalize column names (strip, lower, replace spaces with underscores)
    data = data.rename(columns=lambda x: x.strip().lower().replace(" ", "_"))

    # Map expected names to normalized names
    col_map = {
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
    # Header with bold formatting
    message = f"*Consumo de gas e valor a pagar {target_date}*\n\n"
    # Introductory message
    message = (
        "🤖 Esta é uma mensagem automática do sistema de consumo de gás.\n\n" + message
    )
    for index, row in data.iterrows():
        apt = str(row[col_map["apartamento"]]).encode("ascii", "ignore").decode("ascii")
        leitura = (
            str(row[col_map["leitura_atual"]]).encode("ascii", "ignore").decode("ascii")
        )
        consumo = (
            str(row[col_map["consumo_m3"]]).encode("ascii", "ignore").decode("ascii")
        )
        # Format valor_final_rs as 'R$ xx,yy'
        try:
            valor_float = float(row[col_map["valor_final_rs"]])
            valor = (
                f"R$ {valor_float:,.2f}".replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )
        except Exception:
            valor = str(row[col_map["valor_final_rs"]])
        message += f"🏠 Apartamento: *{apt}*\n"
        message += f"📊 Leitura atual: {leitura}\n"
        message += f"⚡ Consumo: _{consumo}_\n"
        message += f"💰 Valor final: *{valor}*\n"
        message += f"{'─' * 25}\n\n"
    message += f"_Relatorio gerado em {target_date}_\n"
    message += f"_Total de apartamentos: {len(data)}_"
    # Remove emojis, mas mantenha acentuação
    import re
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002700-\U000027BF"  # Dingbats
            u"\U000024C2-\U0001F251" 
            "]+",
            flags=re.UNICODE
        )
        return emoji_pattern.sub(r"", text)

    clean_message = remove_emojis(message)
    print("Formatted message with WhatsApp styling:")
    print(f"Original message length: {len(message)}")
    print(f"Cleaned message length: {len(clean_message)}")
    print(f"Preview: {clean_message[:200]}...")
    return clean_message
