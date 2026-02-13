import streamlit as st
import time
import math
import io
import pandas as pd

import services.database as db
import ui.components as components
from datetime import datetime
from core.config import LISTA_STATUS, LISTA_PAGAMENTO, PALETA_CORES


# --- FUNÇÃO AUXILIAR DE ESTILO (FORMATAÇÃO CONDICIONAL) ---
def highlight_status(val):
    val_limpo = str(val).strip()
    cor = PALETA_CORES["STATUS"].get(val_limpo, None)
    if cor:
        return f'background-color: {cor}; color: black; font-weight: 600;'
    return ''


def _tentar_navegar_para_edicao():
    """
    Tenta navegar para a página de edição.
    - Se você usa Streamlit multipage padrão, st.switch_page deve funcionar.
    - Se você usa roteador próprio no app.py, cai no fallback via session_state.
    """
    # ✅ Tentativa 1: Streamlit multipage
    try:
        # Ajuste o caminho se a sua estrutura for diferente.
        # Se sua página estiver em "pages/gerenciar_edicao.py", use exatamente isso.
        st.switch_page("ui/pages/gerenciar_edicao.py")
        return
    except Exception:
        pass

    # ✅ Fallback: para apps com roteamento manual (app.py lê essa chave)
    st.session_state["nav_page"] = "gerenciar_edicao"
    st.rerun()


# --- COMPONENTE: MODAL DE DETALHES (LEITURA) ---
@st.dialog("📦 Detalhes do Pedido")
def mostrar_detalhes_pedido(row, perfil, nome_user):
    # Padroniza chaves para evitar diferença de maiúsculas
    row = {str(k).upper().strip(): v for k, v in dict(row).items()}

    st.markdown(f"### 🆔 Pedido #{row.get('ID_PEDIDO', '')}")

    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown(f"**👤 Cliente:** {row.get('NOME CLIENTE', '')}")
        st.caption(f"Cód: {row.get('COD CLIENTE', '-')}")
    with c2:
        st.markdown(f"**📍 Cidade:** {row.get('CIDADE', '')}")
        st.caption(f"Rota: {row.get('ROTA', '-')}")

    st.markdown("---")
    st.warning("📝 **ITENS DO PEDIDO:**")
    st.markdown(f"#### {row.get('PEDIDO', 'Sem itens descritos')}")
    st.markdown("---")

    l1, l2 = st.columns(2)
    with l1:
        st.markdown("**📅 Entrega:**")
        st.write(row.get('DIA DA ENTREGA', '-'))
    with l2:
        st.markdown("**🚚 Rota:**")
        st.write(row.get('ROTA', '-'))

    st.markdown("---")

    val_status_atual = row.get('STATUS', '-')
    val_pagamento_atual = row.get('PAGAMENTO', '-')
    val_nr_atual = row.get('NR PEDIDO', '')
    val_obs_atual = row.get('OBSERVAÇÃO', '')

    if pd.isna(val_nr_atual): val_nr_atual = ""
    if pd.isna(val_obs_atual): val_obs_atual = ""

    # Bloco leitura (Admin e OP)
    c_read1, c_read2 = st.columns(2)
    with c_read1:
        st.markdown("**📊 Status:**")
        cor = PALETA_CORES["STATUS"].get(str(val_status_atual).strip(), "#8b949e")
        st.markdown(
            f"<span style='color:{cor}; font-weight:bold; font-size:1.1em'>{val_status_atual}</span>",
            unsafe_allow_html=True
        )
    with c_read2:
        st.markdown("**💳 Pagamento:**")
        st.write(val_pagamento_atual)

    st.markdown("<br>", unsafe_allow_html=True)
    if val_nr_atual:
        st.info(f"🔢 **NR:** {val_nr_atual}")
    else:
        st.info("🔢 **NR:** (vazio)")

    if val_obs_atual:
        st.info(f"👀 **Obs:** {val_obs_atual}")
    else:
        st.info("👀 **Obs:** (vazio)")

    st.markdown("---")

    # Ação extra para OP: ir para edição (em página separada)
    if perfil != "Admin":
        st.caption("✏️ OP pode editar: Status, Pagamento, NR Pedido (apenas se estiver vazio) e Observação.")
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("✏️ Ir para Edição", type="primary", use_container_width=True):
                # Salva o pedido em session_state para a página gerenciar_edicao.py usar
                st.session_state["pedido_para_visualizar"] = row
                st.session_state["pedido_id_edicao"] = row.get("ID_PEDIDO", "")
                _tentar_navegar_para_edicao()
        with c_btn2:
            if st.button("Fechar", use_container_width=True):
                st.rerun()
    else:
        if st.button("Fechar", use_container_width=True):
            st.rerun()


