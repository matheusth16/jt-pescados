import streamlit as st

# --- 1. PALETA DE CORES CENTRALIZADA (Fonte da Verdade) ---
PALETA_CORES = {
    # Cores usadas nos gráficos e status dos pedidos
    "STATUS": {
        "PENDENTE": "#ffeb00",     # Amarelo
        "GERADO": "#ff8500",       # Laranja
        "NÃO GERADO": "#b10202",   # Vermelho Escuro
        "CANCELADO": "#ffa0a0",    # Vermelho Claro
        "ENTREGUE": "#11734b",     # Verde Escuro (Sucesso)
        "ORÇAMENTO": "#e8eaed",    # Cinza Claro
        "RESERVADO": "#0a53a8",    # Azul Escuro
        
        # --- NOVOS STATUS (RECEBIMENTO SALMÃO) ---
        "LIVRE": "#28a745",        # Verde Claro (Disponível)
        "ABERTO": "#0dcaf0"        # Azul Ciano (Em fracionamento)
    },
    # Cores usadas no tema da interface (CSS)
    "TEMA": {
        "Operador": {
            "principal": "#004080",       # Azul Marinho
            "destaque": "#00BFFF",        # Azul Ciano
            "bg_card_sutil": "rgba(0, 191, 255, 0.03)"
        },
        "Admin": {
            "principal": "#B22222",       # Vermelho JT
            "destaque": "#FFD700",        # Dourado
            "bg_card_sutil": "rgba(255, 0, 0, 0.03)"
        }
    }
}

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
            border-color: {c_dest};
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
            border-left: 5px solid {c_prin};
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
        
        /* --- VISUAL DE GRADE PARA AS TAGS (RECEBIMENTO SALMÃO) --- */
        .tag-box {{
            background-color: #161b22;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            padding: 10px;
            text-align: center;
            margin-bottom: 10px;
            transition: all 0.2s;
            cursor: pointer;
        }}
        .tag-box:hover {{
            border-color: {c_dest};
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }}
        .tag-number {{ font-size: 1.1em; font-weight: bold; color: #fff; }}
        .tag-weight {{ font-size: 0.9em; color: #ccc; }}
        
        /* --- CORES DINÂMICAS PARA SAÚDE DA OPERAÇÃO --- */
        .saude-baixa {{ border-left: 5px solid #ff4b4b !important; }} /* Vermelho Erro */
        .saude-media {{ border-left: 5px solid #ffeb3b !important; }} /* Amarelo Atenção */
        .saude-alta  {{ border-left: 5px solid #28a745 !important; }} /* Verde Sucesso */

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
            background-color: {c_prin}20 !important;
            border-bottom: 3px solid {c_prin} !important;
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
            padding: 25px;
        }}

        /* --- DATA EDITOR (TABELAS) --- */
        [data-testid="stDataFrame"] {{
            border: 1px solid #30363d;
            border-radius: 10px;
        }}

    </style>
    """, unsafe_allow_html=True)
    
    # Retorna o dicionário para ser usado no app.py
    return tema_ativo