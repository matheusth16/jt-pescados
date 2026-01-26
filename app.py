import streamlit as st
import time
import plotly.express as px
from datetime import datetime
import pandas as pd
from gspread.exceptions import APIError, WorksheetNotFound
import services.database as db
import ui.styles as styles
import ui.components as components

# --- CONFIGURAÇÕES GLOBAIS ---
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. GESTÃO DE SESSÃO RESILIENTE ---
def inicializar_sessao():
    """Garante que as variáveis de estado existam, sobrevivendo a recarregamentos."""
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
    
    # NOVAS VARIÁVEIS PARA O SALMÃO (ESTACA ZERO)
    if "salmao_df" not in st.session_state:
        st.session_state.salmao_df = pd.DataFrame()
    if "salmao_range_str" not in st.session_state:
        st.session_state.salmao_range_str = ""

# Esta chamada deve ficar no topo absoluto do script
inicializar_sessao()

# --- MODAL DE DESMEMBRAMENTO ---
@st.dialog("✂️ Desmembrar Tag (Fracionamento)")
def modal_desmembramento(tag_id, peso_atual):
    st.caption(f"Adicione uma nova unidade para a Tag {tag_id}.")
    
    letra, peso_unidade, cliente, status = components.render_split_form(tag_id, peso_atual)
    
    if st.button("Confirmar Unidade", type="primary", use_container_width=True):
        if not letra or not cliente:
            st.warning("Preencha Letra e Cliente.")
            return
        if peso_unidade <= 0:
            st.warning("O peso deve ser maior que zero.")
            return

        sucesso = db.registrar_subtag(
            tag_id, letra, cliente, peso_unidade, status, st.session_state.usuario_nome
        )
        if sucesso:
            st.success(f"Unidade {letra} registrada com sucesso!")
            time.sleep(1)
            st.rerun()

# --- CONSTANTES E ESTILOS ---
LISTA_STATUS = ["GERADO", "PENDENTE", "NÃO GERADO", "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"]
LISTA_PAGAMENTO = ["A COMBINAR", "PIX", "BOLETO", "CARTÃO"]

CORES_STATUS = styles.PALETA_CORES["STATUS"]

perfil_atual = st.session_state.usuario_perfil if st.session_state.logado else "Admin"
cores_tema = styles.aplicar_estilos(perfil=perfil_atual)
cor_principal = cores_tema["principal"]

# --- FUNÇÕES DE CACHE INTELIGENTE ---
@st.cache_data(show_spinner=False)
def carregar_clientes_cache(versao_hash):
    try:
        conn = db.get_connection()
        ws = conn.worksheet("BaseClientes")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            df.columns = [str(c).strip() for c in df.columns]
        return df
    except APIError as e:
        components.render_error_details("Google Sheets instável (429).", e)
        return pd.DataFrame()
    except Exception as e:
        components.render_error_details("Erro ao carregar clientes.", e)
        return pd.DataFrame()

@st.cache_data(show_spinner=False)
def carregar_pedidos_cache(versao_hash):
    try:
        return db.buscar_pedidos_visualizacao()
    except Exception as e:
        components.render_error_details("Erro ao sincronizar pedidos.", e)
        return pd.DataFrame()


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
                        st.session_state.usuario_nome = dados['nome']
                        st.session_state.usuario_perfil = dados['perfil']
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                except ConnectionError as e:
                    components.render_error_details("Sem conexão com a internet.", e)
                except Exception as e:
                    components.render_error_details("Erro técnico no login.", e)

# --- 3. SISTEMA PRINCIPAL ---
if not st.session_state.logado:
    tela_login()
