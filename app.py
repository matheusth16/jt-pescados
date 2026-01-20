import streamlit as st
import gspread
import pandas as pd
from datetime import datetime

# 1. Configuração da Página (Primeiro comando obrigatório)
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
    /* Botões: Vermelho da Marca */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #B22222; /* Vermelho Escuro (Firebrick) */
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #8B0000; /* Vermelho mais escuro ao passar o mouse */
        color: white;
    }
    
    /* Métricas: Fundo Transparente com Detalhe Dourado */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #FFD700; /* Linha Dourada na esquerda */
    }
    
    /* Abas Selecionadas */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM CACHE (Mantém igual) ---
@st.cache_resource
def conectar_google_sheets():
    try:
        gc = gspread.service_account(filename="credentials.json")
        KEY = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"
        sh = gc.open_by_key(KEY)
        return sh
    except Exception as e:
        return None

sh = conectar_google_sheets()

if not sh:
    st.error("❌ Erro grave de conexão com o Google Sheets.")
    st.stop()

ws_pedidos = sh.sheet1 
ws_clientes = sh.worksheet("BaseClientes")

# --- BARRA LATERAL COM LOGO ---
with st.sidebar:
    # Tenta carregar a imagem local, se não achar, usa um ícone de peixe
    try:
        st.image("imagem da empresa.jpg", use_container_width=True)
    except:
        st.warning("⚠️ Arquivo 'imagem da empresa.jpg' não encontrado na pasta.")
        st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=100)

    st.markdown("---")
    
    # Métricas Rápidas
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
st.markdown("Use as abas abaixo para navegar.")

# --- CRIAÇÃO DAS ABAS ---
tab_pedidos, tab_historico, tab_clientes = st.tabs(["📝 Novo Pedido", "📊 Histórico de Vendas", "➕ Cadastrar Clientes"])

# ==================================================
# ABA 1: NOVO PEDIDO
# ==================================================
with tab_pedidos:
    st.subheader("Lançamento de Pedido")
    
    # Carrega clientes
    try:
        lista_nomes = sorted(list(set(ws_clientes.col_values(2)[1:])))
    except:
        lista_nomes = []

    with st.form(key="form_pedido", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            if not lista_nomes:
                st.warning("⚠️ Cadastre clientes na aba 'Cadastrar Clientes'.")
                nome_cliente = st.text_input("Nome do Cliente (Avulso):")
            else:
                nome_cliente = st.selectbox("Selecione o Cliente:", options=lista_nomes)
        
        with col2:
            dia_entrega = st.date_input("Data de Entrega:", value=datetime.today())

        pedido = st.text_area("Descrição Detalhada do Pedido:", height=150, placeholder="Ex: 10 Caixas de Peças X...")
        
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
                    st.success(f"✅ Pedido para **{nome_cliente}** salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==================================================
# ABA 2: HISTÓRICO (TABELA MELHORADA)
# ==================================================
# ==================================================
# ABA 2: GERENCIAMENTO (CRUD COMPLETO)
# ==================================================
with tab_historico:
    st.subheader("Gerenciamento de Pedidos")
    st.caption("Edite os valores diretamente na tabela. Selecione linhas e aperte 'Del' para excluir.")
    
    # 1. Carregar os dados atuais
    try:
        dados = ws_pedidos.get_all_values()
    except:
        dados = []

    if len(dados) > 1:
        # Criar o DataFrame
        df = pd.DataFrame(dados[1:], columns=dados[0])
        
        # 2. O Editor Mágico (CRUD na tela)
        # num_rows="dynamic" -> Permite adicionar/remover linhas
        df_editado = st.data_editor(
            df, 
            num_rows="dynamic", 
            use_container_width=True,
            key="editor_pedidos",
            height=500
        )
        
        # 3. Botão para efetivar a mudança no Google Sheets
        if st.button("💾 Salvar Alterações na Nuvem", type="primary"):
            try:
                # A: Limpa a planilha antiga (mantém só o objeto da aba)
                ws_pedidos.clear()
                
                # B: Reconstrói a lista de dados (Cabeçalho + Conteúdo Editado)
                # df_editado.columns.tolist() -> Pega os nomes das colunas
                # df_editado.values.tolist()  -> Pega os dados das linhas
                novos_dados = [df_editado.columns.tolist()] + df_editado.values.tolist()
                
                # C: Atualiza o Google Sheets
                # Dependendo da versão do gspread, pode precisar de ws_pedidos.update(novos_dados)
                ws_pedidos.update(range_name="A1", values=novos_dados)
                
                st.success("✅ Banco de dados atualizado com sucesso!")
                st.balloons() # Um efeito visual para confirmar
                
                # Aguarda 2s e recarrega para garantir que os dados estão frescos
                import time
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")
                
    else:
        st.info("Nenhum pedido registrado ainda para editar.")

# ==================================================
# ABA 3: CADASTRO DE CLIENTES
# ==================================================
with tab_clientes:
    st.subheader("Cadastro de Novos Parceiros")
    
    with st.form(key="form_novo_cliente", clear_on_submit=True):
        c1, c2 = st.columns([2, 1]) # Coluna 1 é o dobro do tamanho da 2
        
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
                    st.success(f"✅ Cliente **{novo_nome.upper()}** cadastrado com ID {novo_id}!")
                    # Pequeno delay para recarregar os dados
                    st.toast("Atualizando lista de clientes...", icon="🔄")
                    
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {e}")
            else:
                st.warning("Preencha o nome do cliente.")