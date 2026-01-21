import streamlit as st
import time
from datetime import datetime
import services.database as db
import ui.styles as styles

# 1. Configuração da Página
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Carregar Estilos
styles.aplicar_estilos()

# 3. Sidebar e Métricas
with st.sidebar:
    try:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
    except:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

    st.markdown("---")
    
    total_clientes, total_pedidos = db.get_metricas()
        
    c1, c2 = st.columns(2)
    c1.metric("Clientes", total_clientes)
    c2.metric("Pedidos", total_pedidos)
    
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
tab_pedidos, tab_historico, tab_clientes = st.tabs(["📝 Novo Pedido", "📊 Gerenciar Pedidos", "➕ Cadastrar Clientes"])

# --- ABA 1: NOVO PEDIDO ---
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    lista_nomes = db.listar_clientes() 

    with st.form(key="form_pedido", clear_on_submit=True):
        # Layout: Linha 1 (Cliente e Data) | Linha 2 (Pagamento e Status)
        c1, c2 = st.columns([2, 1])
        with c1:
            if not lista_nomes:
                nome_cliente = st.text_input("Nome do Cliente (Avulso):")
            else:
                try:
                    index_padrao = lista_nomes.index("VENDA A CONSUMIDOR")
                except ValueError:
                    index_padrao = 0
                
                nome_cliente = st.selectbox("Selecione o Cliente:", options=lista_nomes, index=index_padrao)
        
        with c2:
            dia_entrega = st.date_input("Data de Entrega:", value=datetime.today())

        c3, c4 = st.columns(2)
        with c3:
            # NOVO: Campo de Pagamento
            pagamento_inicial = st.selectbox(
                "Forma de Pagamento:",
                options=["A COMBINAR", "PIX", "BOLETO", "CARTÃO"],
                index=0
            )
        
        with c4:
            status_inicial = st.selectbox(
                "Status Inicial:", 
                options=["GERADO", "PENDENTE", "NÃO GERADO", "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"],
                index=0 
            )

        pedido = st.text_area("Descrição Detalhada:", height=150)
        botao_enviar = st.form_submit_button("💾 Salvar Pedido")

        if botao_enviar:
            if not pedido:
                st.warning("Preencha a descrição do pedido.")
            else:
                try:
                    # Envia os 5 dados agora (incluindo pagamento)
                    db.salvar_pedido(nome_cliente, pedido, dia_entrega, pagamento_inicial, status_inicial)
                    st.success(f"✅ Pedido Salvo! (Status: {status_inicial} | Pagto: {pagamento_inicial})")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_historico:
    st.subheader("Painel de Controle")
    
    df = db.buscar_pedidos_visualizacao() 
    
    if not df.empty:
        df.columns = [c.strip().upper() for c in df.columns] # Normaliza tudo para Maiúsculo
        
        # Identifica colunas (procura por PAGAMENTO e STATUS)
        col_status = "STATUS" if "STATUS" in df.columns else None
        col_pagto = "PAGAMENTO" if "PAGAMENTO" in df.columns else None

        if col_status and col_pagto:
            # Bloqueia todas as colunas que NÃO sejam Pagamento ou Status
            colunas_bloqueadas = [c for c in df.columns if c not in [col_status, col_pagto]]

            df_editado = st.data_editor(
                df, 
                column_config={
                    col_status: st.column_config.SelectboxColumn(
                        "Status",
                        width="medium",
                        options=["PENDENTE", "GERADO", "NÃO GERADO", "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"],
                        required=True
                    ),
                    col_pagto: st.column_config.SelectboxColumn(
                        "Pagamento",
                        width="medium",
                        options=["A COMBINAR", "PIX", "BOLETO", "CARTÃO"],
                        required=True
                    )
                },
                disabled=colunas_bloqueadas, 
                num_rows="fixed",
                use_container_width=True,
                key="editor_pedidos",
                height=500
            )
            
            if st.button("💾 Atualizar Alterações na Nuvem", type="primary"):
                try:
                    db.atualizar_pedidos_editaveis(df_editado) 
                    st.success("✅ Dados atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.error("⚠️ Colunas 'STATUS' ou 'PAGAMENTO' não encontradas no cabeçalho da planilha.")
            st.dataframe(df)
    else:
        st.info("Nenhum pedido encontrado.")

# --- ABA 3: CLIENTES (Sem alterações) ---
with tab_clientes:
    st.subheader("Cadastro de Parceiros")
    with st.form(key="form_novo_cliente", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1: novo_nome = st.text_input("Nome do Cliente / Empresa")
        with c2: nova_cidade = st.text_input("Cidade", value="SÃO CARLOS")
        if st.form_submit_button("Salvar Novo Cliente"):
            if novo_nome:
                try:
                    db.criar_novo_cliente(novo_nome, nova_cidade) 
                    st.success("✅ Cliente cadastrado!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")