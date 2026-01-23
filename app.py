import streamlit as st
import time
import plotly.express as px
from datetime import datetime
import services.database as db
import ui.styles as styles

# --- CONFIGURAÇÕES GLOBAIS ---
LISTA_STATUS = [
    "GERADO", 
    "PENDENTE", 
    "NÃO GERADO", 
    "CANCELADO", 
    "ENTREGUE", 
    "ORÇAMENTO", 
    "RESERVADO"
]

LISTA_PAGAMENTO = [
    "A COMBINAR", 
    "PIX", 
    "BOLETO", 
    "CARTÃO"
]

# MAPA DE CORES
CORES_STATUS = {
    "GERADO": "#FFA500",       "🆕 GERADO": "#FFA500",      # Laranja
    "PENDENTE": "#FFEB3B",     "⏳ PENDENTE": "#FFEB3B",    # Amarelo
    "NÃO GERADO": "#8B0000",   "🔴 NÃO GERADO": "#8B0000",  # Vermelho Escuro
    "CANCELADO": "#FF8080",    "🚫 CANCELADO": "#FF8080",   # Salmão
    "ENTREGUE": "#28A745",     "✅ ENTREGUE": "#28A745",    # Verde
    "ORÇAMENTO": "#E0E0E0",    "📝 ORÇAMENTO": "#E0E0E0",   # Cinza Claro
    "RESERVADO": "#0056b3",    "🔒 RESERVADO": "#0056b3"    # Azul Forte
}

# 1. Configuração da Página
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Carregar Estilos
styles.aplicar_estilos()

# 3. Inicializar Estado do Formulário (Form ID)
if "form_id" not in st.session_state:
    st.session_state.form_id = 0

# 3. Sidebar
with st.sidebar:
    try:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
    except:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

    st.markdown("---")
    
    st.link_button(
        label="📊 Acessar Planilha Google", 
        url="https://docs.google.com/spreadsheets/d/1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc/edit?usp=sharing",
        use_container_width=True
    )
    
    st.markdown("---")
    st.info("Sistema de Gestão\n**JT Pescados**")

# --- CORPO PRINCIPAL ---
st.title("📦 Gestão de Pedidos")

# --- CABEÇALHO DE MÉTRICAS (HEADER) ---
with st.container():
    total_clientes, total_pedidos = db.get_metricas()
    
    c_meta1, c_meta2 = st.columns(2)
    
    with c_meta1:
        st.metric("👥 Total de Clientes", total_clientes)
        
    with c_meta2:
        st.metric("📦 Pedidos Realizados", total_pedidos)

# --- ABAS ---
tab_dash, tab_pedidos, tab_historico, tab_clientes = st.tabs([
    "📈 Dashboard", 
    "📝 Novo Pedido", 
    "📊 Gerenciar Pedidos", 
    "➕ Cadastrar Clientes"
])


