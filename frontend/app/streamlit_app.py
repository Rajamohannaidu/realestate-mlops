# app/streamlit_app.py - API-Based Integration

from dotenv import load_dotenv
from pathlib import Path
import os
import sys
from datetime import datetime
import requests
import json

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# CRITICAL: Page config must be the FIRST Streamlit command
st.set_page_config(
    page_title="AI Real Estate Advisor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/real-estate-ai',
        'Report a bug': "https://github.com/yourusername/real-estate-ai/issues",
        'About': "# AI Real Estate Investment Advisor\nPowered by Machine Learning & AI"
    }
)

# ============================================================================
# API Configuration
# ============================================================================

# Get backend URL from environment or use default
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8080')

# Ensure URL doesn't have trailing slash
BACKEND_URL = BACKEND_URL.rstrip('/')

logger_info = f"Backend URL: {BACKEND_URL}"
print(f"✓ {logger_info}")

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def check_backend_ready():
    """Check if backend models are loaded"""
    try:
        response = requests.get(f"{BACKEND_URL}/ready", timeout=5)
        return response.status_code == 200
    except Exception as e:
        return False

def call_backend_api(endpoint, method="GET", data=None):
    """Helper function to call backend API"""
    try:
        url = f"{BACKEND_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            raise Exception(f"API Error {response.status_code}: {error_detail}")
    except requests.exceptions.Timeout:
        raise Exception("Backend request timed out. Models may still be loading...")
    except Exception as e:
        raise Exception(f"Backend API Error: {str(e)}")

