import streamlit as st
import time
from datetime import datetime
import pandas as pd

# Backend
import services.database as db
import ui.styles as styles

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Sistema JT Pescados",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

styles.aplicar_estilos()

# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    try:
        st.image("assets/imagem da empresa.jpg", use_container_width=True)
    except:
        st.image(
            "https://cdn-icons-png.flaticon.com/512/3063/3063822.png",
            width=100
        )

    st.markdown("---")

    total_clientes, total_pedidos = db.get_metricas()

    c1, c2 = st.columns(2)
    c1.metric("Clientes", total_clientes)
    c2.metric("Pedidos", total_pedidos)

    st.markdown("---")
    st.info("Sistema de Gestão\n**JT Pescados**")

# ==============================
# CORPO PRINCIPAL
# ==============================
st.title("📦 Gestão de Pedidos")

tab_pedidos, tab_gerenciar, tab_clientes = st.tabs(
    ["📝 Novo Pedido", "📊 Gerenciar Pedidos", "➕ Cadastrar Clientes"]
)

# ==============================
# ABA 1 — NOVO PEDIDO
# ==============================
with tab_pedidos:
    st.subheader("Lançamento de Pedido")

    lista_clientes = db.listar_clientes()

    STATUS_OPCOES = [
        "Selecione…",
        "PENDENTE",
        "GERADO",
        "NÃO GERADO",
        "CANCELADO",
        "ENTREGUE",
        "ORÇAMENTO",
        "RESERVADO",
    ]

    with st.form("form_pedido", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            if lista_clientes:
                nome_cliente = st.selectbox(
                    "Cliente",
                    options=["Selecione…"] + lista_clientes
                )
            else:
                nome_cliente = st.text_input("Nome do Cliente")

        with col2:
            data_entrega = st.date_input(
                "Data de Entrega",
                value=datetime.today()
            )

        descricao = st.text_area(
            "Descrição do Pedido",
            height=150
        )

        status = st.selectbox(
            "Status do Pedido",
            options=STATUS_OPCOES,
            index=0
        )

        salvar = st.form_submit_button("💾 Salvar Pedido")

        if salvar:
            erros = []

            if not nome_cliente or nome_cliente == "Selecione…":
                erros.append("Selecione um cliente.")

            if not descricao.strip():
                erros.append("Preencha a descrição do pedido.")

            if status == "Selecione…":
                erros.append("Selecione um status.")

            if erros:
                for e in erros:
                    st.warning(e)
            else:
                try:
                    db.salvar_pedido(
                        nome_cliente,
                        descricao,
                        data_entrega,
                        status
                    )
                    st.success("✅ Pedido salvo com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar pedido: {e}")

# ==============================
# ABA 2 — GERENCIAR PEDIDOS
# ==============================
with tab_gerenciar:
    st.subheader("Pedidos Cadastrados")

    df = db.buscar_todos_pedidos()

    if df.empty:
        st.info("Nenhum pedido encontrado.")
    else:
        # Garante que STATUS não seja editável no sistema
        colunas_bloqueadas = ["STATUS"] if "STATUS" in df.columns else []

        df_visual = st.data_editor(
            df,
            disabled=colunas_bloqueadas,
            use_container_width=True,
            height=500,
            hide_index=True
        )

        st.caption(
            "ℹ️ O status deve ser alterado diretamente no Google Sheets."
        )

# ==============================
# ABA 3 — CLIENTES
# ==============================
with tab_clientes:
    st.subheader("Cadastro de Clientes")

    with st.form("form_cliente", clear_on_submit=True):
        c1, c2 = st.columns([2, 1])

        with c1:
            novo_nome = st.text_input("Nome do Cliente / Empresa")

        with c2:
            nova_cidade = st.text_input("Cidade", value="SÃO CARLOS")

        salvar_cliente = st.form_submit_button("Salvar Cliente")

        if salvar_cliente:
            if not novo_nome.strip():
                st.warning("Informe o nome do cliente.")
            else:
                try:
                    db.criar_novo_cliente(novo_nome, nova_cidade)
                    st.success("✅ Cliente cadastrado!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar cliente: {e}")