else:
    try:
        hash_dados = db.obter_versao_planilha()
    except:
        hash_dados = time.time()

    NOME_USER = st.session_state.usuario_nome
    PERFIL = st.session_state.usuario_perfil

    with st.sidebar:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        components.render_user_card(NOME_USER, PERFIL)
        st.caption("🔄 Sincronizado")
        st.markdown("---")
        
        if PERFIL == "Admin":
            st.markdown("#### 🛠️ Ferramentas")
            st.link_button("📂 Planilha Master", "https://docs.google.com/spreadsheets/d/1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc/edit?usp=sharing", use_container_width=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logado = False
            st.rerun()

    st.title("📦 Portal de Pedidos Digital")
    
    try:
        qtd_cli, qtd_ped = db.get_metricas(_hash_versao=hash_dados)
    except Exception:
        qtd_cli, qtd_ped = "-", "-"
    
    m1, m2, m3 = st.columns(3)
    with m1: components.render_metric_card("👥 Total Clientes", qtd_cli, "#58a6ff")
    with m2: components.render_metric_card("📦 Pedidos Totais", qtd_ped, "#f1e05a")
    with m3: components.render_metric_card("👤 Usuário Logado", NOME_USER, "#238636")

    # --- NAVEGAÇÃO ---
    aba_dash = aba_novo = aba_gestao = aba_clientes = aba_salmao = None

    if PERFIL == "Admin":
        opcoes = ["📈 Dashboard", "📝 Novo Pedido", "👁️ Gerenciar", "🐟 Recebimento de Salmão", "➕ Clientes"]
        default_idx = 0
    else:
        opcoes = ["🚚 Operações", "🐟 Recebimento de Salmão", "📈 Indicadores"]
        default_idx = 0

    escolha_nav = st.segmented_control(
        "Menu Principal",
        opcoes,
        selection_mode="single",
        default=opcoes[default_idx],
        key="navegacao_principal"
    )
    
    st.markdown("---")

    if escolha_nav in ["📈 Dashboard", "📈 Indicadores"]: aba_dash = st.container()
    elif escolha_nav == "📝 Novo Pedido": aba_novo = st.container()
    elif escolha_nav in ["👁️ Gerenciar", "🚚 Operações"]: aba_gestao = st.container()
    elif escolha_nav == "➕ Clientes": aba_clientes = st.container()
    elif escolha_nav == "🐟 Recebimento de Salmão": aba_salmao = st.container()

    # =========================================================================
    # ABA: RECEBIMENTO DE SALMÃO (NOVA E BLINDADA)
    # =========================================================================
    if aba_salmao:
        with aba_salmao:
            st.subheader("🐟 Recebimento de Salmão")
            st.info("ℹ️ Para evitar lentidão, o sistema carrega os dados apenas sob demanda.")

            # --- PAINEL DE COMANDO (ESTACA ZERO) ---
            with st.container(border=True):
                c_in, c_fim, c_btn = st.columns([1, 1, 2], vertical_alignment="bottom")
                
                with c_in:
                    tag_start = st.number_input("Tag Inicial", min_value=1, value=1, step=1)
                with c_fim:
                    tag_end = st.number_input("Tag Final", min_value=1, value=50, step=1)
                
                with c_btn:
                    carregar = st.button("🔍 Carregar Intervalo", type="primary", use_container_width=True)

            # --- LÓGICA DE CARREGAMENTO SEGURO ---
            if carregar:
                qtd_solicitada = tag_end - tag_start + 1
                
                # 1. TRAVA DE SEGURANÇA
                if qtd_solicitada > 50:
                    st.error(f"⚠️ Atenção: Você tentou carregar {qtd_solicitada} tags.")
                    st.warning("⛔ O limite máximo é de 50 tags por vez para evitar travamentos.")
                    st.session_state.salmao_df = pd.DataFrame() # Limpa para garantir
                elif tag_end < tag_start:
                    st.error("Erro: A Tag Final deve ser maior que a Inicial.")
                else:
                    # 2. CARREGAMENTO PERMITIDO
                    with st.spinner(f"Buscando Tags de {tag_start} a {tag_end}..."):
                        df_res = db.get_estoque_filtrado(tag_start, tag_end)
                        st.session_state.salmao_df = df_res
                        st.session_state.salmao_range_str = f"Tags {tag_start} a {tag_end}"

            # --- VISUALIZAÇÃO DA TABELA ---
            if not st.session_state.salmao_df.empty:
                st.markdown(f"### 📋 Editando: {st.session_state.salmao_range_str}")
                
                df_view = st.session_state.salmao_df
                
                if PERFIL == "Admin":
                    # Admin apenas vê
                    st.dataframe(df_view, use_container_width=True, hide_index=True)
                else:
                    # Operador EDITA
                    cfg_colunas = {
                        "Tag": st.column_config.NumberColumn("Tag", disabled=True, format="%d"),
                        "Calibre": st.column_config.SelectboxColumn("Calibre", options=["8/10", "10/12", "12/14", "14/16"]),
                        "Status": st.column_config.SelectboxColumn("Status", options=["Livre", "Reservado", "Orçamento", "Gerado", "Aberto"]),
                        "Peso": st.column_config.NumberColumn("Peso (kg)", format="%.2f"),
                        "Validade": st.column_config.TextColumn("Validade"),
                        "Cliente": st.column_config.TextColumn("Cliente Destino")
                    }

                    tabela_editada = st.data_editor(
                        df_view,
                        key="editor_salmao_safe",
                        use_container_width=True,
                        height=500,
                        hide_index=True,
                        column_config=cfg_colunas,
                        selection_mode="single-row" # Habilita seleção para o botão de corte
                    )
                    
                    c_save, c_split = st.columns([1, 1])
                    
                    with c_save:
                        if st.button("💾 Salvar Alterações", type="primary"):
                            with st.spinner("Gravando..."):
                                n = db.salvar_alteracoes_estoque(tabela_editada, NOME_USER)
                                if n > 0:
                                    st.success(f"✅ {n} linhas atualizadas!")
                                    # Atualiza o cache local
                                    st.session_state.salmao_df = tabela_editada
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.info("Nenhuma alteração detectada.")

                    with c_split:
                        # Lógica do Desmembramento
                        sel = st.session_state["editor_salmao_safe"].get("selection", {}).get("rows", [])
                        if sel:
                            idx_row = sel[0]
                            row_data = tabela_editada.iloc[idx_row]
                            status_atual = str(row_data.get("Status", "")).upper()
                            
                            if "ABERTO" in status_atual:
                                if st.button(f"✂️ Desmembrar Tag {row_data['Tag']}", type="secondary"):
                                    modal_desmembramento(row_data['Tag'], row_data['Peso'])
                            else:
                                st.caption("Para desmembrar, mude o Status para 'Aberto' e Salve.")
                        else:
                            st.caption("👆 Selecione uma linha com status ABERTO para fracionar.")

            else:
                if st.session_state.salmao_range_str:
                    st.warning("Nenhum dado encontrado neste intervalo.")

    # =========================================================================
    # ABA: DASHBOARD
    # =========================================================================
    if aba_dash:
        with aba_dash:
            c_titulo, c_filtro = st.columns([1, 1.2], vertical_alignment="center")
            with c_titulo:
                st.markdown("### 📊 Indicadores de Performance")
            with c_filtro:
                filtro_tempo = st.segmented_control(
                    "Período:", options=["Hoje", "Últimos 7 Dias", "Mês Atual", "Tudo"], 
                    default="Tudo", selection_mode="single", label_visibility="collapsed"
                )
            if not filtro_tempo: filtro_tempo = "Tudo"
            st.markdown("---")

            df_bruto = carregar_pedidos_cache(hash_dados)
            
            if not df_bruto.empty:
                df_bruto.columns = [c.upper().strip() for c in df_bruto.columns]
                col_dt = next((c for c in df_bruto.columns if "ENTREGA" in c), None)

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
                
                # GRÁFICOS
                c_pizza, c_barra = st.columns(2)
                with c_pizza:
                    with st.container(border=True):
                        st.markdown("#### Status dos Pedidos")
                        if "STATUS" in df_dash.columns:
                            contagem_status = df_dash["STATUS"].value_counts().reset_index()
                            contagem_status.columns = ["STATUS", "TOTAL"]
                            fig_status = px.pie(contagem_status, values="TOTAL", names="STATUS", 
                                            hole=0.6, color="STATUS", color_discrete_map=CORES_STATUS)
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
                            fig_pg.update_layout(xaxis_title="", yaxis_title="",
                                margin=dict(t=30, b=10, l=10, r=10),
                                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                                font=dict(color="white"), xaxis=dict(showgrid=False, showticklabels=False))
                            fig_pg.update_traces(marker_line_color='rgba(0,0,0,0)', textposition='outside')
                            st.plotly_chart(fig_pg, use_container_width=True)

                # SAÚDE DA OPERAÇÃO
                st.markdown("#### Resumo da Operação")
                c1, c2, c3 = st.columns(3)
                with c1:
                    entregues = len(df_dash[df_dash["STATUS"] == "ENTREGUE"]) if "STATUS" in df_dash.columns else 0
                    pct_saude = (entregues / total_pedidos * 100) if total_pedidos > 0 else 0
                    classe_cor = "saude-baixa" if pct_saude < 50 else "saude-media" if pct_saude < 80 else "saude-alta"
                    components.render_status_card("🩺 Saúde da Operação", f"{pct_saude:.1f}%", css_class=classe_cor)
                with c2:
                    pendentes = len(df_dash[df_dash["STATUS"].isin(["PENDENTE", "GERADO"])]) if "STATUS" in df_dash.columns else 0
                    components.render_status_card("⏳ Aguardando Processo", pendentes, inline_color="#FFA500")
                with c3:
                    components.render_status_card("✅ Pedidos Entregues", entregues, inline_color="#28A745")
                
                # EVOLUÇÃO
                st.markdown("#### 📈 Evolução de Pedidos por Dia")
                with st.container(border=True):
                    if col_dt and not df_dash.empty:
                        evolucao_diaria = df_dash.groupby(df_dash[col_dt].dt.date).size().reset_index(name='QTD')
                        evolucao_diaria.columns = ['DATA', 'QTD']
                        evolucao_diaria = evolucao_diaria.sort_values('DATA')
                        fig_evol = px.line(evolucao_diaria, x='DATA', y="QTD", markers=True, 
                                        line_shape="spline", color_discrete_sequence=[cor_principal])
                        fig_evol.update_layout(xaxis_title="", yaxis_title="Pedidos",
                            margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="white"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
                        st.plotly_chart(fig_evol, use_container_width=True)
                        
                # TOP CLIENTES
                st.markdown("#### 🏆 Top 5 Clientes do Período")
                with st.container(border=True):
                    if "NOME CLIENTE" in df_dash.columns:
                        top_clientes = df_dash["NOME CLIENTE"].value_counts().reset_index().head(5)
                        top_clientes.columns = ["CLIENTE", "QTD"]
                        max_pedidos = top_clientes["QTD"].max() if not top_clientes.empty else 1
                        st.data_editor(top_clientes, column_config={
                                "CLIENTE": st.column_config.TextColumn("👤 Nome do Cliente"),
                                "QTD": st.column_config.ProgressColumn("📦 Volume de Pedidos", format="%d", min_value=0, max_value=int(max_pedidos)),
                            }, hide_index=True, use_container_width=True, disabled=True)
            else:
                st.info("Sem dados para exibir (ou houve falha no carregamento).")

    # =========================================================================
    # ABA: NOVO PEDIDO
    # =========================================================================
    if PERFIL == "Admin" and aba_novo:
        with aba_novo:
            st.markdown("### 📝 Novo Pedido")
            
            df_clientes_completo = carregar_clientes_cache(hash_dados)
            lista_nomes = ["Consumidor Final"]

            if not df_clientes_completo.empty:
                if "Cliente" in df_clientes_completo.columns:
                    nomes_validos = df_clientes_completo["Cliente"].dropna().astype(str).str.upper().unique()
                    lista_nomes = sorted([n for n in nomes_validos if n.strip() != ""])

            with st.container(border=True):
                st.markdown("#### 1️⃣ Identificação e Entrega")
                c1, c2 = st.columns([2, 1])
                
                with c1: 
                    idx_padrao = 0
                    if "VENDA A CONSUMIDOR" in lista_nomes:
                        idx_padrao = lista_nomes.index("VENDA A CONSUMIDOR")
                    
                    cli = st.selectbox("Cliente:", lista_nomes, index=idx_padrao, key=f"c_{st.session_state.form_id}")
                    
                    cidade_cli = "Não informado"
                    rota_cli = "-"
                    
                    if not df_clientes_completo.empty and "Cliente" in df_clientes_completo.columns:
                        try:
                            row_cli = df_clientes_completo[df_clientes_completo["Cliente"].astype(str).str.upper() == str(cli).upper()]
                            if not row_cli.empty:
                                cidade_cli = row_cli.iloc[0].get("Nome Cidade", "SÃO CARLOS")
                                rota_cli = row_cli.iloc[0].get("ROTA", "-")
                        except:
                            pass 

                    rota_upper = str(rota_cli).strip().upper()
                    if "RETIRADA" in rota_upper:
                        st.info(f"📍 **Cidade:** {cidade_cli}  |  🏢 **Rota:** {rota_cli} (Cliente vem buscar)")
                    elif rota_cli in ["-", "Não definido", "", "None"]:
                        st.warning(f"📍 **Cidade:** {cidade_cli}  |  ⚠️ **Rota:** Pendente de Logística")
                    else:
                        st.success(f"📍 **Cidade:** {cidade_cli}  |  🚚 **Rota:** {rota_cli} (Entrega Externa)")

                    @st.dialog("📜 Histórico Completo")
                    def modal_historico(cliente_nome):
                        st.markdown(f"### 👤 {cliente_nome}")
                        st.caption("Visualizando os últimos pedidos encontrados.")
                        st.markdown("---")
                        
                        try:
                            df_hist_bruto = carregar_pedidos_cache(hash_dados)
                            itens_historico = db.obter_resumo_historico(df_hist_bruto, cliente_nome)
                            
                            if itens_historico:
                                for item in itens_historico[:10]:
                                    components.render_history_item(
                                        id_ped=item['id'],
                                        data=item['data'],
                                        status=item['status'],
                                        descricao=item['descricao'],
                                        pagamento=item['pagamento']
                                    )
                                
                                restante = len(itens_historico) - 10
                                if restante > 0:
                                    st.info(f"E mais {restante} pedidos antigos...")
                            else:
                                st.warning("📭 Nenhum histórico encontrado para este cliente.")
                        except Exception as e:
                            st.error(f"Erro ao carregar: {e}")

                    if st.button("📜 Ver Histórico", use_container_width=True):
                        modal_historico(cli)
                        
                with c2: 
                    dt = st.date_input("Data de Entrega:", datetime.today(), format="DD/MM/YYYY", key=f"d_{st.session_state.form_id}")
                    if dt < datetime.today().date():
                        st.warning("⚠️ Atenção: Data retroativa!")
                    st.write("")
                    st.write("")
                    try:
                        df_vol = carregar_pedidos_cache(hash_dados)
                        if not df_vol.empty:
                            data_sel = dt.strftime("%d/%m/%Y")
                            pedidos_no_dia = len(df_vol[df_vol["DIA DA ENTREGA"] == data_sel])
                            st.metric("📅 Agendamentos do Dia", f"{pedidos_no_dia} Pedidos")
                    except:
                        pass

                st.divider()
                st.markdown("#### 2️⃣ Detalhes Comerciais")
                c3, c4 = st.columns(2)
                with c3: pg = st.selectbox("Forma de Pagamento:", LISTA_PAGAMENTO, key=f"p_{st.session_state.form_id}")
                with c4: stt = st.selectbox("Status Inicial:", LISTA_STATUS, index=2, key=f"s_{st.session_state.form_id}")
                
                usar_nr = st.checkbox("Informar NR do Pedido externo?", key=f"chk_{st.session_state.form_id}")
                nr_ped = ""
                if usar_nr:
                    nr_ped = st.text_input("Digite o NR do Pedido:", placeholder="Ex: 12345", key=f"nr_{st.session_state.form_id}")

                st.divider()
                st.markdown("#### 3️⃣ Itens do Pedido")
                desc = st.text_area("Descrição (Quantidade e Produtos):", height=150, placeholder="Ex: 10kg de Tilápia...", key=f"de_{st.session_state.form_id}")
                form_invalido = len(desc.strip()) == 0

                if desc:
                    st.markdown("---")
                    components.render_preview_card(cli, dt, rota_cli, pg, stt, cor_principal)
                    st.markdown("<br>", unsafe_allow_html=True)
                else:
                    st.caption("📝 *Preencha a descrição dos itens para liberar o botão de cadastro.*")

                # --- 4. PREVENÇÃO DE DUPLO CLIQUE ---
                c_btn1, c_btn2 = st.columns([3, 1])
                
                with c_btn1:
                    if st.session_state.processando_envio:
                        components.render_loader_action("🚀 Enviando pedido para o Google Sheets...")
                        try:
                            db.salvar_pedido(cli, desc, dt, pg, stt, nr_pedido=nr_ped, usuario_logado=NOME_USER)
                            carregar_pedidos_cache.clear()
                            carregar_clientes_cache.clear()
                            st.toast(f"✅ Pedido para **{cli}** salvo com sucesso!", icon="🎉")
                            time.sleep(1.5)
                            st.session_state.processando_envio = False
                            st.session_state.form_id += 1
                            st.rerun()
                        except APIError as e:
                            components.render_error_details("Limite do Google (429). Aguarde e tente de novo.", e)
                            st.session_state.processando_envio = False 
                        except ConnectionError as e:
                            components.render_error_details("Sem conexão com a internet.", e)
                            st.session_state.processando_envio = False
                        except Exception as e:
                            components.render_error_details("Erro inesperado ao gravar.", e)
                            st.session_state.processando_envio = False

                    else:
                        def iniciar_envio():
                            st.session_state.processando_envio = True

                        st.button("🚀 CADASTRAR PEDIDO", 
                                  type="primary", 
                                  use_container_width=True, 
                                  disabled=form_invalido, 
                                  on_click=iniciar_envio)
                
                with c_btn2:
                    if st.button("🗑️ Limpar", 
                                 use_container_width=True, 
                                 disabled=st.session_state.processando_envio):
                        st.session_state.form_id += 1
                        st.rerun()

    # =========================================================================
    # ABA: GESTÃO (MISTA)
    # =========================================================================
    if aba_gestao:
        with aba_gestao:
            st.subheader("📋 Painel de Controle")
            
            df_gestao = carregar_pedidos_cache(hash_dados)
            
            if not df_gestao.empty:
                df_gestao.columns = [c.upper().strip() for c in df_gestao.columns]

                with st.expander("🔍 Filtros de Busca", expanded=False):
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: 
                        f_status = st.multiselect("Filtrar por Status:", LISTA_STATUS, default=[])
                    with c_f2:
                        col_dt_nome = next((c for c in df_gestao.columns if "ENTREGA" in c), None)
                        f_data = st.date_input("Filtrar por Data:", value=[]) if col_dt_nome else None

                df_display = df_gestao.copy()
                if f_status:
                    df_display = df_display[df_display["STATUS"].isin(f_status)]
                
                cfg_visual = {
                    "ID_PEDIDO": st.column_config.NumberColumn("🆔 ID", format="%d", width="small"),
                    "NOME CLIENTE": st.column_config.TextColumn("👤 Cliente", width="medium"),
                    "STATUS": st.column_config.SelectboxColumn("📊 Status", options=LISTA_STATUS, required=True, width="medium"),
                    "PAGAMENTO": st.column_config.SelectboxColumn("💳 Pagamento", options=LISTA_PAGAMENTO, width="medium"),
                    "DIA DA ENTREGA": st.column_config.TextColumn("📅 Entrega")
                }

                df_estilizado = df_display.style.map(
                    lambda x: f'background-color: {CORES_STATUS.get(x, "")}; color: {"white" if x in ["NÃO GERADO", "RESERVADO", "ENTREGUE"] else "black"}', 
                    subset=['STATUS']
                )

                if PERFIL == "Admin":
                    st.dataframe(df_estilizado, use_container_width=True, height=600, hide_index=True)
                else:
                    df_editado = st.data_editor(
                        df_display, column_config=cfg_visual,
                        use_container_width=True, height=600, hide_index=True, key="tabela_operador"
                    )

                    if st.button("💾 CONFIRMAR ALTERAÇÕES", type="primary", use_container_width=True):
                        try:
                            db.atualizar_pedidos_editaveis(df_editado, usuario_logado=NOME_USER)
                            carregar_pedidos_cache.clear()
                            st.success("✅ Atualizado!")
                            time.sleep(1)
                            st.rerun()
                        except APIError as e:
                            components.render_error_details("Erro 429: Muitos acessos simultâneos.", e)
                        except Exception as e:
                            components.render_error_details("Falha ao atualizar pedidos.", e)

    # =========================================================================
    # ABA: CLIENTES (EXCLUSIVO ADMIN)
    # =========================================================================
    if PERFIL == "Admin" and aba_clientes:
        with aba_clientes:
            st.subheader("➕ Gestão de Clientes")
            
            with st.container(border=True):
                with st.form("cad_cli", clear_on_submit=True):
                    nn = st.text_input("Nome do Cliente / Empresa", placeholder="Razão Social ou Nome Fantasia")
                    c1, c2 = st.columns(2)
                    with c1: cc = st.text_input("Cidade", value="SÃO CARLOS")
                    with c2: doc_raw = st.text_input("CPF/CNPJ", placeholder="Digite apenas os números")
                    
                    doc_limpo = "".join(filter(str.isdigit, doc_raw))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("SALVAR NOVO CLIENTE", use_container_width=True):
                        if not nn:
                            st.warning("O Nome do Cliente é obrigatório.")
                        elif doc_limpo and len(doc_limpo) not in [11, 14]:
                            st.error(f"⚠️ Documento Inválido! Detectamos {len(doc_limpo)} dígitos.")
                        else:
                            try:
                                db.criar_novo_cliente(nn, cc, doc_limpo)
                                carregar_clientes_cache.clear()
                                st.success(f"✅ {nn} cadastrado com sucesso!")
                                time.sleep(1)
                                st.rerun()
                            except Exception as e:
                                components.render_error_details("Erro ao criar cliente.", e)

            st.markdown("---")
            st.markdown("### 🔍 Clientes já Cadastrados")
            df_clientes_view = carregar_clientes_cache(hash_dados)
            
            if not df_clientes_view.empty:
                st.write(f"Atualmente você possui **{len(df_clientes_view)}** clientes na base.")
                st.dataframe(df_clientes_view, column_config={
                        "ID": st.column_config.NumberColumn("ID", format="%d"),
                        "Cliente": st.column_config.TextColumn("👤 Cliente"),
                        "Nome Cidade": st.column_config.TextColumn("📍 Cidade"),
                        "CPF/CNPJ": st.column_config.TextColumn("🆔 Documento"),
                        "ROTA": st.column_config.TextColumn("🚚 Rota")
                    }, hide_index=True, use_container_width=True, height=400)
            else:
                st.info("Nenhum cliente encontrado na base de dados (ou falha no carregamento).")