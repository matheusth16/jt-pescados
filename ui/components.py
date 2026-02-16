import streamlit as st
from ui.styles import PALETA_CORES

try:
    from streamlit_javascript import st_javascript  # type: ignore
except Exception:
    st_javascript = None


def render_login_header():
    """Renderiza o cabeçalho do formulário de login."""
    st.markdown("<h2 style='text-align: center;'>🐟 JT PESCADOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Acesso Restrito</p>", unsafe_allow_html=True)


def render_user_card(nome, perfil, *, compact: bool = True):
    """Renderiza o cartão do usuário na sidebar.

    Opção 2: exibe título fixo "Usuário" e o perfil em formato amigável.
    compact=True deixa o card mais baixo (ideal para sidebar).
    """
    perfil_map = {
        "ADMIN": "Administrador",
        "Admin": "Administrador",
        "OPERACAO": "Operação",
        "Operacao": "Operação",
        "OPERAÇÃO": "Operação",
        "OPERADOR": "Operador",
        "Operador": "Operador",
        "USER": "Usuário",
        "User": "Usuário",
    }
    perfil_label = perfil_map.get(str(perfil).strip(), str(perfil).strip())

    if compact:
        st.markdown(
            f"""
<div class="user-card" style="padding:10px 12px; border-radius:12px;">
    <p class="user-name" style="margin:0; font-size:0.95rem; line-height:1.1;">👤 Usuário</p>
    <p class="user-role" style="margin:4px 0 0 0; font-size:0.82rem; line-height:1.1; opacity:0.9;">{perfil_label}</p>
</div>
""",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
<div class="user-card">
    <p class="user-name">👤 Usuário</p>
    <p class="user-role">{perfil_label}</p>
</div>
""",
            unsafe_allow_html=True
        )


def render_metric_card(label, value, color_hex, compact: bool = True, **kwargs):
    """
    Renderiza os cartões de métricas do topo.
    """
    st.markdown(f"""
<div class="metric-container" style="border-left-color: {color_hex};">
    <p class="metric-label">{label}</p>
    <p class="metric-value">{value}</p>
</div>
""", unsafe_allow_html=True)


def render_status_card(label, value, css_class="", inline_color="", help_text=""):
    """
    Renderiza cartões de status no Dashboard.
    CORREÇÃO: HTML compactado para evitar erros de renderização do Markdown.
    """
    style_inline = f"border-left: 4px solid {inline_color};" if inline_color else ""

    html_tooltip_block = ""
    tooltip_css = ""

    if help_text:
        tooltip_css = """<style>
.tooltip-wrapper{position:relative;display:inline-flex;align-items:center;margin-left:6px;cursor:help;}
.tooltip-wrapper .tooltip-content{visibility:hidden;width:220px;background-color:#262730;color:#fff;text-align:left;border:1px solid #444;border-radius:6px;padding:10px;position:absolute;z-index:999;bottom:135%;left:50%;transform:translateX(-50%);opacity:0;transition:opacity 0.2s;font-size:0.85rem;box-shadow:0 4px 10px rgba(0,0,0,0.5);pointer-events:none;}
.tooltip-wrapper:hover .tooltip-content{visibility:visible;opacity:1;}
.tooltip-wrapper .tooltip-content::after{content:"";position:absolute;top:100%;left:50%;margin-left:-5px;border-width:5px;border-style:solid;border-color:#262730 transparent transparent transparent;}
.tooltip-content .status-chip{display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.8em;}
</style>"""
        html_tooltip_block = f'<div class="tooltip-wrapper">ℹ️<div class="tooltip-content">{help_text}</div></div>'

    # Montagem compacta para evitar que o Streamlit interprete espaços como código
    html = f"""{tooltip_css}<div class="status-card {css_class}" style="{style_inline}"><div style="display:flex;align-items:center;justify-content:space-between;"><span class="sc-label" style="display:flex;align-items:center;">{label}{html_tooltip_block}</span></div><p class="sc-value" style="margin-top:5px;">{value}</p></div>"""

    st.markdown(html, unsafe_allow_html=True)


def render_preview_card(cliente, data, rota, pagamento, status, cor_borda):
    """
    Card de pré-visualização no formulário de Novo Pedido.
    """
    st.markdown(f"""
<div class="preview-card" style="border-top: 4px solid {cor_borda}">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
        <span style="font-size: 1.1em; font-weight: bold; color: {cor_borda}">{cliente}</span>
        <span style="font-size: 0.9em; background: #333; padding: 2px 8px; border-radius: 4px;">{status}</span>
    </div>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em; color: #ddd;">
        <div>📅 <b>Entrega:</b> {data.strftime('%d/%m/%Y')}</div>
        <div>🚚 <b>Rota:</b> {rota}</div>
        <div>💳 <b>Pgto:</b> {pagamento}</div>
    </div>
</div>
""", unsafe_allow_html=True)


def render_history_item(id_ped, data, status, descricao, pagamento):
    """
    Renderiza um item na lista de histórico do cliente.
    """
    cor_stt = PALETA_CORES["STATUS"].get(status, "#555")

    st.markdown(f"""
<div class="hist-item">
    <div class="hist-header">
        <span class="hist-id">#{id_ped}</span>
        <span class="hist-date">{data}</span>
        <span class="hist-status" style="background-color: {cor_stt}">{status}</span>
    </div>
    <div class="hist-body">
        {descricao}
    </div>
    <div class="hist-footer">
        <span>💳 {pagamento}</span>
    </div>
</div>
""", unsafe_allow_html=True)


def render_pagination(pagina_atual, total_paginas, key_prefix="btn"):
    """
    Renderiza controles de paginação.
    """
    if total_paginas <= 1:
        return 1

    c_esq, c_prev, c_info, c_next, c_dir = st.columns([3, 1, 2, 1, 3], vertical_alignment="center")

    nova_pagina = pagina_atual

    with c_prev:
        if st.button("◀ Anterior", key=f"{key_prefix}_prev", disabled=(pagina_atual <= 1), use_container_width=True):
            nova_pagina = max(1, pagina_atual - 1)

    with c_info:
        st.markdown(
            f"<p style='text-align: center; margin: 0; color: #8b949e; font-size: 0.9em;'>"
            f"Página <b>{pagina_atual}</b> de <b>{total_paginas}</b>"
            f"</p>",
            unsafe_allow_html=True
        )

    with c_next:
        if st.button("Próxima ▶", key=f"{key_prefix}_next", disabled=(pagina_atual >= total_paginas), use_container_width=True):
            nova_pagina = min(total_paginas, pagina_atual + 1)

    return nova_pagina


def render_error_details(msg_principal, exception_obj):
    """Padroniza a exibição de erros."""
    st.error(f"{msg_principal}: {exception_obj}")
    with st.expander("Ver detalhes técnicos"):
        st.write(exception_obj)


def proxima_letra_disponivel(letras_usadas):
    """
    Recebe lista ['A', 'B', 'D'] e retorna a próxima (ex: 'C' ou 'E').
    Lógica simples: A..Z.
    """
    alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    usadas = [str(l).upper().strip() for l in letras_usadas]

    for letra in alfabeto:
        if letra not in usadas:
            return letra

    # Se estourar o alfabeto (A..Z), retorna '??'
    return "??"


# ============================================================
# ✅ NOVO: MODO LISTA (MOBILE) PARA TABELAS
# ============================================================

def render_view_mode_toggle(
    key: str,
    default: str = "Tabela",
    options=("Tabela", "Lista"),
    label: str = "Visualização"
) -> str:
    """
    Renderiza um seletor simples para alternar entre Tabela e Lista.

    Uso recomendado:
        modo = components.render_view_mode_toggle("view_pedidos")
        if modo == "Tabela":
            st.dataframe(df)
        else:
            components.render_df_as_list_cards(...)
    """
    if default not in options:
        default = options[0]

    idx = options.index(default)
    return st.radio(
        label,
        options,
        index=idx,
        horizontal=True,
        label_visibility="collapsed",
        key=key
    )


def render_kv_row(label: str, value: str):
    """Exibe uma linha 'Campo: Valor' como markdown compacto."""
    st.markdown(
        f"<div style='display:flex; gap:8px; margin:2px 0;'>"
        f"<span style='color:#8b949e; min-width:110px;'>{label}:</span>"
        f"<span style='color:#f0f6fc; font-weight:600;'>{value}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


def render_df_as_list_cards(
    df,
    *,
    id_col: str = None,
    title_col: str = None,
    subtitle_cols: list[str] = None,
    fields: list[tuple[str, str]] = None,
    action_label: str = "Ver",
    action_key_prefix: str = "card_action",
    return_on_click: bool = True
):
    """
    Renderiza um DataFrame como LISTA (cards) — ideal para celular.

    Parâmetros:
        df: pandas.DataFrame
        id_col: coluna que identifica unicamente (ex.: "ID", "Pedido_ID").
        title_col: coluna usada como título principal do card.
        subtitle_cols: colunas mostradas logo abaixo do título.
        fields: lista de tuplas (label, coluna) para exibir como "campo: valor".
        action_label: rótulo do botão (ex.: "Ver", "Editar", "Abrir").
        action_key_prefix: prefixo para keys do Streamlit.
        return_on_click: se True, retorna o id/índice clicado.

    Retorno:
        - Se return_on_click=True: retorna o valor do id_col (ou o índice) do item clicado, ou None.
        - Se False: retorna None.
    """
    if df is None or len(df) == 0:
        st.info("Nenhum registro para exibir.")
        return None

    subtitle_cols = subtitle_cols or []
    fields = fields or []

    clicked_id = None

    for i, row in df.reset_index(drop=False).iterrows():
        # Identificador único
        if id_col and id_col in row:
            item_id = row[id_col]
        else:
            # fallback: usa índice original, se existir
            item_id = row.get("index", i)

        # Título
        if title_col and title_col in row:
            title = str(row[title_col])
        elif id_col and id_col in row:
            title = f"#{row[id_col]}"
        else:
            title = f"Item {i+1}"

        # Subtítulo
        subtitle_parts = []
        for col in subtitle_cols:
            if col in row and str(row[col]).strip() != "":
                subtitle_parts.append(str(row[col]))
        subtitle = " • ".join(subtitle_parts)

        # Card container
        with st.container(border=True):
            # ✅ Evita f-string aninhada com escapes (Python 3.11)
            if subtitle:
                subtitle_html = (
                    f"<div style='color:#8b949e; font-size:0.95em;'>"
                    f"{subtitle}"
                    f"</div>"
                )
            else:
                subtitle_html = ""

            st.markdown(
                f"<div style='display:flex; flex-direction:column; gap:4px;'>"
                f"<div style='font-size:1.05em; font-weight:800; color:#f0f6fc;'>{title}</div>"
                f"{subtitle_html}"
                f"</div>",
                unsafe_allow_html=True
            )

            # Campos
            for lbl, col in fields:
                if col in row:
                    render_kv_row(lbl, str(row[col]))

            # Ação
            if action_label:
                if st.button(action_label, key=f"{action_key_prefix}_{item_id}", use_container_width=True):
                    clicked_id = item_id

    return clicked_id if return_on_click else None


def is_mobile(breakpoint: int = 768) -> bool:
    """Retorna True se a largura da tela for menor que breakpoint."""
    if st_javascript is None:
        return False  # fallback: assume desktop

    w = st_javascript("window.innerWidth")
    try:
        return int(w) < breakpoint
    except Exception:
        return False
