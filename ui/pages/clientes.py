import streamlit as st
import time
import math
import services.database as db
import ui.components as components
from ui.plotly_theme import aplicar_tema_plotly


def _is_mobile(breakpoint: int = 768) -> bool:
    """
    Detecta mobile via JS (largura de tela).
    - Requer: pip install streamlit-javascript
    - Fallback: se não estiver instalado, assume desktop (tabela).
    """
    try:
        from streamlit_javascript import st_javascript  # type: ignore
        w = st_javascript("window.innerWidth")
        try:
            return int(w) < breakpoint
        except Exception:
            return False
    except Exception:
        return False


def render_page(hash_dados, perfil):
    st.subheader("➕ Gestão de Clientes")

    # --- FORMULÁRIO DE CADASTRO (MANTIDO IGUAL) ---
    with st.container(border=True):
        with st.form("cad_cli", clear_on_submit=True):
            nn = st.text_input("Nome do Cliente / Empresa", placeholder="Razão Social ou Nome Fantasia")
            c1, c2 = st.columns(2)
            with c1:
                cc = st.text_input("Cidade", value="SÃO CARLOS")
            with c2:
                doc_raw = st.text_input("CPF/CNPJ", placeholder="Digite apenas os números")

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

    lista_clientes_fragment()


@st.fragment
def lista_clientes_fragment():
    """
    Lista paginada de clientes. Interações (paginação, Voltar) reexecutam só este bloco.
    """
    if "pag_atual_clientes" not in st.session_state:
        st.session_state["pag_atual_clientes"] = 1

    TAMANHO_PAGINA = 20
    df_clientes_view, total_registros = db.buscar_clientes_paginado(
        st.session_state["pag_atual_clientes"],
        TAMANHO_PAGINA
    )
    total_paginas = math.ceil(total_registros / TAMANHO_PAGINA) if TAMANHO_PAGINA > 0 else 1

    if not df_clientes_view.empty:
        st.caption(f"Total de registros na base: **{total_registros}**")
        mobile = _is_mobile()

        if not mobile:
            st.dataframe(
                df_clientes_view,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Código": st.column_config.NumberColumn("ID", format="%d", width="small"),
                    "Cliente": st.column_config.TextColumn("👤 Cliente", width="medium"),
                    "Nome Cidade": st.column_config.TextColumn("📍 Cidade"),
                    "CPF/CNPJ": st.column_config.TextColumn("🆔 Documento"),
                    "ROTA": st.column_config.TextColumn("🚚 Rota"),
                }
            )
        else:
            components.render_df_as_list_cards(
                df_clientes_view,
                id_col="Código",
                title_col="Cliente",
                subtitle_cols=["Nome Cidade", "ROTA"],
                fields=[
                    ("Documento", "CPF/CNPJ"),
                    ("Cidade", "Nome Cidade"),
                    ("Rota", "ROTA"),
                ],
                action_label=None,
                action_key_prefix="cli_card"
            )

        if total_paginas > 1:
            st.markdown("---")
            nova_pagina = components.render_pagination(st.session_state["pag_atual_clientes"], total_paginas)
            if nova_pagina != st.session_state["pag_atual_clientes"]:
                st.session_state["pag_atual_clientes"] = nova_pagina
    else:
        st.info("Nenhum cliente encontrado nesta página.")
        if total_paginas > 0 and st.button("Voltar ao Início", key="cli_voltar_inicio"):
            st.session_state["pag_atual_clientes"] = 1
