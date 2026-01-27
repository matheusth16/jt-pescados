import streamlit as st
import pandas as pd
import time
from datetime import datetime
import services.database as db
import ui.components as components
from core.config import PALETA_CORES
from services.utils import calcular_status_validade

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
            elif peso_unidade > saldo_disponivel + 0.001: 
                st.error(f"⛔ Peso indisponível! Você tentou {peso_unidade}kg, mas só restam {saldo_disponivel:.3f}kg.")
            else:
                # Prepara tabela para salvamento seguro (convertendo datas se necessário)
                if df_tabela_atual is not None and not df_tabela_atual.empty:
                    df_safe = df_tabela_atual.copy()
                    if "Validade" in df_safe.columns:
                        df_safe["Validade"] = df_safe["Validade"].apply(
                            lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) and not isinstance(x, str) else x
                        )
                    db.salvar_alteracoes_estoque(df_safe, usuario_nome)

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
    
    # --- MÉTRICAS GLOBAIS DE ESTOQUE ---
    qtd_total, qtd_livre, qtd_gerado, qtd_orc, qtd_reservado = db.get_resumo_global_salmao()
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1: components.render_metric_card("📦 Total Tags", qtd_total, "#8b949e")
    with m2: components.render_metric_card("✅ Livre", qtd_livre, "#28a745")
    with m3: components.render_metric_card("⚙️ Gerado", qtd_gerado, "#ff8500")
    with m4: components.render_metric_card("📝 Orçamento", qtd_orc, "#e8eaed")
    with m5: components.render_metric_card("🔵 Reservado", qtd_reservado, "#0a53a8")

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
        
        df_view = st.session_state.salmao_df.copy() # Trabalha numa cópia para filtros
        
        # --- CONVERSÃO PARA DATE PICKER ---
        if "Validade" in df_view.columns:
            df_view["Validade"] = pd.to_datetime(df_view["Validade"], format="%d/%m/%Y", errors="coerce")

        # ==========================================================
        # 🌪️ FILTROS AVANÇADOS (NOVO)
        # ==========================================================
        with st.expander("🌪️ Filtros Avançados (Calibre / Fornecedor)", expanded=False):
            c_fil1, c_fil2 = st.columns(2)
            
            with c_fil1:
                # Pega opções únicas do DF atual
                opcoes_calibre = sorted([str(x) for x in df_view["Calibre"].unique() if str(x) != "nan" and str(x) != ""])
                filtro_calibre = st.multiselect("Filtrar por Calibre:", options=opcoes_calibre)
            
            with c_fil2:
                # Verifica se existe coluna Fornecedor antes de tentar filtrar
                opcoes_forn = []
                if "Fornecedor" in df_view.columns:
                    opcoes_forn = sorted([str(x) for x in df_view["Fornecedor"].unique() if str(x) != "nan" and str(x) != ""])
                filtro_fornecedor = st.multiselect("Filtrar por Fornecedor:", options=opcoes_forn)

            # APLICAÇÃO DOS FILTROS
            if filtro_calibre:
                df_view = df_view[df_view["Calibre"].astype(str).isin(filtro_calibre)]
            
            if filtro_fornecedor and "Fornecedor" in df_view.columns:
                df_view = df_view[df_view["Fornecedor"].astype(str).isin(filtro_fornecedor)]

        # ==========================================================
        
        container_pendencias = st.container()
        st.markdown("---")
        st.markdown(f"### 📋 Tabela Geral: {st.session_state.salmao_range_str}")
        
        # Configuração das Colunas (Adicionado Fornecedor)
        cfg_colunas = {
            "Tag": st.column_config.NumberColumn("Tag", disabled=True, format="%d"),
            "Calibre": st.column_config.SelectboxColumn("Calibre", options=["8/10", "10/12", "12/14", "14/16"]),
            "Status": st.column_config.SelectboxColumn("Status", options=["Livre", "Reservado", "Orçamento", "Gerado", "Aberto"]),
            "Peso": st.column_config.NumberColumn("Peso (kg)", format="%.2f"),
            "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
            "Cliente": st.column_config.TextColumn("Cliente Destino"),
            "Fornecedor": st.column_config.TextColumn("Fornecedor") # <--- ADICIONADO
        }

        # Função auxiliar para estilo
        def estilizar_validade(val):
            val_str = ""
            if pd.notnull(val):
                if isinstance(val, (pd.Timestamp, datetime)):
                    val_str = val.strftime("%d/%m/%Y")
                else:
                    val_str = str(val)
            
            status = calcular_status_validade(val_str)
            cor = PALETA_CORES["VALIDADE"].get(status, "")
            return f'background-color: {cor}' if cor else ''

        if perfil == "Admin":
            df_estilizado = df_view.style.map(estilizar_validade, subset=['Validade'])
            st.dataframe(df_estilizado, use_container_width=True, height=400, hide_index=True, column_config=cfg_colunas)
            tabela_editada = df_view 
        else:
            # Lógica de Alertas
            itens_criticos = 0
            itens_alerta = 0
            for val in df_view['Validade']:
                val_str = val.strftime("%d/%m/%Y") if pd.notnull(val) else ""
                s = calcular_status_validade(val_str)
                if s == "CRITICO": itens_criticos += 1
                if s == "ALERTA": itens_alerta += 1

            if itens_criticos > 0 or itens_alerta > 0:
                st.warning(f"⚠️ Atenção: {itens_criticos} Lotes Críticos e {itens_alerta} em Alerta!")

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
                    # --- CONVERSÃO INVERSA ---
                    tabela_salvar = tabela_editada.copy()
                    tabela_salvar["Validade"] = tabela_salvar["Validade"].apply(
                        lambda x: x.strftime("%d/%m/%Y") if pd.notnull(x) else ""
                    )
                    
                    n = db.salvar_alteracoes_estoque(tabela_salvar, nome_user)
                    if n > 0:
                        st.success(f"✅ {n} linhas atualizadas!")
                        # Atualiza a sessão original (sem filtros) com os novos dados
                        # Idealmente, recarregaríamos do banco, mas para ser rápido, atualizamos o que foi editado
                        st.session_state.salmao_df = tabela_editada 
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.info("Nada para salvar.")

        # PAINEL DE PENDÊNCIAS (Considera apenas o filtrado ou o total?
        # Aqui usamos tabela_editada, ou seja, se filtrou, só vê pendências do filtro. O que faz sentido.)
        with container_pendencias:
            if not tabela_editada.empty and "Status" in tabela_editada.columns:
                df_abertos = tabela_editada[tabela_editada["Status"].astype(str).str.upper() == "ABERTO"]
                
                if not df_abertos.empty:
                    st.warning("🔥 **Tags Abertas (Prioridade)**")
                    for idx, row in df_abertos.iterrows():
                        with st.container(border=True):
                            c_tag, c_peso, c_cli, c_btn = st.columns([1, 1.5, 2, 2], vertical_alignment="center")
                            with c_tag: st.markdown(f"### 🏷️ {row['Tag']}")
                            with c_peso: 
                                st.markdown(f"**{row['Peso']} kg**")
                                st.caption(row['Calibre'])
                            with c_cli:
                                st.write(f"👤 {row['Cliente']}" if row['Cliente'] else "Sem cliente")
                            with c_btn:
                                if st.button(f"✂️ Desmembrar", key=f"top_cut_{row['Tag']}", type="primary", use_container_width=True):
                                    modal_desmembramento(row['Tag'], row['Peso'], nome_user, tabela_editada)
    else:
        if st.session_state.get("salmao_range_str"):
            st.warning("Nenhum dado encontrado.")