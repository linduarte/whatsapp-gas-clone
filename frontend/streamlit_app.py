"""frontend/streamlit_app.py"""

import pandas as pd  # type: ignore[import]
import requests
import streamlit as st

st.set_page_config(
    page_title="Gas Consumption Manager",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏠 Gas Consumption WhatsApp Manager")
st.markdown("---")

# API base URL
API_BASE = "http://localhost:8000/api/v1"

# Centralização Segura e Limpa do Estado Global da Aplicação
if "gas_data" not in st.session_state:
    st.session_state.gas_data = None
if "selected_month_str" not in st.session_state:
    st.session_state.selected_month_str = ""

# Menu Lateral de Navegação
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page", ["📊 Upload Data", "👀 Preview Data", "📱 Send WhatsApp"]
)

# ---------------------------------------------------------------------------------
# ABA 1: UPLOAD DE DADOS
# ---------------------------------------------------------------------------------
if page == "📊 Upload Data":
    st.header("📊 Upload Excel File")

    st.subheader("📅 Month Selection")
    col1, col2 = st.columns(2)

    with col1:
        month = st.selectbox(
            "Select Month",
            options=[
                "01",
                "02",
                "03",
                "04",
                "05",
                "06",
                "07",
                "08",
                "09",
                "10",
                "11",
                "12",
            ],
            format_func=lambda x: {
                "01": "January",
                "02": "February",
                "03": "March",
                "04": "April",
                "05": "May",
                "06": "June",
                "07": "July",
                "08": "August",
                "09": "September",
                "10": "October",
                "11": "November",
                "12": "December",
            }[x],
        )

    with col2:
        year = st.selectbox(
            "Select Year",
            options=["2024", "2025", "2026"],
            index=2,  # Aponta dinamicamente para o ano corrente de 2026
        )

    TARGET_MONTH = f"{month}/{year}"
    st.session_state.selected_month_str = TARGET_MONTH
    st.info(f"📅 Selected: {TARGET_MONTH}")

    uploaded_file = st.file_uploader(
        "Choose Excel file",
        type=["xlsx", "xls"],
        help="Upload your gas consumption Excel file",
    )

    if uploaded_file:
        with st.spinner("Processing file..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                params = {"target_month": TARGET_MONTH}
                response = requests.post(
                    f"{API_BASE}/upload-excel",
                    files=files,
                    params=params,
                    timeout=30,
                )

                if response.status_code == 200:
                    st.session_state.gas_data = response.json()
                    st.success("✅ File processed successfully!")
                    st.info(f"📅 Filtered data for: {TARGET_MONTH}")

                    # Extrai os dados internos para exibição imediata
                    dados_internos = st.session_state.gas_data.get("data", [])
                    if dados_internos:
                        df = pd.DataFrame(dados_internos)
                        if "valor_final_rs" in df.columns:
                            df["valor_final_rs"] = df["valor_final_rs"].apply(
                                lambda x: f"{float(x):.2f}"
                            )
                        st.dataframe(df, width="stretch")
                    else:
                        st.warning("⚠️ No data found matching the filters.")
                else:
                    st.error(f"❌ Error: {response.text}")
            except requests.RequestException as e:
                st.error(f"❌ Network error processing file: {str(e)}")
            except ValueError as e:
                st.error(f"❌ Invalid response content: {str(e)}")

# ---------------------------------------------------------------------------------
# ABA 2: VISUALIZAÇÃO E SUMÁRIO ESTATÍSTICO
# ---------------------------------------------------------------------------------
elif page == "👀 Preview Data":
    if st.session_state.gas_data and "data" in st.session_state.gas_data:
        st.header("👀 Data Preview")

        data = st.session_state.gas_data
        data_alvo = data.get("target_date", st.session_state.selected_month_str)
        st.info(f"📅 Target Month: {data_alvo}")

        df = pd.DataFrame(data["data"])

        df_display = df.copy()
        if "valor_final_rs" in df_display.columns:
            df_display["valor_final_rs"] = df_display["valor_final_rs"].apply(
                lambda x: f"{float(x):.2f}"
            )

        st.dataframe(df_display, width="stretch")

        # Seção de Métricas Consolidadas (Conversão segura para Float)
        st.subheader("📈 Summary Statistics")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Apartments", len(df))
        with col2:
            total_consumption = pd.to_numeric(df["consumo_m3"], errors="coerce").sum()
            st.metric("Total Consumption", f"{total_consumption:.3f} m³")
        with col3:
            total_value = pd.to_numeric(df["valor_final_rs"], errors="coerce").sum()
            st.metric("Total Value", f"R$ {total_value:.2f}")
    else:
        st.warning("⚠️ Please upload an Excel file first!")

# ---------------------------------------------------------------------------------
# ABA 3: ENVIO AUTOMATIZADO VIA PLAYWRIGHT
# ---------------------------------------------------------------------------------
elif page == "📱 Send WhatsApp":
    if st.session_state.gas_data and "data" in st.session_state.gas_data:
        st.header("📱 Send WhatsApp Message")

        try:
            # Pegamos os dados que já foram validados e processados pelo upload
            dados_lista = st.session_state.gas_data.get("data", [])
            data_alvo = st.session_state.gas_data.get(
                "target_date", st.session_state.selected_month_str
            )

            # Montamos a mensagem diretamente no frontend, evitando erros 422 de API
            message_lines = [
                "🤖 Esta é uma mensagem automática do sistema de consumo de gás.\n",
                f"*Consumo de gás e valor a pagar - {data_alvo}*\n",
            ]

            for item in dados_lista:
                apt = str(item.get("apartamento", ""))
                leitura = str(item.get("leitura_atual", ""))
                consumo = str(item.get("consumo_m3", ""))

                try:
                    valor_float = float(item.get("valor_final_rs", 0))
                    VALOR_STR = (
                        f"R$ {valor_float:,.2f}".replace(",", "X")
                        .replace(".", ",")
                        .replace("X", ".")
                    )
                except (ValueError, TypeError):
                    VALOR_STR = str(item.get("valor_final_rs", ""))

                message_lines.append(f"🏠 Apartamento: *{apt}*")
                message_lines.append(f"📊 Leitura atual: {leitura}")
                message_lines.append(f"⚡ Consumo: _{consumo}_ m³")
                message_lines.append(f"💰 Valor final: *{VALOR_STR}*")
                message_lines.append(f"{'─' * 25}\n")

            message_lines.append(f"_Relatório gerado em {data_alvo}_")
            message_lines.append(f"_Total de apartamentos: {len(dados_lista)}_")
            FORMATTED_MESSAGE = "\n".join(message_lines)

            st.subheader("📝 Message Preview")
            # Exibe a mensagem gerada localmente pronta para edição ou envio
            mensagem_final = st.text_area(
                "Message Editor", FORMATTED_MESSAGE, height=250
            )

            col_phone, col_btn = st.columns([2, 1])
            with col_phone:
                phone = st.text_input(
                    "📞 Phone Number",
                    placeholder="Ex: 31988887777",
                    help="Insira o número com o DDD. O sistema ajustará o código do país automaticamente.",
                )

            with col_btn:
                st.markdown("<br>", unsafe_allow_html=True)
                botao_disparo = st.button(
                    "📤 Launch WhatsApp Automation", type="primary"
                )

            if botao_disparo:
                if phone:
                    # Limpa caracteres não numéricos do telefone (espaços, traços, parênteses)
                    phone_clean = "".join(filter(str.isdigit, phone))
                    
                    # Se o usuário digitou 11 dígitos (ex: 31988292853), adiciona o código do Brasil (55)
                    if len(phone_clean) == 11:
                        phone_clean = f"55{phone_clean}"
                        
                    with st.spinner("🚀 Solicitando disparo ao servidor de automação..."):
                        try:
                            api_base = "http://127.0.0.1:8000/api/v1"
                            
                            send_response = requests.post(
                                f"{api_base}/send-whatsapp",
                                json={
                                    "phone_number": phone_clean,  # Envia o número já formatado com 55
                                    "message": mensagem_final,
                                },
                                timeout=300,  # 5 minutos
                            )

                            if send_response.status_code == 200:
                                st.success("🎉 Processo concluído com sucesso! Relatório transmitido.")
                            else:
                                st.error(f"❌ Falha no servidor de automação: {send_response.text}")
                        except requests.RequestException as req_err:
                            st.error(f"❌ Erro de conexão com o backend: {str(req_err)}")
                else:
                    st.error("❌ Please enter a phone number.")
        except (KeyError, TypeError, ValueError) as e:
            st.error(f"❌ Error generating message: {str(e)}")
    else:
        st.warning("⚠️ Please upload and preview data first!")

# Footer - Fim definitivo do arquivo streamlit_app.py
st.markdown("---")
st.markdown("*WhatsApp Gas Consumption Manager v2.0 • Playwright Engine via API*")
