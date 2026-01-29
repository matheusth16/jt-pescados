import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import services.database as db
import ui.components as components
import ui.styles as styles
from core.config import PALETA_CORES

def render_page(hash_dados, perfil):
    # Aplica estilos para pegar a cor principal do tema
    cores = styles.aplicar_estilos(perfil)
    cor_principal = cores["principal"]
    
    c_titulo, c_filtro = st.columns([1, 1.2], vertical_alignment="center")
    with c_titulo:
        st.markdown("### 📊 Indicadores de Performance")
    with c_filtro:
        filtro_tempo = st.segmented_control(
            "Período:", options=["Hoje", "Últimos 7 Dias", "Mês Atual", "Tudo"], 
            default="Tudo", selection_mode="single", label_visibility="collapsed"
        )
    if not filtro_tempo: filtro_tempo = "Tudo"
    st.markdown("---")

    df_bruto = db.buscar_pedidos_visualizacao()
    
    if not df_bruto.empty:
        # Padroniza colunas para evitar erros de maiúsculas/minúsculas
        df_bruto.columns = [c.upper().strip() for c in df_bruto.columns]
        col_dt = next((c for c in df_bruto.columns if "ENTREGA" in c), None)

        df_dash = df_bruto.copy()
        if col_dt:
            # Garante conversão de data compatível com Supabase
            df_dash[col_dt] = pd.to_datetime(df_dash[col_dt], dayfirst=True, errors='coerce')
            hoje = pd.Timestamp.now().normalize()
            
            if filtro_tempo == "Hoje":
                df_dash = df_dash[df_dash[col_dt] == hoje]
            elif filtro_tempo == "Últimos 7 Dias":
                df_dash = df_dash[df_dash[col_dt] >= (hoje - pd.Timedelta(days=7))]
            elif filtro_tempo == "Mês Atual":
                df_dash = df_dash[(df_dash[col_dt].dt.month == hoje.month) & (df_dash[col_dt].dt.year == hoje.year)]

        total_pedidos = len(df_dash)
        
        # --- GRÁFICOS (PIZZA E BARRA) ---
        c_pizza, c_barra = st.columns(2)
        with c_pizza:
            with st.container(border=True):
                st.markdown("#### Status dos Pedidos")
                if "STATUS" in df_dash.columns:
                    contagem_status = df_dash["STATUS"].value_counts().reset_index()
                    contagem_status.columns = ["STATUS", "TOTAL"]
                    
                    fig_status = px.pie(
                        contagem_status, 
                        values="TOTAL", 
                        names="STATUS", 
                        hole=0.6, 
                        color="STATUS", 
                        color_discrete_map=PALETA_CORES["STATUS"]
                    )
                    
                    fig_status.add_annotation(
                        text=f"<b>{total_pedidos}</b><br>PEDIDOS", 
                        showarrow=False, 
                        font=dict(size=26, color="white")
                    )
                    
                    fig_status.update_traces(
                        textposition='outside', 
                        textinfo='percent+label',
                        domain={'x': [0.1, 0.9], 'y': [0.1, 0.9]},
                        hovertemplate='<b>%{label}</b><br>Qtd: %{value}<br>(%{percent})',
                        sort=True, 
                        direction='clockwise', 
                        rotation=90
                    )
                    
                    fig_status.update_layout(
                        margin=dict(t=80, b=50, l=50, r=50), 
                        showlegend=True,
                        legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5),
                        paper_bgcolor='rgba(0,0,0,0)', 
                        plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=16, color="white")
                    )
                    
                    st.plotly_chart(fig_status, use_container_width=True)

        with c_barra:
            with st.container(border=True):
                st.markdown("#### Preferência de Pagamento")
                if "PAGAMENTO" in df_dash.columns:
                    contagem_pg = df_dash["PAGAMENTO"].value_counts().reset_index()
                    contagem_pg.columns = ["PAGAMENTO", "QTD"]
                    contagem_pg = contagem_pg.sort_values("QTD", ascending=True)
                    fig_pg = px.bar(contagem_pg, x="QTD", y="PAGAMENTO", orientation='h',
                                text="QTD", color_discrete_sequence=[cor_principal])
                    fig_pg.update_layout(xaxis_title="", yaxis_title="",
                        margin=dict(t=30, b=10, l=10, r=60),
                        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=16,color="white"), xaxis=dict(showgrid=False, showticklabels=False))
                    fig_pg.update_traces(marker_line_color='rgba(0,0,0,0)', textposition='outside', textfont_size=18)
                    st.plotly_chart(fig_pg, use_container_width=True)

        # --- SAÚDE DA OPERAÇÃO ---
        st.markdown("#### Resumo da Operação")
        c1, c2, c3 = st.columns(3)
        with c1:
            entregues = len(df_dash[df_dash["STATUS"] == "ENTREGUE"]) if "STATUS" in df_dash.columns else 0
            pct_saude = (entregues / total_pedidos * 100) if total_pedidos > 0 else 0
            classe_cor = "saude-baixa" if pct_saude < 50 else "saude-media" if pct_saude < 80 else "saude-alta"
            components.render_status_card("🩺 Saúde da Operação", f"{pct_saude:.1f}%", css_class=classe_cor)
        
        with c2:
            if "STATUS" in df_dash.columns:
                counts = df_dash["STATUS"].value_counts()
                
                p_orcamento = int(counts.get("ORÇAMENTO", 0))
                p_reservado = int(counts.get("RESERVADO", 0))
                p_n_gerado  = int(counts.get("NÃO GERADO", 0))
                p_pendente  = int(counts.get("PENDENTE", 0))
                p_gerado    = int(counts.get("GERADO", 0))
                
                total_aguardando = p_orcamento + p_reservado + p_n_gerado + p_pendente + p_gerado
                
                def make_chip(label, val, cor):
                    return f'<div class="status-chip"><div><span class="chip-dot" style="background-color: {cor}; box-shadow: 0 0 5px {cor};"></span><span class="chip-label">{label}</span></div><span class="chip-val">{val}</span></div>'

                help_html = (
                    make_chip("Orçamento", p_orcamento, PALETA_CORES["STATUS"]["ORÇAMENTO"]) +
                    make_chip("Reservado", p_reservado, PALETA_CORES["STATUS"]["RESERVADO"]) +
                    make_chip("Não Gerado", p_n_gerado, PALETA_CORES["STATUS"]["NÃO GERADO"]) +
                    make_chip("Pendente", p_pendente, PALETA_CORES["STATUS"]["PENDENTE"]) +
                    make_chip("Gerado", p_gerado, PALETA_CORES["STATUS"]["GERADO"])
                )
            else:
                total_aguardando = 0
                help_html = "Sem dados"

            components.render_status_card(
                "⏳ Aguardando Processo", 
                total_aguardando, 
                inline_color="#FFA500", 
                help_text=help_html
            )
            
        with c3:
            components.render_status_card("✅ Pedidos Entregues", entregues, inline_color="#28A745")
        
        # --- EVOLUÇÃO ---
        st.markdown("#### 📈 Evolução de Pedidos por Dia")
        with st.container(border=True):
            if col_dt and not df_dash.empty:
                evolucao_diaria = df_dash.groupby(df_dash[col_dt].dt.date).size().reset_index(name='QTD')
                evolucao_diaria.columns = ['DATA', 'QTD']
                evolucao_diaria = evolucao_diaria.sort_values('DATA')
                fig_evol = px.line(evolucao_diaria, x='DATA', y="QTD", markers=True, 
                                line_shape="spline", color_discrete_sequence=[cor_principal])
                fig_evol.update_layout(xaxis_title="", yaxis_title="Pedidos",
                    margin=dict(t=30, b=10, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=16,color="white"), xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
                st.plotly_chart(fig_evol, use_container_width=True)
                
        # --- TOP CLIENTES ---
        st.markdown("#### 🏆 Top 5 Clientes do Período")
        with st.container(border=True):
            if "NOME CLIENTE" in df_dash.columns:
                top_clientes = df_dash["NOME CLIENTE"].value_counts().reset_index().head(5)
                top_clientes.columns = ["CLIENTE", "QTD"]
                
                # CORREÇÃO DO ERRO 4.0: Força conversão para texto
                top_clientes["CLIENTE"] = top_clientes["CLIENTE"].astype(str)
                
                max_pedidos = top_clientes["QTD"].max() if not top_clientes.empty else 1
                st.data_editor(top_clientes, column_config={
                        "CLIENTE": st.column_config.TextColumn("👤 Nome do Cliente"),
                        "QTD": st.column_config.ProgressColumn("📦 Volume de Pedidos", format="%d", min_value=0, max_value=int(max_pedidos)),
                    }, hide_index=True, use_container_width=True, disabled=True)
    else:
        st.info("Sem dados para exibir (ou houve falha no carregamento).")