"""frontend/streamlit_app.py"""

import asyncio

import pandas as pd  # type: ignore
import requests
import streamlit as st

from app.services.whatsapp_automation import send_whatsapp_with_playwright

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
                        st.dataframe(df, use_container_width=True)
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

        st.dataframe(df_display, use_container_width=True)

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
            # Consome a rota do backend para buscar o template de mensagem estruturado
            response = requests.post(
                f"{API_BASE}/format-message",
                json=st.session_state.gas_data,
                timeout=15,
            )

            if response.status_code == 200:
                formatted_message = response.json().get("formatted_message", "")

                st.subheader("📝 Message Preview")
                # Exibimos em text_area para revisão, mas liberado para pequenos ajustes manuais se você quiser
                mensagem_final = st.text_area(
                    "Message Editor", formatted_message, height=250
                )

                col_phone, col_btn = st.columns([2, 1])
                with col_phone:
                    phone = st.text_input(
                        "📞 Phone Number",
                        placeholder="Ex: 31988887777",
                        help="Insira o número com o DDD. O sistema ajustará o código do país automaticamente.",
                    )

                with col_btn:
                    st.markdown(
                        "<br>", unsafe_allow_html=True
                    )  # Alinhamento vertical do botão com o input
                    botao_disparo = st.button(
                        "📤 Launch WhatsApp Automation", type="primary"
                    )

                if botao_disparo:
                    if phone and mensagem_final:
                        # Cria uma caixa de feedback em tempo real controlada pelo Playwright
                        status_logger = st.info("Iniciando motores da automação...")

                        # Callback dinâmico para atualizar o Streamlit direto de dentro do loop assíncrono
                        def log_callback(texto):
                            """Callback to write status updates into the Streamlit status logger.

                            Args:
                                texto: Text to write to the status logger.
                            """
                            status_logger.write(f"🤖 {texto}")

                        # Executa o loop assíncrono do Playwright de forma isolada e segura
                        sucesso = asyncio.run(
                            send_whatsapp_with_playwright(
                                phone=phone,
                                message=mensagem_final,
                                status_callback=log_callback,
                            )
                        )

                        if sucesso:
                            status_logger.success(
                                "🎉 Processo concluído com sucesso! Relatório transmitido."
                            )
                        else:
                            status_logger.error(
                                "❌ Falha na automação. Verifique os logs no terminal para análise."
                            )
                    else:
                        st.error("❌ Please enter a phone number and message.")
            else:
                st.error("❌ Error formatting message templates via Backend.")
        except requests.RequestException as e:
            st.error(f"❌ Network error while contacting backend: {str(e)}")
        except ValueError as e:
            st.error(f"❌ Invalid response content: {str(e)}")
    else:
        st.warning("⚠️ Please upload and preview data first!")

st.markdown("---")
st.markdown("*WhatsApp Gas Consumption Manager v2.0 • Playwright Engine*")
