import streamlit as st

def aplicar_estilos():
    st.markdown("""
    <style>
        /* Estilo dos Botões */
        .stButton>button, .stLinkButton>a {
            width: 100%;
            border-radius: 8px;
            background-color: #B22222;
            color: white !important;
            border: none;
            font-weight: bold;
            display: flex;
            justify-content: center;
            align-items: center;
            text-decoration: none;
        }
        .stButton>button:hover, .stLinkButton>a:hover {
            background-color: #8B0000;
            color: white !important;
            border-color: #8B0000;
        }
        
        /* Estilo das Métricas (Sidebar) */
        [data-testid="stMetric"] {
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            border-left: 5px solid #FFD700;
        }
        
        /* NOVO: Estilo dos Cards (Containers com Borda) */
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background-color: rgba(255, 255, 255, 0.03) !important; /* Fundo sutil */
            padding: 20px !important;
        }
        
        .block-container {
            padding-top: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)