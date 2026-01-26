import streamlit as st
from ui.styles import PALETA_CORES 

def render_login_header():
    """Renderiza o cabeçalho do formulário de login."""
    st.markdown("<h2 style='text-align: center;'>🐟 JT PESCADOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Acesso Restrito</p>", unsafe_allow_html=True)

def render_user_card(nome, perfil):
    """Renderiza o cartão do utilizador na sidebar."""
    st.markdown(f"""
        <div class="user-card">
            <p class="user-name">👤 {nome}</p>
            <p class="user-role">{perfil}</p>
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, color_hex):
    """
    Renderiza os cartões de métricas do topo (Total Clientes, etc.).
    color_hex: Cor da borda esquerda (ex: #58a6ff).
    """
    st.markdown(f"""
        <div class="metric-container" style="border-left-color: {color_hex};">
            <p class="metric-label">{label}</p>
            <p class="metric-value">{value}</p>
        </div>
    """, unsafe_allow_html=True)

def render_status_card(label, value, css_class="", inline_color=None):
    """
    Renderiza os cartões de status da operação (Saúde, Pendentes, Entregues).
    """
    style_attr = ""
    if inline_color:
        style_attr = f'style="border-left: 5px solid {inline_color};"'
    
    st.markdown(f'''
        <div class="status-card {css_class}" {style_attr}>
            <span class="status-card-label">{label}</span>
            <span class="status-card-value">{value}</span>
        </div>
    ''', unsafe_allow_html=True)

def render_preview_card(cliente, data_obj, rota, pagamento, status, cor_borda):
    """
    Renderiza o resumo visual antes de cadastrar um novo pedido.
    """
    data_fmt = data_obj.strftime('%d/%m/%Y')
    st.markdown(f"""
    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 5px solid {cor_borda};">
        <small style="color: #8b949e; font-weight: bold; text-transform: uppercase;">🔍 Resumo do Lançamento</small><br>
        <span style="font-size: 1.1em; font-weight: bold;">{cliente}</span><br>
        <span style="color: #c9d1d9;">📅 Entrega: {data_fmt} ({rota})</span><br>
        <span style="color: #c9d1d9;">💳 {pagamento} &nbsp; | &nbsp; 📊 {status}</span>
    </div>
    """, unsafe_allow_html=True)

def render_error_details(mensagem_amigavel, erro_tecnico=None):
    """
    Exibe um erro formatado.
    """
    st.error(f"⚠️ {mensagem_amigavel}")
    
    if erro_tecnico:
        with st.expander("🔍 Ver Detalhes Técnicos (Suporte)"):
            st.code(str(erro_tecnico), language="python")
            st.caption("Envie um print desta tela para o suporte técnico.")

# --- COMPONENTE DE PREVENÇÃO DE DUPLO CLIQUE ---
def render_loader_action(mensagem="⏳ Processando solicitação..."):
    """
    Exibe um cartão animado de 'Carregando'.
    Este componente deve ser chamado NO LUGAR do botão quando o estado estiver 'processando'.
    """
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 15px; 
        background-color: rgba(255, 255, 255, 0.05); 
        border-radius: 8px; 
        border: 1px dashed rgba(255, 255, 255, 0.3);
        margin-top: 10px;
        animation: pulse 1.5s infinite;
    ">
        <h4 style="margin: 0; color: #fff;">{mensagem}</h4>
        <small style="color: #888;">Por favor, não atualize a página.</small>
    </div>
    <style>
    @keyframes pulse {{
        0% {{ opacity: 0.6; }}
        50% {{ opacity: 1; }}
        100% {{ opacity: 0.6; }}
    }}
    </style>
    """, unsafe_allow_html=True)

def render_history_item(id_ped, data, status, descricao, pagamento):
    """
    Renderiza um único item do histórico com formatação visual de timeline.
    """
    s = str(status).upper().strip()
    
    # Busca a cor na paleta centralizada (com fallback para cinza se não encontrar)
    cor_status = PALETA_CORES["STATUS"].get(s, "#8b949e")
    
    icone = "⚪"
    if s == "ENTREGUE":
        icone = "✅"
    elif s in ["PENDENTE", "GERADO", "ORÇAMENTO"]:
        icone = "⏳"
    elif s in ["CANCELADO", "NÃO GERADO"]:
        icone = "❌"
    elif s == "RESERVADO":
        icone = "🔵"

    st.markdown(f"""
    <div style="
        margin-bottom: 10px; 
        padding: 10px; 
        border-left: 4px solid {cor_status}; 
        background-color: rgba(255,255,255,0.03); 
        border-radius: 4px;
    ">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-weight: bold; font-size: 0.9em; color: {cor_status};">
                {icone} {s}
            </span>
            <span style="font-size: 0.8em; color: #8b949e;">{data} (ID: {id_ped})</span>
        </div>
        <div style="margin-top: 5px; font-size: 0.9em; color: #c9d1d9;">
            {descricao[:60]}{"..." if len(descricao) > 60 else ""}
        </div>
        <div style="margin-top: 4px; font-size: 0.75em; color: #8b949e;">
            💳 {pagamento}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- NOVO: FORMULÁRIO DE DESMEMBRAMENTO ---
def render_split_form(tag_pai, peso_pai):
    """
    Renderiza os campos dentro do Modal de Desmembramento.
    """
    st.markdown(f"**Tag Origem:** `{tag_pai}` &nbsp;|&nbsp; **Peso Total:** `{peso_pai} kg`")
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        letra = st.text_input("Letra / ID da Parte", placeholder="Ex: A, B, P1...")
    with c2:
        peso_unidade = st.number_input("Peso desta Parte (kg)", min_value=0.0, max_value=float(peso_pai) if peso_pai else 100.0, format="%.3f")
    
    nome_cliente = st.text_input("Cliente Destino", placeholder="Para quem vai este pedaço?")
    status_unidade = st.selectbox("Status Inicial", ["GERADO", "RESERVADO", "ORÇAMENTO", "LIVRE"])
    
    return letra, peso_unidade, nome_cliente, status_unidade