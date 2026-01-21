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
tab_pedidos, tab_historico, tab_clientes = st.tabs(["📝 Novo Pedido", "📊 Gerenciar Status", "➕ Cadastrar Clientes"])

# --- ABA 1: NOVO PEDIDO ---
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    lista_nomes = db.listar_clientes() 

    with st.form(key="form_pedido", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1]) 
        
        with col1:
            if not lista_nomes:
                nome_cliente = st.text_input("Nome do Cliente (Avulso):")
            else:
                nome_cliente = st.selectbox("Selecione o Cliente:", options=lista_nomes)
        
        with col2:
            dia_entrega = st.date_input("Data de Entrega:", value=datetime.today())
            
        with col3:
            # AGORA SIM: Lista Completa de Opções
            status_inicial = st.selectbox(
                "Status Inicial:", 
                options=[
                    "GERADO", 
                    "PENDENTE", 
                    "NÃO GERADO", 
                    "CANCELADO", 
                    "ENTREGUE", 
                    "ORÇAMENTO", 
                    "RESERVADO"
                ],
                index=0 # "GERADO" continua como sugestão inicial
            )

        pedido = st.text_area("Descrição Detalhada:", height=150)
        botao_enviar = st.form_submit_button("💾 Salvar Pedido")

        if botao_enviar:
            if not pedido:
                st.warning("Preencha a descrição do pedido.")
            else:
                try:
                    # Envia o status escolhido para o banco
                    db.salvar_pedido(nome_cliente, pedido, dia_entrega, status_inicial)
                    st.success(f"✅ Pedido salvo com status '{status_inicial}'!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_historico:
    st.subheader("Painel de Controle de Status")
    
    df = db.buscar_pedidos_visualizacao() 
    
    if not df.empty:
        # Limpeza para garantir que acha a coluna
        df.columns = [c.strip() for c in df.columns]
        coluna_status_nome = next((c for c in df.columns if c.upper() == "STATUS"), None)

        if coluna_status_nome:
            colunas_bloqueadas = [c for c in df.columns if c != coluna_status_nome]

            df_editado = st.data_editor(
                df, 
                column_config={
                    coluna_status_nome: st.column_config.SelectboxColumn(
                        "Status Atual",
                        width="medium",
                        options=[
                            "PENDENTE", "GERADO", "NÃO GERADO", 
                            "CANCELADO", "ENTREGUE", "ORÇAMENTO", "RESERVADO"
                        ],
                        required=True
                    )
                },
                disabled=colunas_bloqueadas, 
                num_rows="fixed",
                use_container_width=True,
                key="editor_pedidos",
                height=500
            )
            
            if st.button("💾 Atualizar Status na Nuvem", type="primary"):
                try:
                    db.atualizar_apenas_status(df_editado) 
                    st.success("✅ Status atualizados com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.error("⚠️ Coluna 'STATUS' não encontrada na planilha.")
    else:
        st.info("Nenhum pedido encontrado.")

# --- ABA 3: CLIENTES ---
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