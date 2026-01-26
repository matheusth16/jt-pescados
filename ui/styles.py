import streamlit as st

def aplicar_estilos(perfil="Admin"):
    """
    Aplica todo o design system do JT Pescados.
    Centraliza cores, cards, botões e abas em um único lugar.
    """
    
    # --- 1. PALETA DE CORES INTELIGENTE ---
    if perfil == "Operador":
        cor_principal = "#004080"      # Azul Marinho
        cor_destaque = "#00BFFF"       # Azul Ciano
        bg_card_sutil = "rgba(0, 191, 255, 0.03)" 
    else:
        cor_principal = "#B22222"      # Vermelho JT
        cor_destaque = "#FFD700"       # Dourado
        bg_card_sutil = "rgba(255, 0, 0, 0.03)"   

    # --- 2. INJEÇÃO DE ESTILOS CSS ---
    st.markdown(f"""
    <style>
        /* --- CONFIGURAÇÕES GERAIS --- */
        .main {{ 
            background-color: #0E1117; 
        }}
        
        /* --- SIDEBAR: CARD DO USUÁRIO --- */
        .user-card {{
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            margin-bottom: 20px;
            transition: transform 0.3s ease;
        }}
        .user-card:hover {{
            transform: scale(1.02);
            border-color: {cor_destaque};
        }}
        .user-name {{
            font-size: 18px;
            font-weight: bold;
            color: white;
            margin: 0;
        }}
        .user-role {{
            font-size: 13px;
            color: #8b949e;
            margin-top: 5px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* --- CARDS DE MÉTRICAS DO TOPO (KPIs) --- */
        .metric-container {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-left: 5px solid {cor_principal};
            border-radius: 10px;
            padding: 20px;
            text-align: left;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }}
        .metric-label {{ color: #8b949e; font-size: 14px; font-weight: 500; margin-bottom: 5px; }}
        .metric-value {{ color: white; font-size: 28px; font-weight: bold; }}

        /* --- DASHBOARD: STATUS CARDS LATERAIS --- */
        .status-card {{
            background-color: #1c2128;
            border: 1px solid #30363d;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: background-color 0.2s;
            min-height: 80px;
        }}
        .status-card:hover {{
            background-color: #21262d;
        }}
        .status-card-label {{
            color: #c9d1d9;
            font-size: 14px;
            font-weight: 500;
        }}
        .status-card-value {{
            color: white;
            font-size: 22px;
            font-weight: bold;
        }}
        
        /* --- CORES DINÂMICAS PARA SAÚDE DA OPERAÇÃO --- */
        .saude-baixa {{ border-left: 5px solid #ff4b4b !important; }} /* Vermelho Erro */
        .saude-media {{ border-left: 5px solid #ffeb3b !important; }} /* Amarelo Atenção */
        .saude-alta {{ border-left: 5px solid #28a745 !important; }}  /* Verde Sucesso */

        /* --- ESTILO DAS ABAS (TABS) --- */
        .stTabs [data-baseweb="tab-list"] {{ 
            gap: 10px; 
        }}
        .stTabs [data-baseweb="tab"] {{
            background-color: #161b22;
            border-radius: 8px 8px 0 0;
            padding: 10px 20px;
            color: #8b949e;
            border: 1px solid transparent;
            transition: all 0.2s;
        }}
        .stTabs [data-baseweb="tab"]:hover {{
            color: white;
            background-color: #21262d;
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {cor_principal}20 !important;
            border-bottom: 3px solid {cor_principal} !important;
            color: white !important;
        }}

        /* --- CONTAINERS COM BORDA (st.container) --- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px;
            border: 1px solid #30363d !important;
            background-color: #161b22;
            padding: 15px;
        }}

        /* --- BOTÕES E LINKS --- */
        .stButton>button, .stLinkButton>a {{
            width: 100%;
            border-radius: 8px;
            background-color: {cor_principal};
            color: white !important;
            border: none;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            height: 3em;
            transition: all 0.3s ease;
        }}
        .stButton>button:hover, .stLinkButton>a:hover {{
            filter: brightness(1.2);
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            transform: translateY(-2px);
        }}

        /* --- FORMULÁRIOS --- */
        [data-testid="stForm"] {{
            background-color: {bg_card_sutil};
            border: 1px solid {cor_principal};
            border-radius: 15px;
            padding: 25px;
        }}

        /* --- DATA EDITOR (TABELAS) --- */
        [data-testid="stDataFrame"] {{
            border: 1px solid #30363d;
            border-radius: 10px;
        }}

    </style>
    """, unsafe_allow_html=True)