# Custom CSS for modern design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding: 2rem 3rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        margin: 2rem auto;
        max-width: 1400px;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] * { color: white !important; }
    
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 3rem !important;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    h2 {
        color: #2d3748;
        font-weight: 600;
        font-size: 1.8rem !important;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        color: white;
        margin: 1rem 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.4);
    }
    
    .info-card {
        background: linear-gradient(135deg, #f6f8fb 0%, #ffffff 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        margin: 1rem 0;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .feature-card:hover {
        border-color: #667eea;
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .success-box {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: #065f46;
        font-weight: 500;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: #92400e;
        font-weight: 500;
        margin: 1rem 0;
    }
    
    .info-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: #1e3a8a;
        font-weight: 500;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Backend Status Check
# ============================================================================

backend_ok = check_backend_health()

if not backend_ok:
    st.error("🚨 Backend Service Unavailable")
    st.markdown("""
    ### Unable to Connect to Backend
    
    The FastAPI backend is not responding. Please check:
    
    1. **Backend is running:** Verify the backend container is up
    2. **Correct URL:** Current backend URL: `""" + BACKEND_URL + """`
    3. **Environment variable:** Set `BACKEND_URL` if needed
    4. **Network connectivity:** Check if services can communicate
    
    **For local development:**
    ```bash
    # Terminal 1: Start backend
    cd backend
    uvicorn src.api.main:app --reload --port 8080
    
    # Terminal 2: Start frontend
    cd frontend
    streamlit run app/streamlit_app.py
    ```
    """)
    st.stop()

# Check if models are loaded
models_ready = check_backend_ready()

# Initialize session state
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏡 Home"

if 'predicted_price' not in st.session_state:
    st.session_state.predicted_price = None

if 'prediction_made' not in st.session_state:
    st.session_state.prediction_made = False

# Sidebar
with st.sidebar:
    st.markdown("### 🏠 AI Real Estate Advisor")
    st.markdown("---")
    
    # Backend Status
    if models_ready:
        st.markdown('<div class="success-box">✅ Backend Ready</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="warning-box">⏳ Loading Models...</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    page = st.radio(
        "Navigate",
        [
            "🏡 Home",
            "🔮 Price Prediction",
            "💰 Investment Analysis",
            "📊 Model Status"
        ],
        label_visibility="collapsed"
    )
    
    st.session_state.current_page = page
    
    st.markdown("---")
    st.markdown("### 📊 Quick Stats")
    st.markdown("""
    <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px;">
        <p style="margin:0.3rem 0; font-size:0.9rem; color:white;"><strong>Backend:</strong> Available</p>
        <p style="margin:0.3rem 0; font-size:0.9rem; color:white;"><strong>Models:</strong> Ready</p>
        <p style="margin:0.3rem 0; font-size:0.9rem; color:white;"><strong>API Version:</strong> 1.0</p>
    </div>
    """, unsafe_allow_html=True)

# Main Pages
if page == "🏡 Home":
    st.markdown("<h1>🏠 AI Real Estate Investment Advisor</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3 style="margin-top:0;">🎯 Make Smarter Property Investment Decisions</h3>
        <p style="font-size:1.1rem; margin-bottom:0;">
            Leverage machine learning and AI to predict property prices, analyze investments, 
            and get expert guidance—all in one platform.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🔮 Price Prediction</h3>
            <p>Get accurate property valuations using advanced ML models.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>💰 Investment Analytics</h3>
            <p>Comprehensive ROI analysis and investment metrics.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Market Insights</h3>
            <p>Understand model decisions with explainability tools.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if st.button("🚀 Start Predicting Now", use_container_width=True):
            st.session_state.current_page = "🔮 Price Prediction"
            st.rerun()

elif page == "🔮 Price Prediction":
    st.markdown("<h1>🔮 Property Price Prediction</h1>", unsafe_allow_html=True)
    
    if not models_ready:
        st.warning("⏳ Models are still loading. Please wait...")
        st.stop()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<h3>📝 Property Specifications</h3>", unsafe_allow_html=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            area = st.number_input("🏠 Area (sq ft)", 1000, 20000, 5000, 100)
            bedrooms = st.number_input("🛏️ Bedrooms", 1, 6, 3)
        with col_b:
            bathrooms = st.number_input("🚿 Bathrooms", 1, 4, 2)
            stories = st.number_input("🏢 Stories", 1, 4, 2)
        
        st.markdown("---")
        col_c, col_d = st.columns(2)
        with col_c:
            mainroad = st.selectbox("🛣️ Main Road", ["yes", "no"])
            guestroom = st.selectbox("👥 Guest Room", ["yes", "no"])
            basement = st.selectbox("⬇️ Basement", ["yes", "no"])
        with col_d:
            hotwaterheating = st.selectbox("♨️ Hot Water", ["yes", "no"])
            airconditioning = st.selectbox("❄️ AC", ["yes", "no"])
            prefarea = st.selectbox("⭐ Preferred Area", ["yes", "no"])
        
        parking = st.number_input("🚗 Parking", 0, 3, 2)
        furnishingstatus = st.selectbox("🪑 Furnishing", 
                                       ["furnished", "semi-furnished", "unfurnished"])
        
        predict_button = st.button("🔮 Predict Price", type="primary", use_container_width=True)
    
    with col2:
        st.markdown("<h3>📊 Results</h3>", unsafe_allow_html=True)
        
        if predict_button:
            try:
                with st.spinner("🔄 Analyzing property..."):
                    # Call backend API
                    payload = {
                        "area": area,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "stories": stories,
                        "mainroad": mainroad,
                        "guestroom": guestroom,
                        "basement": basement,
                        "hotwaterheating": hotwaterheating,
                        "airconditioning": airconditioning,
                        "parking": parking,
                        "prefarea": prefarea,
                        "furnishingstatus": furnishingstatus
                    }
                    
                    result = call_backend_api("/predict", "POST", payload)
                    
                    st.session_state.predicted_price = result['predicted_price']
                    st.session_state.prediction_made = True
                
                st.markdown("""
                <div class="success-box">
                    <h2 style="margin:0; color:#065f46;">✅ Prediction Complete!</h2>
                </div>
                """, unsafe_allow_html=True)
                
                col_x, col_y, col_z = st.columns(3)
                with col_x:
                    st.metric("💰 Predicted Price", f"₹{result['predicted_price']:,.0f}")
                with col_y:
                    st.metric("📏 Price/Sq Ft", f"₹{result['price_per_sqft']:,.0f}")
                with col_z:
                    st.metric("📊 Model", result['model_used'])
                
                # Confidence interval
                if result.get('confidence_interval_lower'):
                    st.markdown(f"""
                    <div class="info-card">
                        <strong>95% Confidence Interval:</strong><br>
                        ₹{result['confidence_interval_lower']:,.0f} - ₹{result['confidence_interval_upper']:,.0f}
                    </div>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Prediction failed: {str(e)}")
        
        else:
            st.markdown("""
            <div class="info-card" style="text-align:center; padding:3rem;">
                <h3>👈 Enter property details</h3>
                <p>Fill in the form to get your prediction</p>
                <div style="font-size:4rem; opacity:0.3;">🏠</div>
            </div>
            """, unsafe_allow_html=True)

elif page == "💰 Investment Analysis":
    st.markdown("<h1>💰 Investment Analysis</h1>", unsafe_allow_html=True)
    
    if not models_ready:
        st.warning("⏳ Models are still loading. Please wait...")
        st.stop()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<h3>📊 Investment Parameters</h3>", unsafe_allow_html=True)
        
        with st.form("investment_form"):
            purchase_price = st.number_input("💵 Purchase Price (₹)", 1000000, 50000000, 5000000, 100000)
            monthly_rental = st.number_input("🏠 Monthly Rental (₹)", 0, 500000, 25000, 1000)
            annual_tax = st.number_input("📋 Annual Tax (₹)", 0, 1000000, 50000, 5000)
            annual_insurance = st.number_input("🛡️ Annual Insurance (₹)", 0, 500000, 25000, 1000)
            annual_maintenance = st.number_input("🔧 Annual Maintenance (₹)", 0, 500000, 30000, 1000)
            
            holding_period = st.slider("📅 Holding Period (years)", 1, 30, 5)
            
            calculate_button = st.form_submit_button("📊 Analyze", use_container_width=True)
    
    with col2:
        st.markdown("<h3>📈 Analysis Results</h3>", unsafe_allow_html=True)
        
        if calculate_button:
            try:
                with st.spinner("🔄 Analyzing..."):
                    payload = {
                        "purchase_price": purchase_price,
                        "monthly_rental_income": monthly_rental,
                        "annual_property_tax": annual_tax,
                        "annual_insurance": annual_insurance,
                        "annual_maintenance": annual_maintenance,
                        "holding_period_years": holding_period,
                        "down_payment_percent": 20,
                        "loan_interest_rate": 7.5,
                        "loan_term_years": 30,
                        "vacancy_rate": 5,
                        "annual_appreciation_rate": 3
                    }
                    
                    result = call_backend_api("/analyze", "POST", payload)
                
                st.markdown("""
                <div class="success-box">
                    <h3 style="margin:0;">✅ Analysis Complete!</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("💹 ROI", f"{result['roi']:.2f}%")
                    st.metric("📈 Cap Rate", f"{result['cap_rate']:.2f}%")
                with col_m2:
                    st.metric("🏠 Rental Yield", f"{result['rental_yield']:.2f}%")
                    st.metric("💰 Cash Flow", f"₹{result['cash_flow_annual']:,.0f}/yr")
                
                st.markdown(f"""
                <div class="info-card">
                    <strong>Investment Grade:</strong> {result['investment_grade']}<br>
                    <strong>Recommendation:</strong> {result['recommendation']}
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")

elif page == "📊 Model Status":
    st.markdown("<h1>📊 Backend Status</h1>", unsafe_allow_html=True)
    
    try:
        status = call_backend_api("/models/status", "GET")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="feature-card">
                <h4>✅ Status</h4>
                <p><strong>Models Loaded:</strong> {status['models_loaded']}</p>
                <p><strong>Preprocessor:</strong> {status['preprocessor_loaded']}</p>
                <p><strong>Analytics:</strong> {status['analytics_available']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="feature-card">
                <h4>ℹ️ Details</h4>
                <p><strong>Last Loaded:</strong> {status['last_loaded']}</p>
                {f"<p><strong>Error:</strong> {status['error_message']}</p>" if status['error_message'] else ""}
            </div>
            """, unsafe_allow_html=True)
        
        if status.get('model_info'):
            st.markdown(f"""
            <div class="info-card">
                <h4>Model Information</h4>
                {json.dumps(status['model_info'], indent=2)}
            </div>
            """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Failed to get status: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align:center; padding:1rem; color:#718096; font-size:0.85rem;">
    <p>🏠 AI Real Estate Investment Advisor | Powered by FastAPI + Streamlit</p>
</div>
""", unsafe_allow_html=True)