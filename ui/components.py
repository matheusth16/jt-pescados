import streamlit as st
from ui.styles import PALETA_CORES

def render_login_header():
    """Renderiza o cabeçalho do formulário de login."""
    st.markdown("<h2 style='text-align: center;'>🐟 JT PESCADOS</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>Acesso Restrito</p>", unsafe_allow_html=True)

def render_user_card(nome, perfil):
    """Renderiza o cartão do utilizador na sidebar."""
    st.markdown(f"""
<div class="user-card">
    <p class="user-name">👤 {nome}</p>
    <p class="user-role">{perfil}</p>
</div>
""", unsafe_allow_html=True)

def render_metric_card(label, value, color_hex):
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
        tooltip_css = """<style>.tooltip-wrapper{position:relative;display:inline-flex;align-items:center;margin-left:6px;cursor:help;}.tooltip-wrapper .tooltip-content{visibility:hidden;width:220px;background-color:#262730;color:#fff;text-align:left;border:1px solid #444;border-radius:6px;padding:10px;position:absolute;z-index:999;bottom:135%;left:50%;transform:translateX(-50%);opacity:0;transition:opacity 0.2s;font-size:0.85rem;box-shadow:0 4px 10px rgba(0,0,0,0.5);pointer-events:none;}.tooltip-wrapper:hover .tooltip-content{visibility:visible;opacity:1;}.tooltip-wrapper .tooltip-content::after{content:"";position:absolute;top:100%;left:50%;margin-left:-5px;border-width:5px;border-style:solid;border-color:#262730 transparent transparent transparent;}.tooltip-content .status-chip{display:flex;justify-content:space-between;margin-bottom:4px;font-size:0.8em;}</style>"""
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