# --- NOVO: FRAGMENTO DA TABELA DE GESTÃO ---
@st.fragment
def tabela_gestao_interativa(perfil, nome_user):
    """
    Isola a tabela, filtros e paginação.
    Interagir aqui NÃO recarrega o restante da página (cabeçalho, menu, etc).
    """
    # 1. PREPARAÇÃO DOS FILTROS
    opts_cid, opts_rota = db.listar_dados_filtros()

    with st.expander("🔍 Filtros de Busca (Processamento no Servidor)", expanded=True):
        c_f1, c_f2, c_f3, c_f4 = st.columns(4)
        with c_f1:
            f_status = st.multiselect("Status:", LISTA_STATUS)
        with c_f2:
            f_data = st.date_input("Período (Filtro Local):", value=[], format="DD/MM/YYYY")
        with c_f3:
            f_cidade = st.multiselect("Cidade:", opts_cid)
        with c_f4:
            f_rota = st.multiselect("Rota:", opts_rota)

    filtros_db = {}
    if f_status: filtros_db["status"] = f_status
    if f_cidade: filtros_db["cidade"] = f_cidade
    if f_rota: filtros_db["rota"] = f_rota

    # 2. BUSCA PAGINADA
    TAMANHO_PAGINA = 20
    df_gestao, total_registros = db.buscar_pedidos_paginado(
        pagina_atual=st.session_state["pag_atual_gerenciar"],
        tamanho_pagina=TAMANHO_PAGINA,
        filtros=filtros_db
    )

    total_paginas = math.ceil(total_registros / TAMANHO_PAGINA) if TAMANHO_PAGINA > 0 else 1

    if not df_gestao.empty:
        df_gestao.columns = [c.upper().strip() for c in df_gestao.columns]

        # 3. FILTRO DE DATA (LOCAL)
        df_display = df_gestao.copy()
        col_dt_display = next((c for c in df_display.columns if "ENTREGA" in c), None)

        if f_data and col_dt_display and len(f_data) == 2:
            ini, fim = f_data
            dts = pd.to_datetime(df_display[col_dt_display], dayfirst=True, errors='coerce').dt.date
            df_display = df_display[(dts >= ini) & (dts <= fim)]

        # 4. EXPORTAÇÃO
        with st.container():
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_display.to_excel(writer, index=False, sheet_name='Pedidos')

            st.download_button(
                label="📥 Baixar Tabela em Excel",
                data=buffer,
                file_name=f"pedidos_jt_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
                mime="application/vnd.ms-excel",
                type="secondary"
            )

        # 5. TABELA INTERATIVA
        cfg_visual = {
            "ID_PEDIDO": st.column_config.NumberColumn("🆔 ID", format="%d", width="small"),
            "COD CLIENTE": st.column_config.NumberColumn("🔢 Cód.", format="%d", width="small"),
            "NOME CLIENTE": st.column_config.TextColumn("👤 Cliente", width="medium"),
            "CIDADE": st.column_config.TextColumn("📍 Cidade", width="small"),
            "ROTA": st.column_config.TextColumn("🚚 Rota", width="small"),
            "PEDIDO": st.column_config.TextColumn("📝 Itens", width="medium"),
            "DIA DA ENTREGA": st.column_config.TextColumn("📅 Entrega"),
            "STATUS": st.column_config.TextColumn("📊 Status", width="medium"),
            "PAGAMENTO": st.column_config.TextColumn("💳 Pagamento", width="medium"),
            "NR PEDIDO": st.column_config.TextColumn("🔢 NR", width="small"),
            "OBSERVAÇÃO": st.column_config.TextColumn("📝 Obs", width="medium"),
            "CARIMBO DE DATA/HORA": None, "VERSÃO": None, "VERSAO": None
        }

        colunas_travadas = list(cfg_visual.keys())

        # Coluna de seleção
        df_display.insert(0, "VER", False)
        cfg_visual["VER"] = st.column_config.CheckboxColumn(
            "🔍 Ver" if perfil == "Admin" else "🔍 Ver",
            width="small"
        )

        df_styled = df_display.style.map(highlight_status, subset=["STATUS"])

        if perfil == "Admin":
            st.info("👆 Clique na caixa da primeira coluna para **Ver Detalhes**.")
        else:
            st.info("👆 Clique na caixa da primeira coluna para **Ver Detalhes** e depois **Ir para Edição**.")

        df_editado = st.data_editor(
            df_styled,
            column_config=cfg_visual,
            use_container_width=True,
            height=600,
            hide_index=True,
            disabled=colunas_travadas,
            key=f"editor_geral_{st.session_state.gerenciar_editor_key}"
        )

        # Lógica de Seleção (Força Rerun GLOBAL para abrir Modal)
        linhas_selecionadas = df_editado[df_editado["VER"] == True]
        if not linhas_selecionadas.empty:
            st.session_state.pedido_para_visualizar = linhas_selecionadas.iloc[0].to_dict()
            st.session_state.gerenciar_editor_key += 1
            st.rerun()

        # Paginação dentro do fragmento
        if total_paginas > 1:
            st.markdown("---")
            nova_pagina = components.render_pagination(st.session_state["pag_atual_gerenciar"], total_paginas)
            if nova_pagina != st.session_state["pag_atual_gerenciar"]:
                st.session_state["pag_atual_gerenciar"] = nova_pagina
                st.rerun()

    else:
        st.info("Nenhum pedido encontrado com os filtros selecionados.")


def render_page(hash_dados, perfil, nome_user):
    if "gerenciar_editor_key" not in st.session_state:
        st.session_state.gerenciar_editor_key = 0
    if "pedido_para_visualizar" not in st.session_state:
        st.session_state.pedido_para_visualizar = None
    if "pag_atual_gerenciar" not in st.session_state:
        st.session_state["pag_atual_gerenciar"] = 1

    titulo = "👁️ Visão Geral" if perfil == "Admin" else "🚚 Painel de Operações"
    st.subheader(titulo)

    # CHAMADA DO FRAGMENTO ISOLADO
    tabela_gestao_interativa(perfil, nome_user)

    # MODAL (Fora do fragmento para garantir contexto correto de sobreposição)
    if st.session_state.pedido_para_visualizar is not None:
        pedido_visto = st.session_state.pedido_para_visualizar
        st.session_state.pedido_para_visualizar = None
        mostrar_detalhes_pedido(pedido_visto, perfil, nome_user)
