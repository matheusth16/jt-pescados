import streamlit as st
import time
from gspread.exceptions import APIError
import services.database as db
import ui.components as components
from core.config import LISTA_STATUS, LISTA_PAGAMENTO, PALETA_CORES

def render_page(hash_dados, perfil, nome_user):
    st.subheader("📋 Painel de Controle")
    
    df_gestao = db.buscar_pedidos_visualizacao()
    
    if not df_gestao.empty:
        df_gestao.columns = [c.upper().strip() for c in df_gestao.columns]

        with st.expander("🔍 Filtros de Busca", expanded=True):
            c_f1, c_f2 = st.columns(2)
            with c_f1: 
                f_status = st.multiselect("Filtrar por Status:", LISTA_STATUS, default=[])
            with c_f2:
                col_dt_nome = next((c for c in df_gestao.columns if "ENTREGA" in c), None)
                f_data = st.date_input("Filtrar por Data:", value=[]) if col_dt_nome else None

        df_display = df_gestao.copy()
        if f_status:
            df_display = df_display[df_display["STATUS"].isin(f_status)]
        
        cfg_visual = {
            "ID_PEDIDO": st.column_config.NumberColumn("🆔 ID", format="%d", width="small"),
            "NOME CLIENTE": st.column_config.TextColumn("👤 Cliente", width="medium"),
            "STATUS": st.column_config.SelectboxColumn("📊 Status", options=LISTA_STATUS, required=True, width="medium"),
            "PAGAMENTO": st.column_config.SelectboxColumn("💳 Pagamento", options=LISTA_PAGAMENTO, width="medium"),
            "DIA DA ENTREGA": st.column_config.TextColumn("📅 Entrega")
        }

        # Aplica cores nas células de status
        df_estilizado = df_display.style.map(
            lambda x: f'background-color: {PALETA_CORES["STATUS"].get(x, "")}; color: {"white" if x in ["NÃO GERADO", "RESERVADO", "ENTREGUE"] else "black"}', 
            subset=['STATUS']
        )

        if perfil == "Admin":
            st.dataframe(df_estilizado, use_container_width=True, height=600, hide_index=True)
        else:
            df_editado = st.data_editor(
                df_display, column_config=cfg_visual,
                use_container_width=True, height=600, hide_index=True, key="tabela_operador"
            )

            if st.button("💾 CONFIRMAR ALTERAÇÕES", type="primary", use_container_width=True):
                try:
                    db.atualizar_pedidos_editaveis(df_editado, usuario_logado=nome_user)
                    st.success("✅ Atualizado!")
                    time.sleep(1)
                    st.rerun()
                except APIError as e:
                    components.render_error_details("Erro 429: Muitos acessos simultâneos.", e)
                except Exception as e:
                    components.render_error_details("Falha ao atualizar pedidos.", e)