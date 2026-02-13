# ui/plotly_theme.py
from core.config import PALETA_CORES

def aplicar_tema_plotly(
    fig,
    *,
    perfil: str = "Admin",
    base: int = 22,
    titulo: int = 28,
    eixos: int = 20,
    legenda: int = 20,
    cor_texto: str = "white",
    transparente: bool = True,
):
    """
    Aplica padronização de fonte e tema em figuras Plotly para todo o app.

    - Aumenta fonte de tudo (legenda, hover, labels, etc.)
    - Ajusta títulos e eixos
    - Mantém fundo transparente (combina com seu dark mode)
    """

    # Cor principal do tema (você pode expandir para usar outras depois)
    tema_ativo = PALETA_CORES["TEMA"].get(perfil, PALETA_CORES["TEMA"]["Admin"])
    cor_principal = tema_ativo["principal"]

    fig.update_layout(
        font=dict(size=base, color=cor_texto),
        title_font=dict(size=titulo, color=cor_texto),
        legend_font=dict(size=legenda, color=cor_texto),
        margin=dict(t=40, b=20, l=20, r=20),
    )

    # Eixos (quando existirem)
    fig.update_xaxes(
        tickfont=dict(size=eixos, color=cor_texto),
        title_font=dict(size=eixos, color=cor_texto),
    )
    fig.update_yaxes(
        tickfont=dict(size=eixos, color=cor_texto),
        title_font=dict(size=eixos, color=cor_texto),
    )

    # Fundo transparente para integrar com seu CSS (dark mode)
    if transparente:
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

    # Grid sutil (opcional mas ajuda leitura no dark)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.06)")

    # Se houver legenda horizontal embaixo em alguns gráficos, isso mantém bonito
    fig.update_layout(legend=dict(orientation="h"))

    return fig
