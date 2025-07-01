# frontend/streamlit_app.py
import streamlit as st
import requests
import pandas as pd
# import json

st.set_page_config(
    page_title="Gas Consumption Manager",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏠 Gas Consumption WhatsApp Manager")
st.markdown("---")

# API base URL
API_BASE = "http://localhost:8000/api/v1"

# Initialize session state
if 'gas_data' not in st.session_state:
    st.session_state.gas_data = None

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page",
    ["📊 Upload Data", "👀 Preview Data", "📱 Send WhatsApp"]
)

if page == "📊 Upload Data":
    st.header("📊 Upload Excel File")
    
    # Month selection
    st.subheader("📅 Month Selection")
    col1, col2 = st.columns(2)
    
    with col1:
        month = st.selectbox(
            "Select Month",
            options=["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
            format_func=lambda x: {
                "01": "January", "02": "February", "03": "March", "04": "April",
                "05": "May", "06": "June", "07": "July", "08": "August", 
                "09": "September", "10": "October", "11": "November", "12": "December"
            }[x]
        )
    
    with col2:
        year = st.selectbox(
            "Select Year",
            options=["2024", "2025", "2026"],
            index=1  # Default to 2025
        )
    
    target_month = f"{month}/{year}"
    st.info(f"📅 Selected: {month}/{year}")
    
    uploaded_file = st.file_uploader(
        "Choose Excel file", 
        type=['xlsx', 'xls'],
        help="Upload your gas consumption Excel file"
    )
    
    if uploaded_file:
        with st.spinner("Processing file..."):
            try:
                # Include month parameter in the request
                files = {"file": uploaded_file.getvalue()}
                params = {"target_month": target_month}
                response = requests.post(f"{API_BASE}/upload-excel", files={"file": uploaded_file}, params=params)
                
                if response.status_code == 200:
                    st.session_state.gas_data = response.json()
                    st.success("✅ File processed successfully!")
                    
                    # Show month info
                    st.info(f"📅 Filtered data for: {target_month}")
                    
                    # Show preview
                    df = pd.DataFrame([item for item in st.session_state.gas_data['data']])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

elif page == "👀 Preview Data":
    if st.session_state.gas_data:
        st.header("👀 Data Preview")
        
        data = st.session_state.gas_data
        st.info(f"📅 Target Date: {data['target_date']}")
        
        # Convert data to DataFrame
        df = pd.DataFrame([item for item in data['data']])
        
        # Display data
        st.dataframe(df, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Apartments", len(df))
        with col2:
            total_consumption = df['consumo_m3'].sum()
            st.metric("Total Consumption", f"{total_consumption:.2f} m³")
        with col3:
            total_value = df['valor_final_rs'].sum()
            st.metric("Total Value", f"R$ {total_value:.2f}")
            
    else:
        st.warning("⚠️ Please upload a file first!")

elif page == "📱 Send WhatsApp":
    if st.session_state.gas_data:
        st.header("📱 Send WhatsApp Message")
        
        # Format message preview
        try:
            response = requests.post(
                f"{API_BASE}/format-message",
                json=st.session_state.gas_data
            )
            
            if response.status_code == 200:
                formatted_message = response.json()['formatted_message']
                
                st.subheader("📝 Message Preview")
                st.text_area("Message", formatted_message, height=300, disabled=True)
                
                # Phone number input
                phone = st.text_input(
                    "📞 Phone Number",
                    placeholder="+5531988292853",
                    help="Include country code (e.g., +55 for Brazil)"
                )
                
                if st.button("📤 Send Message", type="primary"):
                    if phone:
                        with st.spinner("Sending message..."):
                            try:
                                send_response = requests.post(
                                    f"{API_BASE}/send-whatsapp",
                                    json={
                                        "phone_number": phone,
                                        "message": formatted_message
                                    }
                                )
                                
                                if send_response.status_code == 200:
                                    st.success("✅ Message sent successfully!")
                                else:
                                    st.error(f"❌ Error sending message: {send_response.text}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    else:
                        st.error("❌ Please enter a phone number")
            else:
                st.error("❌ Error formatting message")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
    else:
        st.warning("⚠️ Please upload and preview data first!")

# Footer
st.markdown("---")
st.markdown("*WhatsApp Gas Consumption Manager v1.0*")