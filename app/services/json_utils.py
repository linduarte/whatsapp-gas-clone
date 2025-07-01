import pandas as pd
import json


async def extract_gas_data(
    file_path, date_column, apt_column, last_lecture_column, value_column, target_date
):
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
        return pd.DataFrame()  # Return an empty DataFrame on error


async def format_message_with_styles(data, target_date):
    # Format message with WhatsApp styling (bold, italic) using ASCII-safe characters
    
    # Header with bold formatting
    message = f"*Consumo de gas e valor a pagar {target_date}*\n\n"
    
    for index, row in data.iterrows():
        # Clean the data to use ASCII-safe characters
        apt = str(row['Apartamento']).encode('ascii', 'ignore').decode('ascii')
        leitura = str(row['Leitura atual']).encode('ascii', 'ignore').decode('ascii')
        consumo = str(row['Consumo(m³)']).replace('³', '3').encode('ascii', 'ignore').decode('ascii')
        valor = str(row['Valor final(R$)']).encode('ascii', 'ignore').decode('ascii')
        
        # Format with WhatsApp styling:
        # - Bold for apartment number and value
        # - Regular text for labels
        # - Clean line separation
        message += f"🏠 Apartamento: *{apt}*\n"
        message += f"📊 Leitura atual: {leitura}\n"
        message += f"⚡ Consumo: _{consumo}_\n"
        message += f"💰 Valor final: *{valor}*\n"
        message += f"{'─' * 25}\n\n"  # Separator line
    
    # Footer with italic text
    message += f"_Relatorio gerado em {target_date}_\n"
    message += f"_Total de apartamentos: {len(data)}_"
    
    # Clean the entire message to ensure no problematic characters remain
    clean_message = message.encode('ascii', 'ignore').decode('ascii')
    
    print("Formatted message with WhatsApp styling:")
    print(f"Original message length: {len(message)}")
    print(f"Cleaned message length: {len(clean_message)}")
    print(f"Preview: {clean_message[:200]}...")
    
    return clean_message
