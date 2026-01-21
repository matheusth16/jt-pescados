# ui/styles.py
import streamlit as st

def aplicar_estilos():
    st.markdown("""
    <style>
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            background-color: #B22222;
            color: white;
            border: none;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #8B0000;
            color: white;
        }
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #FFD700;
        }
        /* Ajuste para o formulário ficar mais limpo */
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)