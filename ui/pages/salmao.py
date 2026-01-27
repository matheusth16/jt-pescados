import streamlit as st
import pandas as pd
import time
import services.database as db
import ui.components as components

# --- MODAL LOCAL ---
@st.dialog("✂️ Desmembrar Tag (Fracionamento)")
def modal_desmembramento(tag_id, peso_atual, usuario_nome):
    st.caption(f"Adicione uma nova unidade para a Tag {tag_id}.")
    
    letra, peso_unidade, cliente, status = components.render_split_form(tag_id, peso_atual)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar Unidade", type="primary", use_container_width=True):
            if not letra or not cliente:
                st.warning("Preencha Letra e Cliente.")
            elif peso_unidade <= 0:
                st.warning("O peso deve ser maior que zero.")
            else:
                sucesso = db.registrar_subtag(
                    tag_id, letra, cliente, peso_unidade, status, usuario_nome
                )
                if sucesso:
                    st.success(f"✅ Unidade {letra} criada!")
                    time.sleep(1)
                    st.rerun()
    
    with c2:
        if st.button("Fechar Janela", use_container_width=True):
            st.rerun()

def render_page(nome_user, perfil):
    st.subheader("🐟 Recebimento de Salmão")
    st.info("ℹ️ Mude o Status na tabela para **'Aberto'** e ele aparecerá no topo para corte.")

    # --- PAINEL DE COMANDO ---
    with st.container(border=True):
        c_in, c_fim, c_btn = st.columns([1, 1, 2], vertical_alignment="bottom")
        
        with c_in:
            tag_start = st.number_input("Tag Inicial", min_value=1, value=1, step=1)
        with c_fim:
            tag_end = st.number_input("Tag Final", min_value=1, value=50, step=1)
        
        with c_btn:
            carregar = st.button("🔍 Carregar Intervalo", type="primary", use_container_width=True)

    # --- LÓGICA DE CARREGAMENTO ---
    if carregar:
        qtd_solicitada = tag_end - tag_start + 1
        if qtd_solicitada > 50:
            st.error(f"⚠️ Limite de 50 tags por vez.")
            st.session_state.salmao_df = pd.DataFrame()
        elif tag_end < tag_start:
            st.error("Erro: Tag Final menor que Inicial.")
        else:
            with st.spinner(f"Buscando Tags..."):
                st.session_state.salmao_df = db.get_estoque_filtrado(tag_start, tag_end)
                st.session_state.salmao_range_str = f"Tags {tag_start} a {tag_end}"

    # --- VISUALIZAÇÃO PRINCIPAL ---
    if not st.session_state.salmao_df.empty:
        
        # 1. RESERVA O ESPAÇO NO TOPO (Para as Tags Abertas)
        # O Streamlit vai desenhar isso aqui primeiro, mesmo que a gente preencha os dados só no final do script.
        container_pendencias = st.container()
        
        st.markdown("---") # Separador visual

        # 2. TABELA GERAL (Fica abaixo)
        st.markdown(f"### 📋 Tabela Geral: {st.session_state.salmao_range_str}")
        
        df_view = st.session_state.salmao_df
        
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
            key="editor_salmao_visual",
            use_container_width=True,
            height=400,
            hide_index=True,
            column_config=cfg_colunas,
            disabled=["Tag"] if perfil != "Admin" else []
        )
        
        # Botão de Salvar (Abaixo da tabela)
        if st.button("💾 Salvar Alterações da Tabela", type="secondary", use_container_width=True):
            with st.spinner("Gravando..."):
                n = db.salvar_alteracoes_estoque(tabela_editada, nome_user)
                if n > 0:
                    st.success(f"✅ {n} linhas atualizadas!")
                    st.session_state.salmao_df = tabela_editada
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("Nada para salvar.")

        # 3. PREENCHE O PAINEL DE PENDÊNCIAS (NO TOPO) USANDO OS DADOS DA TABELA
        # Agora usamos a variável 'tabela_editada' para saber o que mudou em tempo real
        with container_pendencias:
            if not tabela_editada.empty and "Status" in tabela_editada.columns:
                df_abertos = tabela_editada[tabela_editada["Status"].astype(str).str.upper() == "ABERTO"]
                
                if not df_abertos.empty:
                    st.warning("🔥 **Tags Abertas (Prioridade)**") # Destaque visual
                    
                    # Cria colunas para organizar os cards lado a lado se houver muitos (opcional, aqui mantive lista vertical limpa)
                    for idx, row in df_abertos.iterrows():
                        with st.container(border=True):
                            # Layout do Card
                            c_tag, c_peso, c_cli, c_btn = st.columns([1, 1.5, 2, 2], vertical_alignment="center")
                            
                            with c_tag:
                                st.markdown(f"### 🏷️ {row['Tag']}")
                            with c_peso:
                                st.markdown(f"**{row['Peso']} kg**")
                                st.caption(row['Calibre'])
                            with c_cli:
                                if row['Cliente']:
                                    st.write(f"👤 {row['Cliente']}")
                                else:
                                    st.caption("Sem cliente definido")
                            with c_btn:
                                if st.button(f"✂️ Desmembrar", key=f"top_cut_{row['Tag']}", type="primary", use_container_width=True):
                                    modal_desmembramento(row['Tag'], row['Peso'], nome_user)
                else:
                    # Se não tiver nada aberto, podemos deixar vazio ou mostrar uma mensagem sutil
                    pass 

    else:
        if st.session_state.salmao_range_str:
            st.warning("Nenhum dado encontrado.")