# --- ABA 1: DASHBOARD ---
with tab_dash:
    st.subheader("📊 Visão Geral da Operação")
    
    # Função de Cores (Badges)
    def colorir_status(val):
        val_str = str(val).upper()
        bg_color = "transparent"
        color = "white"
        
        if "PENDENTE" in val_str:
            bg_color = "#FFEB3B"; color = "black"
        elif "GERADO" in val_str and "NÃO" not in val_str:
            bg_color = "#FFA500"; color = "black"
        elif "NÃO GERADO" in val_str or "NAO GERADO" in val_str:
            bg_color = "#8B0000"; color = "white"
        elif "CANCELADO" in val_str:
            bg_color = "#FF8080"; color = "black"
        elif "ENTREGUE" in val_str:
            bg_color = "#28A745"; color = "white"
        elif "ORÇAMENTO" in val_str:
            bg_color = "#E0E0E0"; color = "black"
        elif "RESERVADO" in val_str:
            bg_color = "#0056b3"; color = "white"
            
        return f'background-color: {bg_color}; color: {color}; border-radius: 4px; font-weight: bold; padding: 2px'

    with st.container(border=True): 
        df = db.buscar_pedidos_visualizacao()
        
        if not df.empty:
            df.columns = [c.strip().upper() for c in df.columns]
            
            if "STATUS" in df.columns:
                contagem_status = df["STATUS"].value_counts().reset_index()
                contagem_status.columns = ["STATUS", "QUANTIDADE"]
                
                col_grafico, col_dados = st.columns([1.8, 1]) 
                
                with col_grafico:
                    fig = px.pie(
                        contagem_status, 
                        values="QUANTIDADE", 
                        names="STATUS", 
                        color="STATUS", 
                        hole=0.7,
                        color_discrete_map=CORES_STATUS 
                    )
                    
                    fig.update_traces(
                        textposition='outside', 
                        textinfo='percent+label',
                        insidetextorientation='horizontal',
                        marker=dict(line=dict(color='#000000', width=2)),
                        textfont_size=14
                    )
                    
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(size=12, color="white"),
                        showlegend=False, 
                        margin=dict(t=20, b=60, l=60, r=60) 
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, height=500)
                
                with col_dados:
                    st.markdown("### Resumo Rápido")
                    
                    entregues = len(df[df["STATUS"].astype(str).str.contains("ENTREGUE", case=False)])
                    termos_ativos = "PENDENTE|GERADO|ORÇAMENTO|NÃO GERADO|RESERVADO"
                    em_andamento = len(df[df["STATUS"].astype(str).str.contains(termos_ativos, case=False, regex=True)])
                    cancelados = len(df[df["STATUS"].astype(str).str.contains("CANCELADO", case=False)])
                    
                    c1, c2, c3 = st.columns(3)
                    with c1: st.metric("✅ Entregues", entregues)
                    with c2: st.metric("🏃 Ativos", em_andamento)
                    with c3: st.metric("🚫 Cancelados", cancelados)
                    
                    st.markdown("---")
                    
                    if "PAGAMENTO" in df.columns:
                        st.caption("💳 Preferência de Pagamento")
                        df_pagto = df[df["PAGAMENTO"] != ""]
                        contagem_pagto = df_pagto["PAGAMENTO"].value_counts().reset_index()
                        contagem_pagto.columns = ["MEIO", "QTD"]
                        
                        fig_pagto = px.bar(
                            contagem_pagto,
                            x="QTD",
                            y="MEIO",
                            orientation='h',
                            text="QTD",
                            color_discrete_sequence=["#00CC96"]
                        )
                        
                        fig_pagto.update_traces(
                            textposition='outside',
                            marker_line_color='rgb(0,0,0)',
                            marker_line_width=1.5
                        )
                        
                        fig_pagto.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font=dict(color="white"),
                            xaxis=dict(showgrid=False, showticklabels=False),
                            yaxis=dict(showgrid=False),
                            margin=dict(t=0, b=0, l=0, r=0),
                            height=200
                        )
                        
                        st.plotly_chart(fig_pagto, use_container_width=True)
                    
                    st.markdown("---")
                    st.caption("Detalhamento de Status:")
                    
                    st.dataframe(
                        contagem_status.style.applymap(colorir_status, subset=["STATUS"]),
                        use_container_width=True,
                        hide_index=True
                    )
                    
            else:
                st.warning("⚠️ Aguardando dados de STATUS...")
        else:
            st.info("📭 Aguardando o primeiro pedido...")


# --- ABA 2: NOVO PEDIDO ---
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    lista_nomes = db.listar_clientes() 

    with st.container(border=True):
        st.markdown("#### 📝 Dados do Pedido")
        
        # --- LINHA 1: CLIENTE E DATA ---
        c_topo1, c_topo2 = st.columns([2, 1])
        
        with c_topo1:
            try:
                idx_def = lista_nomes.index("VENDA A CONSUMIDOR")
            except:
                idx_def = 0

            key_cliente_manual = f"cliente_manual_{st.session_state.form_id}"
            key_cliente_select = f"cliente_select_{st.session_state.form_id}"

            if not lista_nomes:
                nome_cliente = st.text_input("Nome do Cliente (Avulso):", key=key_cliente_manual)
            else:
                nome_cliente = st.selectbox("👤 Selecione o Cliente:", options=lista_nomes, index=idx_def, key=key_cliente_select)
        
        with c_topo2:
            key_data = f"data_entrega_{st.session_state.form_id}"
            dia_entrega = st.date_input("📅 Entrega:", value=datetime.today(), key=key_data)

        st.markdown("---")

        # --- LINHA 2: DADOS FINANCEIROS E STATUS ---
        
        key_check = f"check_nr_{st.session_state.form_id}"
        usar_nr = st.checkbox("Deseja informar o **Número do Pedido (NR)**?", value=False, key=key_check)
        
        if usar_nr:
            cols = st.columns(3)
        else:
            cols = st.columns(2)

        key_pagto = f"pagto_{st.session_state.form_id}"
        key_status = f"status_{st.session_state.form_id}"
        key_nr = f"nr_input_{st.session_state.form_id}"

        with cols[0]:
            pagamento_inicial = st.selectbox("💳 Pagamento:", options=LISTA_PAGAMENTO, index=0, key=key_pagto)
        
        with cols[1]:
            status_inicial = st.selectbox("📊 Status:", options=LISTA_STATUS, index=0, key=key_status)
            
        if usar_nr:
            with cols[2]:
                nr_pedido_input = st.text_input("🔢 Nº Pedido:", placeholder="Digite...", key=key_nr)
        else:
            nr_pedido_input = "" 

        # --- LINHA 3: DESCRIÇÃO ---
        st.markdown("<br>", unsafe_allow_html=True)
        key_desc = f"descricao_{st.session_state.form_id}"
        pedido = st.text_area("🛒 Descrição do Pedido:", height=150, placeholder="Ex: 5kg de Tilápia, 2 Pacotes de Camarão...", key=key_desc)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        botao_enviar = st.button("💾 Salvar Pedido", type="primary", use_container_width=True)

        if botao_enviar:
            if not pedido:
                st.warning("Preencha a descrição do pedido.")
            else:
                try:
                    db.salvar_pedido(nome_cliente, pedido, dia_entrega, pagamento_inicial, status_inicial, nr_pedido_input)
                    st.success(f"✅ Pedido Salvo! Status: **{status_inicial}**")
                    time.sleep(1)
                    
                    st.session_state.form_id += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- ABA 3: GERENCIAMENTO ---
