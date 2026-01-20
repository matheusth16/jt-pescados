import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
import os
import time

# 1. Configuração da Página
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO PERSONALIZADO (BRANDING JT PESCADOS) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #B22222;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #8B0000;
        color: white;
    }
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FFD700;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO INTELIGENTE (LOCAL OU NUVEM) ---
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    KEY = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"
    
    try:
        # Tenta carregar localmente primeiro
        if os.path.exists("credentials.json"):
            gc = gspread.service_account(filename="credentials.json")
        else:
            # Se não existir arquivo, tenta ler dos Secrets (Streamlit Cloud)
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            gc = gspread.authorize(creds)
        
        return gc.open_by_key(KEY)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

sh = conectar_google_sheets()

if not sh:
    st.stop()

ws_pedidos = sh.sheet1 
ws_clientes = sh.worksheet("BaseClientes")

# --- BARRA LATERAL COM LOGO ---
with st.sidebar:
    try:
        st.image("imagem da empresa.jpg", use_container_width=True)
    except:
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

    st.markdown("---")
    
    try:
        total_clientes = len(ws_clientes.col_values(1)) - 1
        total_pedidos = len(ws_pedidos.col_values(1)) - 1
    except:
        total_clientes = 0
        total_pedidos = 0
        
    c1, c2 = st.columns(2)
    c1.metric("Clientes", total_clientes)
    c2.metric("Pedidos", total_pedidos)
    
    st.markdown("---")
    st.info("Sistema de Gestão\n**JT Pescados**")

# --- TÍTULO PRINCIPAL ---
st.title("📦 Gestão de Pedidos")

# --- CRIAÇÃO DAS ABAS ---
tab_pedidos, tab_historico, tab_clientes = st.tabs(["📝 Novo Pedido", "📊 Gerenciar Pedidos (CRUD)", "➕ Cadastrar Clientes"])

# ==================================================
# ABA 1: NOVO PEDIDO
# ==================================================
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    
    try:
        lista_nomes = sorted(list(set(ws_clientes.col_values(2)[1:])))
    except:
        lista_nomes = []

    with st.form(key="form_pedido", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            if not lista_nomes:
                nome_cliente = st.text_input("Nome do Cliente (Avulso):")
            else:
                nome_cliente = st.selectbox("Selecione o Cliente:", options=lista_nomes)
        with col2:
            dia_entrega = st.date_input("Data de Entrega:", value=datetime.today())

        pedido = st.text_area("Descrição Detalhada do Pedido:", height=150)
        botao_enviar = st.form_submit_button("💾 Salvar Pedido")

        if botao_enviar:
            if not pedido:
                st.warning("O campo de pedido não pode estar vazio.")
            else:
                try:
                    proxima_linha = len(ws_pedidos.col_values(1)) + 1
                    nova_linha = [
                        datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 
                        nome_cliente,
                        pedido, 
                        dia_entrega.strftime("%d/%m/%Y")
                    ]
                    ws_pedidos.insert_row(nova_linha, index=proxima_linha)
                    st.success(f"✅ Pedido salvo!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==================================================
# ABA 2: GERENCIAMENTO (CRUD COMPLETO)
# ==================================================
with tab_historico:
    st.subheader("Gerenciamento de Dados")
    st.caption("Clique nas células para editar ou selecione a linha e aperte 'Del' para excluir.")
    
    try:
        dados = ws_pedidos.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            
            df_editado = st.data_editor(
                df, 
                num_rows="dynamic", 
                use_container_width=True,
                key="editor_pedidos",
                height=500
            )
            
            if st.button("💾 Salvar Alterações na Nuvem", type="primary"):
                try:
                    ws_pedidos.clear()
                    novos_dados = [df_editado.columns.tolist()] + df_editado.values.tolist()
                    ws_pedidos.update(range_name="A1", values=novos_dados)
                    st.success("✅ Banco de dados atualizado!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
        else:
            st.info("Nenhum pedido registrado.")
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

# ==================================================
# ABA 3: CADASTRO DE CLIENTES
# ==================================================
with tab_clientes:
    st.subheader("Cadastro de Novos Parceiros")
    
    with st.form(key="form_novo_cliente", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            novo_nome = st.text_input("Nome do Cliente / Empresa")
        with c2:
            nova_cidade = st.text_input("Cidade", value="SÃO CARLOS")
            
        btn_cadastrar = st.form_submit_button("Salvar Novo Cliente")
        
        if btn_cadastrar:
            if novo_nome:
                try:
                    coluna_ids = ws_clientes.col_values(1)[1:]
                    ids_ocupados = {int(x) for x in coluna_ids if x.isdigit()}
                    novo_id = 1
                    while novo_id in ids_ocupados:
                        novo_id += 1
                    
                    ws_clientes.append_row([novo_id, novo_nome.upper(), nova_cidade.upper()])
                    st.success(f"✅ Cliente cadastrado!")
                    st.toast("Atualizando lista...", icon="🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")