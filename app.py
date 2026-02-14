import streamlit as st
import pandas as pd
import time

import services.database as db
import ui.components as components
import ui.styles as styles

# --- IMPORTS DAS PÁGINAS (Módulos isolados) ---
import ui.pages.dashboard as page_dashboard
import ui.pages.pedidos as page_pedidos
import ui.pages.gerenciar as page_gerenciar
import ui.pages.gerenciar_edicao as page_gerenciar_edicao  # ✅ NOVO
import ui.pages.salmao as page_salmao
import ui.pages.clientes as page_clientes

# --- CONFIGURAÇÕES GLOBAIS ---
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. GESTÃO DE SESSÃO ---
def inicializar_sessao():
    """Garante que as variáveis de estado existam, sobrevivendo a recarregamentos."""
    if "navegacao_principal" not in st.session_state:
        st.session_state.navegacao_principal = None

    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario_nome" not in st.session_state:
        st.session_state.usuario_nome = ""
    if "usuario_perfil" not in st.session_state:
        st.session_state.usuario_perfil = ""
    if "form_id" not in st.session_state:
        st.session_state.form_id = 0
    if "processando_envio" not in st.session_state:
        st.session_state.processando_envio = False

    # Variável de Filtro do Dashboard
    if "filtro_status_dash" not in st.session_state:
        st.session_state.filtro_status_dash = None

    # Variáveis do Módulo Salmão
    if "salmao_df" not in st.session_state:
        st.session_state.salmao_df = pd.DataFrame()
    if "salmao_range_str" not in st.session_state:
        st.session_state.salmao_range_str = ""

    # ✅ rota interna (para navegação programática sem expor no menu)
    if "nav_page" not in st.session_state:
        st.session_state.nav_page = None


# Inicializa as variáveis assim que o script roda
inicializar_sessao()


# --- 2. TELA DE LOGIN ---
def tela_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login_form"):
            components.render_login_header()

            user = st.text_input("Usuário", placeholder="Login...")
            pw = st.text_input("Senha", type="password", placeholder="Senha...")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                try:
                    dados = db.autenticar_usuario(user, pw)
                    if dados:
                        st.session_state.logado = True
                        st.session_state.usuario_nome = dados["nome"]
                        st.session_state.usuario_perfil = dados["perfil"]
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                except ConnectionError as e:
                    components.render_error_details("Sem conexão com a internet.", e)
                except Exception as e:
                    components.render_error_details("Erro técnico no login.", e)


# --- 3. SISTEMA PRINCIPAL (ROTEADOR) ---
if not st.session_state.logado:
    tela_login()
else:
    # 3.1. Dados Globais
    try:
        hash_dados = db.obter_versao_planilha()
    except Exception:
        hash_dados = time.time()

    NOME_USER = st.session_state.usuario_nome
    PERFIL = st.session_state.usuario_perfil

    # Injeta o CSS global baseado no perfil
    styles.aplicar_estilos(perfil=PERFIL)

    # ✅ 3.2. MENU NA SIDEBAR (hambúrguer no mobile)
    with st.sidebar:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        components.render_user_card(NOME_USER, PERFIL)
        st.markdown("---")

        # Opções por perfil
        if PERFIL == "Admin":
            opcoes_menu = ["📈 Dashboard", "📝 Novo Pedido", "👁️ Gerenciar", "🐟 Recebimento de Salmão", "➕ Clientes"]
        else:
            opcoes_menu = ["🚚 Operações", "🐟 Recebimento de Salmão", "📈 Indicadores"]

        # valor inicial
        if st.session_state.navegacao_principal is None:
            st.session_state.navegacao_principal = opcoes_menu[0]

        escolha_nav_sidebar = st.radio(
            "Menu",
            opcoes_menu,
            index=opcoes_menu.index(st.session_state.navegacao_principal),
            key="nav_radio_sidebar"
        )

        # ✅ auto-fechar / navegar melhor no mobile:
        # se mudou, salva e dá rerun (tende a recolher sidebar em mobile)
        if escolha_nav_sidebar != st.session_state.navegacao_principal:
            st.session_state.navegacao_principal = escolha_nav_sidebar
            st.rerun()

        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.session_state.filtro_status_dash = None
            st.session_state.nav_page = None
            st.session_state.navegacao_principal = None
            st.rerun()

    # 3.3. HEADER COMPACTO + MÉTRICAS (Topo)
    # Troca o st.title (muito alto no mobile) por um header menor e limpo.
    st.markdown("### 📦 Portal de Pedidos")

    try:
        qtd_cli, qtd_ped = db.get_metricas(_hash_versao=hash_dados)
    except Exception:
        qtd_cli, qtd_ped = "-", "-"

    m1, m2, m3 = st.columns(3)
    with m1:
        components.render_metric_card("👥 Total Clientes", qtd_cli, "#58a6ff")
    with m2:
        components.render_metric_card("📦 Pedidos Totais", qtd_ped, "#f1e05a")
    with m3:
        components.render_metric_card("👤 Usuário Logado", NOME_USER, "#238636")

    # ✅ 3.4. ROTEAMENTO INTERNO (sem aparecer no menu)
    if st.session_state.nav_page == "gerenciar_edicao":

        # Segurança: Admin nunca entra
        if PERFIL == "Admin":
            st.warning("⛔ Acesso negado. Tela de edição é exclusiva para OP.")
            st.session_state.nav_page = None
            st.session_state.navegacao_principal = "👁️ Gerenciar"
            st.rerun()

        # ✅ GARANTIA: se não houver pedido selecionado, volta pra tabela
        pedido_sel = st.session_state.get("pedido_para_visualizar", None)
        pedido_id = st.session_state.get("pedido_id_edicao", None)

        if pedido_sel is None and (pedido_id is None or str(pedido_id).strip() == ""):
            st.session_state.nav_page = None
            st.session_state.navegacao_principal = "🚚 Operações"
            st.rerun()

        page_gerenciar_edicao.render_page(hash_dados, PERFIL, NOME_USER)
        st.stop()

    # ✅ ESSENCIAL: escolha_nav sempre definido (vem do menu da sidebar)
    escolha_nav = st.session_state.navegacao_principal

    st.markdown("---")

    # 3.5. ROTEAMENTO: Chama a página certa baseada na escolha
    if escolha_nav in ["📈 Dashboard", "📈 Indicadores"]:
        page_dashboard.render_page(hash_dados, PERFIL)

    elif escolha_nav == "📝 Novo Pedido":
        page_pedidos.render_page(hash_dados, PERFIL, NOME_USER)

    elif escolha_nav in ["👁️ Gerenciar", "🚚 Operações"]:
        page_gerenciar.render_page(hash_dados, PERFIL, NOME_USER)

    elif escolha_nav == "➕ Clientes":
        page_clientes.render_page(hash_dados, PERFIL)

    elif escolha_nav == "🐟 Recebimento de Salmão":
        page_salmao.render_page(hash_dados, PERFIL, NOME_USER)
