import streamlit as st
from core.config import PALETA_CORES

def aplicar_estilos(perfil="Admin"):
    """
    Aplica todo o design system do JT Pescados e injeta o CSS global.
    
    Retorna:
        dict: Um dicionário com as cores ativas (principal, destaque, etc.)
              para serem usadas na lógica do Python (ex: gráficos).
    """
    
    # --- 2. SELEÇÃO DO TEMA ---
    # Busca as cores no dicionário global com fallback para Admin se der erro
    tema_ativo = PALETA_CORES["TEMA"].get(perfil, PALETA_CORES["TEMA"]["Admin"])

    # Variáveis locais para facilitar a injeção no f-string abaixo
    c_prin = tema_ativo["principal"]
    c_dest = tema_ativo["destaque"]
    c_bg   = tema_ativo["bg_card_sutil"]

    # --- 3. INJEÇÃO DE ESTILOS CSS ---
    st.markdown(f"""
    <style>
        /* --- CONFIGURAÇÕES GERAIS (Aumento Global + Forçar Dark Mode) --- */
        
        /* Adicionei !important nas cores para o Light Mode não deixar tudo branco */
        .main, .stApp, [data-testid="stSidebar"] {{ 
            background-color: #0E1117 !important; 
            color: #FAFAFA !important;
            font-size: 18px !important;
        }}

        /* Títulos */
        h1, h2, h3 {{
            font-size: 2.2rem !important;
            color: #FAFAFA !important;
        }}

        /* Textos gerais e labels */
        .stMarkdown p, div[data-testid="stText"], label, .stTextInput > label, .stNumberInput > label, .stSelectbox > label {{
            font-size: 1.1rem !important;
            color: #FAFAFA !important;
        }}
        
        /* --- SIDEBAR: CARD DO USUÁRIO --- */
        .user-card {{
            background-color: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .user-name {{
            color: #e6e6e6 !important;
            font-weight: bold;
            font-size: 1.1em;
            margin: 0;
        }}
        .user-role {{
            color: {c_prin} !important;
            font-size: 0.9em;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* --- METRIC CARDS (TOPO) --- */
        .metric-container {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-left: 5px solid {c_prin};
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }}
        .metric-label {{
            color: #8b949e !important;
            font-size: 0.85em;
            margin: 0;
        }}
        .metric-value {{
            color: #f0f6fc !important;
            font-size: 1.5em;
            font-weight: bold;
            margin: 0;
        }}

        /* --- PREVIEW CARD (NOVO PEDIDO) --- */
        .preview-card {{
            background-color: {c_bg};
            border: 1px solid {c_prin};
            border-radius: 10px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }}

        /* --- STATUS CARDS (Dashboard/Operações) --- */
        .status-card {{
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 15px;
            height: 100%;
        }}
        .status-card-label {{
            color: #8b949e !important;
            font-size: 0.85em;
            margin-bottom: 5px;
            display: block;
        }}
        .status-card-value {{
            color: #f0f6fc !important;
            font-size: 1.5em;
            font-weight: bold;
            display: block;
        }}
        
        /* --- VARIAÇÕES DE SAÚDE (Borda Lateral) --- */
        .saude-baixa {{
            border-left: 5px solid #d9534f; 
        }}
        .saude-media {{
            border-left: 5px solid #ffa500; 
        }}
        .saude-alta {{
            border-left: 5px solid #28a745; 
        }}
        
        /* --- STATUS BADGES --- */
        .status-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.85em;
            display: inline-block;
        }}
        
        /* --- CUSTOM TOAST --- */
        div[data-testid="stToast"] {{
            background-color: {c_dest} !important;
            color: white !important;
        }}

        /* --- CONTAINERS COM BORDA (st.container) --- */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 12px;
            border: 1px solid #30363d !important;
            background-color: #161b22 !important;
            padding: 15px;
        }}

        /* --- BOTÕES E LINKS --- */
        .stButton>button, .stLinkButton>a {{
            width: 100%;
            border-radius: 8px;
            background-color: {c_prin};
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
            background-color: {c_bg};
            border: 1px solid {c_prin};
            border-radius: 15px;
            padding: 20px;
        }}
        
        /* --- AJUSTES TABELAS --- */
        [data-testid="stDataFrame"] {{
            border: 1px solid #30363d;
            border-radius: 8px;
        }}
    </style>
    """, unsafe_allow_html=True)

    return tema_ativo