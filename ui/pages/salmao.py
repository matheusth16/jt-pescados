"""
Página de Recebimento de Salmão.
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime

import services.database as db
import ui.components as components
from ui.pages.salmao_utils import preparar_dataframe_view
from ui.pages.salmao_modals import modal_detalhes_tag, highlight_status_salmao


def _is_mobile(breakpoint: int = 768) -> bool:
    try:
        from streamlit_javascript import st_javascript  # type: ignore
        w = st_javascript("window.innerWidth")
        try:
            return int(w) < breakpoint
        except Exception:
            return False
    except Exception:
        return False


@st.fragment
def painel_tabela_interativa(df_base, perfil, range_str):
    """Fragmento que isola a tabela e seus filtros do resto da página."""
    df_view = preparar_dataframe_view(df_base)

    with st.expander("🌪️ Filtros Avançados", expanded=False):
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            cal_ops = sorted([str(x) for x in df_view["Calibre"].unique() if x])
            f_cal = st.multiselect("Calibre", cal_ops)
        with c_f2:
            forn_ops = sorted([str(x) for x in df_view["Fornecedor"].unique() if x])
            f_forn = st.multiselect("Fornecedor", forn_ops)

        if f_cal:
            df_view = df_view[df_view["Calibre"].astype(str).isin(f_cal)]
        if f_forn:
            df_view = df_view[df_view["Fornecedor"].astype(str).isin(f_forn)]

    st.markdown(f"### 📋 Tabela Geral: {range_str}")

    range_atual = st.session_state.get("range_salmao_atual")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_export = df_view.copy()
        if range_atual:
            df_backup = db.get_estoque_backup_filtrado(range_atual[0], range_atual[1])
            if not df_backup.empty:
                df_backup_view = preparar_dataframe_view(df_backup)
                df_export["Origem"] = "Atual / Livre"
                df_backup_view["Origem"] = "Histórico / Gerado"
                df_export = pd.concat([df_export, df_backup_view], ignore_index=True)
        if "Tag" in df_export.columns:
            sort_by = ["Tag", "Origem"] if "Origem" in df_export.columns else ["Tag"]
            df_export = df_export.sort_values(by=sort_by)
        df_export.to_excel(writer, index=False, sheet_name="Salmao_Completo")

    st.download_button(
        label="📥 Baixar Tabela (Com Gerados)",
        data=buffer,
        file_name=f"estoque_salmao_completo_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mime="application/vnd.ms-excel",
        type="secondary"
    )

    cfg_colunas = {
        "Tag": st.column_config.NumberColumn("Tag", format="%d", width="small"),
        "Calibre": st.column_config.TextColumn("Calibre", width="small"),
        "Status": st.column_config.TextColumn("Status", width="small"),
        "Peso": st.column_config.NumberColumn("Peso (kg)", format="%.2f", width="small"),
        "Validade": st.column_config.DateColumn("Validade", format="DD/MM/YYYY"),
        "Cliente": st.column_config.TextColumn("Cliente", width="medium"),
        "Fornecedor": st.column_config.TextColumn("Fornecedor", width="medium"),
    }

    mobile = _is_mobile()

    if not mobile:
        df_tab = df_view.copy()
        df_tab.insert(0, "VER", False)
        cfg_colunas_tab = dict(cfg_colunas)
        cfg_colunas_tab["VER"] = st.column_config.CheckboxColumn(
            "Editar" if perfil != "Admin" else "Ver",
            width="small"
        )
        df_styled = df_tab.style.map(highlight_status_salmao, subset=["Status"])

        tabela = st.data_editor(
            df_styled,
            key=f"editor_salmao_{st.session_state.salmao_editor_key}",
            use_container_width=True,
            height=500,
            hide_index=True,
            column_config=cfg_colunas_tab,
            disabled=[c for c in cfg_colunas_tab.keys() if c != "VER"],
        )

        selecionado = tabela[tabela["VER"] == True]
        if not selecionado.empty:
            dados_linha = selecionado.iloc[0].to_dict()
            val_validade = dados_linha.get("Validade")
            dados_linha["Validade"] = val_validade.strftime("%d/%m/%Y") if pd.notna(val_validade) and hasattr(val_validade, "strftime") else ""
            st.session_state.tag_para_visualizar = dados_linha
            st.session_state.salmao_editor_key += 1
            st.rerun()
    else:
        clicado = components.render_df_as_list_cards(
            df_view,
            id_col="Tag",
            title_col="Tag",
            subtitle_cols=["Status", "Calibre"],
            fields=[
                ("Peso (kg)", "Peso"),
                ("Validade", "Validade"),
                ("Cliente", "Cliente"),
                ("Fornecedor", "Fornecedor"),
            ],
            action_label="Abrir",
            action_key_prefix="tag_card",
            return_on_click=True
        )

        if clicado is not None:
            linha = df_view[df_view["Tag"].astype(str) == str(clicado)]
            if not linha.empty:
                dados_linha = linha.iloc[0].to_dict()
                val_validade = dados_linha.get("Validade")
                dados_linha["Validade"] = val_validade.strftime("%d/%m/%Y") if pd.notna(val_validade) and hasattr(val_validade, "strftime") else str(val_validade or "")
                st.session_state.tag_para_visualizar = dados_linha
                st.session_state.salmao_editor_key += 1
                st.rerun()


def render_page(hash_dados, perfil, nome_user):
    if "salmao_editor_key" not in st.session_state:
        st.session_state.salmao_editor_key = 0
    if "tag_para_visualizar" not in st.session_state:
        st.session_state.tag_para_visualizar = None
    if "range_salmao_atual" not in st.session_state:
        st.session_state.range_salmao_atual = None
    if "salmao_df" not in st.session_state:
        st.session_state.salmao_df = pd.DataFrame()
    if "salmao_range_str" not in st.session_state:
        st.session_state.salmao_range_str = None

    st.subheader("🐟 Recebimento de Salmão")

    qtd_total, qtd_livre, qtd_gerado, qtd_orc, qtd_reservado, qtd_aberto = db.get_resumo_global_salmao()

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        components.render_metric_card("📦 Total", qtd_total, "#8b949e")
    with m2:
        components.render_metric_card("✅ Livre", qtd_livre, "#11734b")
    with m3:
        components.render_metric_card("✂️ Aberto", qtd_aberto, "#473822")
    with m4:
        components.render_metric_card("⚙️ Gerado", qtd_gerado, "#ff8500")
    with m5:
        components.render_metric_card("📝 Orçamento", qtd_orc, "#e8eaed")
    with m6:
        components.render_metric_card("🔵 Reservado", qtd_reservado, "#0a53a8")

    st.markdown("---")
    msg_acao = "Ver Detalhes" if perfil == "Admin" else "Editar ou Fracionar"
    st.info(f"👆 Clique para **{msg_acao}**.")

    with st.container(border=True):
        c_in, c_fim, c_btn = st.columns([1, 1, 2], vertical_alignment="bottom")
        with c_in:
            tag_start = st.number_input("Tag Inicial", min_value=1, value=1, step=1)
        with c_fim:
            tag_end = st.number_input("Tag Final", min_value=1, value=200, step=1)
        with c_btn:
            carregar = st.button("🔍 Carregar Intervalo", type="primary", use_container_width=True)

    if carregar:
        qtd = tag_end - tag_start + 1
        if qtd > 200:
            st.error("Limite de 200 tags.")
        elif tag_end < tag_start:
            st.error("Erro no Intervalo.")
        else:
            with st.spinner("Buscando..."):
                st.session_state.salmao_df = db.get_estoque_filtrado(tag_start, tag_end)
                st.session_state.salmao_range_str = f"Tags {tag_start} a {tag_end}"
                st.session_state.range_salmao_atual = (tag_start, tag_end)

    if not st.session_state.salmao_df.empty:
        painel_tabela_interativa(
            st.session_state.salmao_df,
            perfil,
            st.session_state.salmao_range_str
        )

        if st.session_state.tag_para_visualizar is not None:
            modal_detalhes_tag(
                st.session_state.tag_para_visualizar,
                perfil,
                nome_user,
                st.session_state.range_salmao_atual
            )
    else:
        if st.session_state.get("salmao_range_str"):
            st.warning("Nenhum dado encontrado.")
