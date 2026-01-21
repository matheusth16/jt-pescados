import streamlit as st
import time
from datetime import datetime
# Importando nossos novos módulos
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
        # Tenta carregar da pasta assets se existir, ou url, ou fallback
        st.image("assets/imagem_empresa.jpg", use_container_width=True)
    except:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

    st.markdown("---")
    
    # Chamada ao Backend apenas para pegar números
    total_clientes, total_pedidos = db.get_metricas()
        
    c1, c2 = st.columns(2)
    c1.metric("Clientes", total_clientes)
    c2.metric("Pedidos", total_pedidos)
    
    st.markdown("---")
    st.info("Sistema de Gestão\n**JT Pescados**")

# --- CORPO PRINCIPAL ---
st.title("📦 Gestão de Pedidos")
tab_pedidos, tab_historico, tab_clientes = st.tabs(["📝 Novo Pedido", "📊 Gerenciar Pedidos", "➕ Cadastrar Clientes"])

# --- ABA 1: NOVO PEDIDO ---
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    lista_nomes = db.listar_clientes() # Backend

    with st.form(key="form_pedido", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if not lista_nomes:
                nome_cliente = st.text_input("Nome do Cliente (Avulso):")
            else:
                nome_cliente = st.selectbox("Selecione o Cliente:", options=lista_nomes)
        with col2:
            dia_entrega = st.date_input("Data de Entrega:", value=datetime.today())

        pedido = st.text_area("Descrição Detalhada:", height=150)
        botao_enviar = st.form_submit_button("💾 Salvar Pedido")

        if botao_enviar:
            if not pedido:
                st.warning("Preencha a descrição do pedido.")
            else:
                try:
                    # Backend faz o trabalho sujo
                    db.salvar_pedido(nome_cliente, pedido, dia_entrega)
                    st.success("✅ Pedido salvo com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

# --- ABA 2: GERENCIAMENTO ---
with tab_historico:
    st.subheader("Base de Dados Completa")
    
    df = db.buscar_todos_pedidos() # Backend
    
    if not df.empty:
        df_editado = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_pedidos",
            height=500
        )
        
        if st.button("💾 Salvar Alterações na Nuvem", type="primary"):
            try:
                db.atualizar_banco_completo(df_editado) # Backend
                st.success("✅ Banco atualizado!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")
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
                    db.criar_novo_cliente(novo_nome, nova_cidade) # Backend
                    st.success("✅ Cliente cadastrado!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")