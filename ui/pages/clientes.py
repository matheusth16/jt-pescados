import streamlit as st
import time
import services.database as db
import ui.components as components

def render_page(hash_dados, perfil):
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
                        st.success(f"✅ {nn} cadastrado com sucesso!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        components.render_error_details("Erro ao criar cliente.", e)

    st.markdown("---")
    st.markdown("### 🔍 Clientes já Cadastrados")
    
    # Recriando busca de clientes para tabela
    try:
        conn = db.get_connection()
        ws = conn.worksheet("BaseClientes")
        import pandas as pd
        data = ws.get_all_records()
        df_clientes_view = pd.DataFrame(data)
    except:
        df_clientes_view = pd.DataFrame()
    
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