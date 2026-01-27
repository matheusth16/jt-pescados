import streamlit as st
import pandas as pd
import time
import services.database as db
import ui.components as components

# --- MODAL LOCAL ---
@st.dialog("✂️ Desmembrar Tag (Fracionamento)")
def modal_desmembramento(tag_id, peso_atual, usuario_nome, df_tabela_atual):
    st.caption(f"Adicione uma nova unidade para a Tag {tag_id}.")
    st.markdown(f"**Peso Original:** {peso_atual} kg")
    
    # 1. Busca dados do banco para validação
    letras_usadas, peso_ja_consumido = db.get_consumo_tag(tag_id)
    saldo_disponivel = peso_atual - peso_ja_consumido
    
    # Mostra um resumo do saldo para o operador
    if saldo_disponivel < 0: saldo_disponivel = 0.0
    st.info(f"⚖️ **Saldo Disponível:** {saldo_disponivel:.3f} kg (Já usado: {peso_ja_consumido:.3f} kg)")

    # 2. Renderiza o formulário
    letra, peso_unidade, cliente, status = components.render_split_form(tag_id, peso_atual)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Confirmar Unidade", type="primary", use_container_width=True):
            letra_limpa = str(letra).strip().upper()
            
            # --- VALIDAÇÕES ---
            if not letra or not cliente:
                st.warning("⚠️ Preencha Letra e Cliente.")
            elif peso_unidade <= 0:
                st.warning("⚠️ O peso deve ser maior que zero.")
            elif letra_limpa in letras_usadas:
                st.error(f"⛔ A letra '{letra_limpa}' já existe nesta Tag! Use outra.")
            elif peso_unidade > saldo_disponivel + 0.001: # +0.001 para tolerância de arredondamento
                st.error(f"⛔ Peso indisponível! Você tentou {peso_unidade}kg, mas só restam {saldo_disponivel:.3f}kg.")
            else:
                # --- AUTO-SAVE DA TABELA GERAL (SEGURANÇA) ---
                # Salva o status "Aberto" ou outras edições pendentes antes de criar a subtag
                if df_tabela_atual is not None and not df_tabela_atual.empty:
                    db.salvar_alteracoes_estoque(df_tabela_atual, usuario_nome)

                # --- GRAVAÇÃO DA SUBTAG ---
                sucesso = db.registrar_subtag(
                    tag_id, letra_limpa, cliente, peso_unidade, status, usuario_nome
                )
                if sucesso:
                    st.success(f"✅ Unidade {letra_limpa} criada e Tabela atualizada!")
                    time.sleep(1)
                    st.rerun()
    
    with c2:
        if st.button("Fechar Janela", use_container_width=True):
            st.rerun()

def render_page(nome_user, perfil):
    st.subheader("🐟 Recebimento de Salmão")
    
    # --- MÉTRICAS GLOBAIS DE ESTOQUE (NOVO) ---
    # Busca os totais de TODA a planilha
    qtd_total, qtd_livre, qtd_gerado, qtd_orc, qtd_reservado = db.get_resumo_global_salmao()
    
    # Exibe os cards no topo
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: components.render_metric_card("📦 Total Tags", qtd_total, "#8b949e") # Cinza
    with m2: components.render_metric_card("✅ Livre", qtd_livre, "#28a745")      # Verde
    with m3: components.render_metric_card("⚙️ Gerado", qtd_gerado, "#ff8500")    # Laranja
    with m4: components.render_metric_card("📝 Orçamento", qtd_orc, "#e8eaed")    # Cinza Claro
    with m5: components.render_metric_card("🔵 Reservado", qtd_reservado, "#0a53a8") # Azul

    st.markdown("---")
    
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
        container_pendencias = st.container()
        
        st.markdown("---") # Separador visual

        # 2. TABELA GERAL
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

        # --- LÓGICA DIFERENCIADA POR PERFIL ---
        if perfil == "Admin":
            # Admin: Somente Leitura (st.dataframe)
            st.dataframe(
                df_view,
                use_container_width=True,
                height=400,
                hide_index=True,
                column_config=cfg_colunas
            )
            tabela_editada = df_view 
        else:
            # Operador: Edição (st.data_editor)
            tabela_editada = st.data_editor(
                df_view,
                key="editor_salmao_visual",
                use_container_width=True,
                height=400,
                hide_index=True,
                column_config=cfg_colunas,
                disabled=["Tag"]
            )
            
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

        # 3. PAINEL DE PENDÊNCIAS (TOPO)
        with container_pendencias:
            if not tabela_editada.empty and "Status" in tabela_editada.columns:
                df_abertos = tabela_editada[tabela_editada["Status"].astype(str).str.upper() == "ABERTO"]
                
                if not df_abertos.empty:
                    st.warning("🔥 **Tags Abertas (Prioridade)**")
                    
                    for idx, row in df_abertos.iterrows():
                        with st.container(border=True):
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
                                # Botão Desmembrar disponível para todos (Admin e Operador)
                                # Passamos a 'tabela_editada' inteira para a função salvar automaticamente
                                if st.button(f"✂️ Desmembrar", key=f"top_cut_{row['Tag']}", type="primary", use_container_width=True):
                                    modal_desmembramento(row['Tag'], row['Peso'], nome_user, tabela_editada)
    else:
        if st.session_state.salmao_range_str:
            st.warning("Nenhum dado encontrado.")