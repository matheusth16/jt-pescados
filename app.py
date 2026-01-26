import streamlit as st
import time
import plotly.express as px
from datetime import datetime
import pandas as pd
import services.database as db
import ui.styles as styles

# --- CONFIGURAÇÕES GLOBAIS ---
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Constantes de Negócio
LISTA_STATUS = ["GERADO", "PENDENTE", "NÃO GERADO", "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"]
LISTA_PAGAMENTO = ["A COMBINAR", "PIX", "BOLETO", "CARTÃO"]

# Mapa de Cores
# Mapa de Cores Atualizado conforme sua solicitação
CORES_STATUS = {
    "PENDENTE": "#ffeb00",
    "GERADO": "#ff8500",
    "NÃO GERADO": "#b10202",
    "CANCELADO": "#ffa0a0",
    "ENTREGUE": "#11734b",
    "ORÇAMENTO": "#e8eaed",
    "RESERVADO": "#0a53a8"
}

# --- FUNÇÕES DE CACHE (A SOLUÇÃO DO ERRO 429) ---
# Estas funções guardam os dados na memória para não chamar o Google toda hora

@st.cache_data(ttl=300) # Guarda na memória por 5 minutos
def carregar_clientes_cache():
    """Busca a base de clientes e guarda em cache."""
    conn = db.get_connection()
    try:
        # Tenta ler como lista de registros
        ws = conn.worksheet("BaseClientes")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        
        # Limpeza preventiva dos nomes das colunas
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        print(f"Erro ao ler clientes: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60) # Guarda na memória por 60 segundos
def carregar_pedidos_cache():
    """Busca os pedidos para o Dashboard e Histórico."""
    # Usa a função do database, mas envelopada no cache do Streamlit
    return db.buscar_pedidos_visualizacao()

# --- 1. GESTÃO DE SESSÃO ---
if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_nome = ""
    st.session_state.usuario_perfil = ""
if "form_id" not in st.session_state:
    st.session_state.form_id = 0

# Aplica estilo visual
perfil_atual = st.session_state.usuario_perfil if st.session_state.logado else "Admin"
styles.aplicar_estilos(perfil=perfil_atual)

# --- 2. TELA DE LOGIN ---
def tela_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align: center;'>🐟 JT PESCADOS</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #888;'>Acesso Restrito</p>", unsafe_allow_html=True)
            
            user = st.text_input("Usuário", placeholder="Login...")
            pw = st.text_input("Senha", type="password", placeholder="Senha...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("ACESSAR SISTEMA", use_container_width=True):
                dados = db.autenticar_usuario(user, pw)
                if dados:
                    st.session_state.logado = True
                    st.session_state.usuario_nome = dados['nome']
                    st.session_state.usuario_perfil = dados['perfil']
                    st.rerun()
                else:
                    st.error("Dados inválidos.")

# --- 3. SISTEMA PRINCIPAL ---
if not st.session_state.logado:
    tela_login()
else:
    NOME_USER = st.session_state.usuario_nome
    PERFIL = st.session_state.usuario_perfil
    cor_principal = "#B22222" if PERFIL == "Admin" else "#004080"

    # --- SIDEBAR ---
    with st.sidebar:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="user-card">
                <p class="user-name">👤 {NOME_USER}</p>
                <p class="user-role">{PERFIL}</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if PERFIL == "Admin":
            st.markdown("#### 🛠️ Ferramentas")
            st.link_button("📂 Planilha Master", "https://docs.google.com/spreadsheets/d/1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc/edit?usp=sharing", use_container_width=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

    # --- CABEÇALHO ---
    st.title("📦 Portal de Pedidos Digital")
    
    # As métricas podem ser chamadas direto pois são leves, mas idealmente cachearíamos também
    # Por enquanto, mantemos direto para garantir atualização em tempo real
    qtd_cli, qtd_ped = db.get_metricas()
    m1, m2, m3 = st.columns(3)
    
    with m1:
        st.markdown(f'<div class="metric-container" style="border-left-color: #58a6ff;">'
                    f'<p class="metric-label">👥 Total Clientes</p>'
                    f'<p class="metric-value">{qtd_cli}</p></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-container" style="border-left-color: #f1e05a;">'
                    f'<p class="metric-label">📦 Pedidos Totais</p>'
                    f'<p class="metric-value">{qtd_ped}</p></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-container" style="border-left-color: #238636;">'
                    f'<p class="metric-label">👤 Usuário Logado</p>'
                    f'<p class="metric-value">{NOME_USER}</p></div>', unsafe_allow_html=True)

    # --- DEFINIÇÃO DE NAVEGAÇÃO PERSISTENTE ---
    aba_dash = aba_novo = aba_gestao = aba_clientes = None

    # Define as opções baseado no perfil
    if PERFIL == "Admin":
        opcoes = ["📈 Dashboard", "📝 Novo Pedido", "👁️ Gerenciar", "➕ Clientes"]
        default_idx = 0
    else:
        opcoes = ["🚚 Logística", "📈 Indicadores"]
        default_idx = 0

    # Cria o menu de navegação que LEMBRA a escolha (devido ao parâmetro key)
    escolha_nav = st.segmented_control(
        "Menu Principal",
        opcoes,
        selection_mode="single",
        default=opcoes[default_idx],
        key="navegacao_principal"  # <--- O SEGREDO ESTÁ AQUI (A KEY SEGURA A ABA)
    )
    
    st.markdown("---") # Uma linha para separar o menu do conteúdo

    if escolha_nav in ["📈 Dashboard", "📈 Indicadores"]:
        aba_dash = st.container()
    elif escolha_nav == "📝 Novo Pedido":
        aba_novo = st.container()
    elif escolha_nav in ["👁️ Gerenciar", "🚚 Logística"]:
        aba_gestao = st.container()
    elif escolha_nav == "➕ Clientes":
        aba_clientes = st.container()

    # =========================================================================
    # ABA: DASHBOARD
    # =========================================================================
    # Adicione o IF antes do WITH
    if aba_dash:
        with aba_dash:
            # todo o seu código do dashboard continua aqui identado...
            c_titulo, c_filtro = st.columns([1, 1.2], vertical_alignment="center")
            
            with c_titulo:
                st.markdown("### 📊 Indicadores de Performance")
            
            with c_filtro:
                filtro_tempo = st.segmented_control(
                    "Período:", 
                    options=["Hoje", "Últimos 7 Dias", "Mês Atual", "Tudo"], 
                    default="Tudo",
                    selection_mode="single",
                    label_visibility="collapsed"
                )
                
            if not filtro_tempo:
                filtro_tempo = "Tudo"
                
            st.markdown("---")

            # USANDO CACHE AQUI PARA EVITAR ERRO 429
            df_bruto = carregar_pedidos_cache()
            
            if not df_bruto.empty:
                df_bruto.columns = [c.upper().strip() for c in df_bruto.columns]
                col_dt = next((c for c in df_bruto.columns if "ENTREGA" in c), None)

                # LÓGICA DE FILTRAGEM
                df_dash = df_bruto.copy()
                if col_dt:
                    df_dash[col_dt] = pd.to_datetime(df_dash[col_dt], dayfirst=True, errors='coerce')
                    hoje = pd.Timestamp.now().normalize()
                    
                    if filtro_tempo == "Hoje":
                        df_dash = df_dash[df_dash[col_dt] == hoje]
                    elif filtro_tempo == "Últimos 7 Dias":
                        df_dash = df_dash[df_dash[col_dt] >= (hoje - pd.Timedelta(days=7))]
                    elif filtro_tempo == "Mês Atual":
                        df_dash = df_dash[(df_dash[col_dt].dt.month == hoje.month) & (df_dash[col_dt].dt.year == hoje.year)]

                total_pedidos = len(df_dash)
                
                # --- LINHA 1: GRÁFICOS ---
                c_pizza, c_barra = st.columns(2)
                
                with c_pizza:
                    with st.container(border=True):
                        st.markdown("#### Status dos Pedidos")
                        if "STATUS" in df_dash.columns:
                            contagem_status = df_dash["STATUS"].value_counts().reset_index()
                            contagem_status.columns = ["STATUS", "TOTAL"]
                            
                            fig_status = px.pie(contagem_status, values="TOTAL", names="STATUS", 
                                            hole=0.6, color="STATUS", 
                                            color_discrete_map=CORES_STATUS)
                            
                            fig_status.add_annotation(text=f"<b>{total_pedidos}</b><br>PEDIDOS", 
                                                    showarrow=False, font=dict(size=20, color="white"))
                            
                            fig_status.update_layout(margin=dict(t=30, b=0, l=10, r=10), showlegend=False,
                                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_status, use_container_width=True)

                with c_barra:
                    with st.container(border=True):
                        st.markdown("#### Preferência de Pagamento")
                        if "PAGAMENTO" in df_dash.columns:
                            contagem_pg = df_dash["PAGAMENTO"].value_counts().reset_index()
                            contagem_pg.columns = ["PAGAMENTO", "QTD"]
                            
                            contagem_pg = contagem_pg.sort_values("QTD", ascending=True)
                            
                            fig_pg = px.bar(contagem_pg, x="QTD", y="PAGAMENTO", orientation='h',
                                        text="QTD", color_discrete_sequence=[cor_principal])
                            
                            fig_pg.update_layout(
                                xaxis_title="", yaxis_title="",
                                margin=dict(t=30, b=10, l=10, r=10),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color="white"),
                                xaxis=dict(showgrid=False, showticklabels=False)
                            )
                            fig_pg.update_traces(marker_line_color='rgba(0,0,0,0)', textposition='outside')
                            st.plotly_chart(fig_pg, use_container_width=True)

                # --- LINHA 2: RESUMO DA OPERAÇÃO ---
                st.markdown("#### Resumo da Operação")
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    entregues = len(df_dash[df_dash["STATUS"] == "ENTREGUE"]) if "STATUS" in df_dash.columns else 0
                    pct_saude = (entregues / total_pedidos * 100) if total_pedidos > 0 else 0
                    
                    classe_cor = "saude-baixa" if pct_saude < 50 else "saude-media" if pct_saude < 80 else "saude-alta"
                    
                    st.markdown(f'''
                        <div class="status-card {classe_cor}">
                            <span class="status-card-label">🩺 Saúde da Operação</span>
                            <span class="status-card-value">{pct_saude:.1f}%</span>
                        </div>
                    ''', unsafe_allow_html=True)

                with c2:
                    pendentes = len(df_dash[df_dash["STATUS"].isin(["PENDENTE", "GERADO"])]) if "STATUS" in df_dash.columns else 0
                    st.markdown(f'''
                        <div class="status-card" style="border-left: 5px solid #FFA500;">
                            <span class="status-card-label">⏳ Aguardando Processo</span>
                            <span class="status-card-value">{pendentes}</span>
                        </div>
                    ''', unsafe_allow_html=True)

                with c3:
                    st.markdown(f'''
                        <div class="status-card" style="border-left: 5px solid #28A745;">
                            <span class="status-card-label">✅ Pedidos Entregues</span>
                            <span class="status-card-value">{entregues}</span>
                        </div>
                    ''', unsafe_allow_html=True)
                
                # --- LINHA 3: EVOLUÇÃO TEMPORAL ---
                st.markdown("#### 📈 Evolução de Pedidos por Dia")
                with st.container(border=True):
                    if col_dt and not df_dash.empty:
                        evolucao_diaria = df_dash.groupby(df_dash[col_dt].dt.date).size().reset_index(name='QTD')
                        evolucao_diaria.columns = ['DATA', 'QTD']
                        evolucao_diaria = evolucao_diaria.sort_values('DATA')

                        fig_evol = px.line(evolucao_diaria, x='DATA', y="QTD", markers=True, 
                                        line_shape="spline", color_discrete_sequence=[cor_principal])
                        
                        fig_evol.update_layout(
                            xaxis_title="", yaxis_title="Pedidos",
                            margin=dict(t=30, b=10, l=10, r=10),
                            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="white"),
                            xaxis=dict(showgrid=False),
                            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
                        )
                        st.plotly_chart(fig_evol, use_container_width=True)
                        
                # --- LINHA 4: TOP 5 CLIENTES ---
                st.markdown("#### 🏆 Top 5 Clientes do Período")
                with st.container(border=True):
                    if "NOME CLIENTE" in df_dash.columns:
                        top_clientes = df_dash["NOME CLIENTE"].value_counts().reset_index().head(5)
                        top_clientes.columns = ["CLIENTE", "QTD"]
                        max_pedidos = top_clientes["QTD"].max() if not top_clientes.empty else 1

                        st.data_editor(
                            top_clientes,
                            column_config={
                                "CLIENTE": st.column_config.TextColumn("👤 Nome do Cliente"),
                                "QTD": st.column_config.ProgressColumn(
                                    "📦 Volume de Pedidos",
                                    format="%d",
                                    min_value=0,
                                    max_value=int(max_pedidos),
                                ),
                            },
                            hide_index=True, use_container_width=True, disabled=True
                        )
            else:
                st.info("Sem dados para exibir para o período selecionado.")

    # =========================================================================
    # ABA: NOVO PEDIDO (VERSÃO CORRIGIDA - HISTÓRICO INDEPENDENTE)
    # =========================================================================
    if PERFIL == "Admin" and aba_novo:
        with aba_novo:
            st.markdown("### 📝 Novo Pedido")
            
            # --- 1. CARREGAMENTO DOS DADOS COM CACHE ---
            df_clientes_completo = carregar_clientes_cache()
            lista_nomes = ["Consumidor Final"]

            if not df_clientes_completo.empty:
                # Busca pela coluna "Cliente" (nome exato da sua planilha)
                if "Cliente" in df_clientes_completo.columns:
                    nomes_validos = df_clientes_completo["Cliente"].dropna().unique()
                    lista_nomes = sorted([n for n in nomes_validos if str(n).strip() != ""])

            # --- 2. FORMULÁRIO PRINCIPAL ---
            with st.container(border=True):
                
            # --- PASSO 1: IDENTIFICAÇÃO E ENTREGA ---
                st.markdown("#### 1️⃣ Identificação e Entrega")
                c1, c2 = st.columns([2, 1])
                
                with c1: 
                    # --- 1. SELETOR DE CLIENTES (RECOLOCADO AQUI) ---
                    idx_padrao = 0
                    if "VENDA A CONSUMIDOR" in lista_nomes:
                        idx_padrao = lista_nomes.index("VENDA A CONSUMIDOR")
                        
                    cli = st.selectbox("Cliente:", lista_nomes, index=idx_padrao, key=f"c_{st.session_state.form_id}")
                    
                    # --- 2. BUSCA DE DADOS (CIDADE/ROTA) ---
                    cidade_cli = "Não informado"
                    rota_cli = "-"
                    
                    if not df_clientes_completo.empty and "Cliente" in df_clientes_completo.columns:
                        try:
                            row_cli = df_clientes_completo[df_clientes_completo["Cliente"].astype(str) == str(cli)]
                            if not row_cli.empty:
                                cidade_cli = row_cli.iloc[0].get("Nome Cidade", "SÃO CARLOS")
                                rota_cli = row_cli.iloc[0].get("ROTA", "-")
                        except:
                            pass 

                    # --- 3. CORES DINÂMICAS DA ROTA ---
                    rota_upper = str(rota_cli).strip().upper()
                    
                    if "RETIRADA" in rota_upper:
                        # Azul para Retirada
                        st.info(f"📍 **Cidade:** {cidade_cli}  |  🏢 **Rota:** {rota_cli} (Cliente vem buscar)")
                    elif rota_cli in ["-", "Não definido", "", "None"]:
                        # Amarelo para Rota Desconhecida
                        st.warning(f"📍 **Cidade:** {cidade_cli}  |  ⚠️ **Rota:** Pendente de Logística")
                    else:
                        # Verde para Entregas Externas
                        st.success(f"📍 **Cidade:** {cidade_cli}  |  🚚 **Rota:** {rota_cli} (Entrega Externa)")

                    # --- 4. HISTÓRICO EM POPOVER ---
                    with st.popover("📜 Ver Histórico de Pedidos", use_container_width=True):
                        try:
                            df_hist = carregar_pedidos_cache()
                            if not df_hist.empty:
                                nome_selecionado = str(cli).strip().upper()
                                df_hist.columns = [str(c).strip().upper() for c in df_hist.columns]
                                
                                if "NOME CLIENTE" in df_hist.columns:
                                    df_hist["NOME_LIMPO"] = df_hist["NOME CLIENTE"].astype(str).str.strip().str.upper()
                                    hist_cli = df_hist[df_hist["NOME_LIMPO"] == nome_selecionado].copy()
                                    
                                    if not hist_cli.empty:
                                        if "ID_PEDIDO" in hist_cli.columns:
                                            hist_cli["ID_PEDIDO"] = pd.to_numeric(hist_cli["ID_PEDIDO"], errors='coerce')
                                            hist_cli = hist_cli.sort_values("ID_PEDIDO", ascending=False).head(3)
                                        
                                        cols_to_show = [c for c in ["DATA REGISTRO", "DIA DA ENTREGA", "STATUS", "PEDIDO", "DESCRIÇÃO"] if c in hist_cli.columns]
                                        st.dataframe(hist_cli[cols_to_show], hide_index=True, use_container_width=True)
                                    else:
                                        st.info("Nenhum pedido recente encontrado para este cliente.")
                            else:
                                st.info("Base de pedidos vazia.")
                        except Exception as e:
                            st.error(f"Erro ao carregar histórico: {e}")

                with c2: 
                    # 1. Campo de Data (Padrão BR)
                    dt = st.date_input("Data de Entrega:", datetime.today(), format="DD/MM/YYYY", key=f"d_{st.session_state.form_id}")
                    
                    if dt < datetime.today().date():
                        st.warning("⚠️ Atenção: Data retroativa!")

                    # 2. CONTADOR DE VOLUME (Ocupa o espaço vazio com inteligência)
                    st.write("")
                    st.write("")

                    # 3. Bloco da Métrica com o novo nome
                    try:
                        df_vol = carregar_pedidos_cache()
                        if not df_vol.empty:
                            data_sel = dt.strftime("%d/%m/%Y")
                            # Busca na coluna DIA DA ENTREGA da planilha
                            pedidos_no_dia = len(df_vol[df_vol["DIA DA ENTREGA"] == data_sel])
                            
                            st.metric("📅 Agendamentos do Dia", f"{pedidos_no_dia} Pedidos")
                    except:
                        pass

                st.divider()

                # --- PASSO 2: COMERCIAL ---
                st.markdown("#### 2️⃣ Detalhes Comerciais")
                c3, c4 = st.columns(2)
                with c3: 
                    pg = st.selectbox("Forma de Pagamento:", LISTA_PAGAMENTO, key=f"p_{st.session_state.form_id}")
                
                with c4: 
                    # index=2 garante que venha "NÃO GERADO" por padrão
                    stt = st.selectbox("Status Inicial:", LISTA_STATUS, index=2, key=f"s_{st.session_state.form_id}")
                
                # (O aviso st.warning foi removido daqui)
                
                usar_nr = st.checkbox("Informar NR do Pedido externo?", key=f"chk_{st.session_state.form_id}")
                nr_ped = ""
                if usar_nr:
                    nr_ped = st.text_input("Digite o NR do Pedido:", placeholder="Ex: 12345", key=f"nr_{st.session_state.form_id}")

                st.divider()

# --- PASSO 3: ITENS DO PEDIDO ---
                st.markdown("#### 3️⃣ Itens do Pedido")
                
                # Contador visual simples para ajudar o operador
                desc = st.text_area("Descrição (Quantidade e Produtos):", height=150, placeholder="Ex: 10kg de Tilápia...", key=f"de_{st.session_state.form_id}")
                
                # Variável de controle: Só é válido se tiver texto
                form_invalido = len(desc.strip()) == 0

                # --- CARD DE PRÉ-VISUALIZAÇÃO ---
                if desc:
                    st.markdown("---")
                    st.markdown(f"""
                    <div style="background-color: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 8px; border-left: 5px solid {cor_principal};">
                        <small style="color: #8b949e; font-weight: bold; text-transform: uppercase;">🔍 Resumo do Lançamento</small><br>
                        <span style="font-size: 1.1em; font-weight: bold;">{cli}</span><br>
                        <span style="color: #c9d1d9;">📅 Entrega: {dt.strftime('%d/%m/%Y')} ({rota_cli})</span><br>
                        <span style="color: #c9d1d9;">💳 {pg} &nbsp; | &nbsp; 📊 {stt}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                else:
                    # Aviso sutil para preencher
                    st.caption("📝 *Preencha a descrição dos itens para liberar o botão de cadastro.*")

                # --- BOTÕES DE AÇÃO COM TRAVA DE SEGURANÇA ---
                c_btn1, c_btn2 = st.columns([3, 1])
                
                with c_btn1:
                    # O botão fica DESABILITADO (cinza) se form_invalido for True
                    if st.button("🚀 CADASTRAR PEDIDO", type="primary", use_container_width=True, disabled=form_invalido):
                        with st.spinner("Gravando pedido..."):
                            db.salvar_pedido(cli, desc, dt, pg, stt, nr_pedido=nr_ped, usuario_logado=NOME_USER)
                            carregar_pedidos_cache.clear()
                            
                            st.toast(f"✅ Pedido para **{cli}** salvo com sucesso!", icon="🎉")
                            time.sleep(1.5)
                            st.session_state.form_id += 1
                            st.rerun()
                
                with c_btn2:
                    if st.button("🗑️ Limpar", use_container_width=True):
                        st.session_state.form_id += 1
                        st.rerun()

    # =========================================================================
    # ABA: GESTÃO (MISTA)
    # =========================================================================
    if aba_gestao:
        with aba_gestao:
            st.subheader("📋 Painel de Controle")
            
            df_gestao = carregar_pedidos_cache()
            
            if not df_gestao.empty:
                df_gestao.columns = [c.upper().strip() for c in df_gestao.columns]

                # --- 2. FILTROS RÁPIDOS NO TOPO ---
                with st.expander("🔍 Filtros de Busca", expanded=False):
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: 
                        f_status = st.multiselect("Filtrar por Status:", LISTA_STATUS, default=[])
                    with c_f2:
                        # Busca a coluna de entrega para filtrar por data
                        col_dt_nome = next((c for c in df_gestao.columns if "ENTREGA" in c), None)
                        f_data = st.date_input("Filtrar por Data:", value=[]) if col_dt_nome else None

                # Aplicação dos filtros no DataFrame
                df_display = df_gestao.copy()
                if f_status:
                    df_display = df_display[df_display["STATUS"].isin(f_status)]
                
                # --- 1. SISTEMA DE CORES NA COLUNA STATUS ---
                cfg_visual = {
                    "ID_PEDIDO": st.column_config.NumberColumn("🆔 ID", format="%d", width="small"),
                    "NOME CLIENTE": st.column_config.TextColumn("👤 Cliente", width="medium"),
                    # Aqui aplicamos as suas cores usando o ProgressColumn ou SelectboxColumn estilizado
                    "STATUS": st.column_config.SelectboxColumn(
                        "📊 Status", 
                        options=LISTA_STATUS, 
                        required=True, 
                        width="medium"
                    ),
                    "PAGAMENTO": st.column_config.SelectboxColumn("💳 Pagamento", options=LISTA_PAGAMENTO, width="medium"),
                    "DIA DA ENTREGA": st.column_config.TextColumn("📅 Entrega")
                }

                # Aplicando o estilo de cor de fundo apenas na coluna STATUS
                # O Streamlit permite destacar células usando o dataframe.style
                df_estilizado = df_display.style.map(
                    lambda x: f'background-color: {CORES_STATUS.get(x, "")}; color: {"white" if x in ["NÃO GERADO", "RESERVADO", "ENTREGUE"] else "black"}', 
                    subset=['STATUS']
                )

                # Exibição da Tabela
                if PERFIL == "Admin":
                    st.dataframe(df_estilizado, use_container_width=True, height=600, hide_index=True)
                else:
                    # No editor para o Operador, as cores ajudam a identificar o que precisa mudar
                    df_editado = st.data_editor(
                        df_display, # O editor não suporta .style diretamente, então usamos o column_config
                        column_config=cfg_visual,
                        use_container_width=True,
                        height=600,
                        hide_index=True,
                        key="tabela_operador"
                    )

                    if st.button("💾 CONFIRMAR ALTERAÇÕES", type="primary", use_container_width=True):
                        db.atualizar_pedidos_editaveis(df_editado, usuario_logado=NOME_USER)
                        carregar_pedidos_cache.clear()
                        st.success("✅ Atualizado!")
                        st.rerun()

    # =========================================================================
    # ABA: CLIENTES (EXCLUSIVO ADMIN + CPF/CNPJ)
    # =========================================================================
    if PERFIL == "Admin" and aba_clientes:
        with aba_clientes:
            st.subheader("➕ Gestão de Clientes")
            
            # --- 1. FORMULÁRIO DE CADASTRO COM MÁSCARA ---
            with st.container(border=True):
                with st.form("cad_cli", clear_on_submit=True):
                    nn = st.text_input("Nome do Cliente / Empresa", placeholder="Razão Social ou Nome Fantasia")
                    
                    c1, c2 = st.columns(2)
                    with c1: 
                        cc = st.text_input("Cidade", value="SÃO CARLOS")
                    with c2: 
                        doc_raw = st.text_input("CPF/CNPJ", placeholder="Digite apenas os números")
                    
                    # Limpeza imediata: remove tudo que não for número
                    doc_limpo = "".join(filter(str.isdigit, doc_raw))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("SALVAR NOVO CLIENTE", use_container_width=True):
                        if not nn:
                            st.warning("O Nome do Cliente é obrigatório.")
                        elif doc_limpo and len(doc_limpo) not in [11, 14]:
                            st.error(f"⚠️ Documento Inválido! Detectamos {len(doc_limpo)} dígitos. Use 11 (CPF) ou 14 (CNPJ).")
                        else:
                            db.criar_novo_cliente(nn, cc, doc_limpo)
                            carregar_clientes_cache.clear()
                            st.success(f"✅ {nn} cadastrado com sucesso!")
                            time.sleep(1)
                            st.rerun()

            st.markdown("---")

            # --- 3. TABELA DE CONSULTA (LISTA COMPLETA) ---
            st.markdown("### 🔍 Clientes já Cadastrados")
            
            df_clientes_view = carregar_clientes_cache()
            
            if not df_clientes_view.empty:
                # Garante que as colunas apareçam com nomes amigáveis
                st.write(f"Atualmente você possui **{len(df_clientes_view)}** clientes na base.")
                
                st.dataframe(
                    df_clientes_view,
                    column_config={
                        "ID": st.column_config.NumberColumn("ID", format="%d"),
                        "Cliente": st.column_config.TextColumn("👤 Cliente"),
                        "Nome Cidade": st.column_config.TextColumn("📍 Cidade"),
                        "CPF/CNPJ": st.column_config.TextColumn("🆔 Documento"),
                        "ROTA": st.column_config.TextColumn("🚚 Rota")
                    },
                    hide_index=True,
                    use_container_width=True,
                    height=400
                )
            else:
                st.info("Nenhum cliente encontrado na base de dados.")