with tab_historico:
    st.subheader("Painel de Controle")
    
    with st.container(border=True):
        df = db.buscar_pedidos_visualizacao() 
        
        if not df.empty:
            df.columns = [c.strip().upper() for c in df.columns] 
            
            # --- ATUALIZADO: Identificação das colunas ---
            col_id = "ID_PEDIDO" if "ID_PEDIDO" in df.columns else None
            col_status = "STATUS" if "STATUS" in df.columns else None
            col_pagto = "PAGAMENTO" if "PAGAMENTO" in df.columns else None
            col_nr = "NR PEDIDO" if "NR PEDIDO" in df.columns else None

            if col_status and col_pagto:
                # Definimos quais colunas podem ser editadas
                campos_editaveis = [col_status, col_pagto]
                if col_nr:
                    campos_editaveis.append(col_nr)
                
                # Todas as outras são bloqueadas (incluindo o ID)
                colunas_bloqueadas = [c for c in df.columns if c not in campos_editaveis]

                # Configuração visual das colunas
                config_colunas = {
                    col_status: st.column_config.SelectboxColumn(
                        "Status", width="medium",
                        options=LISTA_STATUS, 
                        required=True
                    ),
                    col_pagto: st.column_config.SelectboxColumn(
                        "Pagamento", width="medium",
                        options=LISTA_PAGAMENTO, 
                        required=True
                    )
                }
                
                # Configuração especial para o ID (se existir)
                if col_id:
                     config_colunas[col_id] = st.column_config.NumberColumn(
                        "# ID", width="small", format="%d"
                     )

                # Configuração para o NR PEDIDO (se existir)
                if col_nr:
                    config_colunas[col_nr] = st.column_config.TextColumn(
                        "Nr Pedido", width="small",
                        help="Edite o número do pedido aqui se necessário"
                    )

                df_editado = st.data_editor(
                    df, 
                    column_config=config_colunas,
                    disabled=colunas_bloqueadas, 
                    num_rows="fixed",
                    use_container_width=True,
                    key="editor_pedidos",
                    height=500
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("💾 Atualizar Alterações na Nuvem", type="primary", use_container_width=True):
                    try:
                        db.atualizar_pedidos_editaveis(df_editado) 
                        st.success("✅ Dados atualizados com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")
            else:
                st.error("⚠️ Colunas 'STATUS' ou 'PAGAMENTO' não encontradas.")
                st.dataframe(df)
        else:
            st.info("Nenhum pedido encontrado.")

# --- ABA 4: CLIENTES ---
with tab_clientes:
    st.subheader("Cadastro de Parceiros")
    
    with st.container(border=True):
        with st.form(key="form_novo_cliente", clear_on_submit=True):
            st.markdown("#### 👤 Dados do Novo Cliente")
            c1, c2 = st.columns([2, 1])
            with c1: novo_nome = st.text_input("Nome do Cliente / Empresa")
            with c2: nova_cidade = st.text_input("Cidade", value="SÃO CARLOS")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Salvar Novo Cliente", use_container_width=True):
                if novo_nome:
                    try:
                        db.criar_novo_cliente(novo_nome, nova_cidade) 
                        st.success("✅ Cliente cadastrado!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")