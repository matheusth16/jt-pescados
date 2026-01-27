import streamlit as st
import time
from datetime import datetime
from gspread.exceptions import APIError
import services.database as db
import ui.components as components
import ui.styles as styles
from core.config import LISTA_STATUS, LISTA_PAGAMENTO

def render_page(hash_dados, perfil, nome_user):
    # Aplica estilos para pegar a cor principal
    cores = styles.aplicar_estilos(perfil)
    cor_principal = cores["principal"]

    st.markdown("### 📝 Novo Pedido")
    
    df_clientes_completo = db.listar_clientes(hash_dados) # Traz lista simples ou df se mudar a logica
    # Para o selectbox funcionar com o que temos hoje no db.py:
    # Nota: listar_clientes no db.py hoje retorna lista de strings nomes.
    # Mas no seu app.py original você usava 'carregar_clientes_cache' que retornava DF.
    # Vou ajustar para usar o cache local do arquivo novo database se necessário ou manter compatibilidade.
    # Pelo app.py original, parecia retornar DF. Vamos garantir no database.py ou usar buscar_pedidos_visualizacao?
    # No app.py original você carregava clientes via db.get_connection...
    # Vamos usar db.listar_clientes para o combobox, mas para pegar dados extras (cidade/rota) precisamos do DF.
    
    # RECRIAÇÃO DA LÓGICA DO APP.PY PARA CLIENTES COMPLETO:
    try:
        conn = db.get_connection()
        ws = conn.worksheet("BaseClientes")
        import pandas as pd
        data = ws.get_all_records()
        df_clientes_completo = pd.DataFrame(data)
        if not df_clientes_completo.empty:
            df_clientes_completo.columns = [str(c).strip() for c in df_clientes_completo.columns]
    except:
        df_clientes_completo = pd.DataFrame()

    lista_nomes = ["Consumidor Final"]
    if not df_clientes_completo.empty:
        if "Cliente" in df_clientes_completo.columns:
            nomes_validos = df_clientes_completo["Cliente"].dropna().astype(str).str.upper().unique()
            lista_nomes = sorted([n for n in nomes_validos if n.strip() != ""])

    with st.container(border=True):
        st.markdown("#### 1️⃣ Identificação e Entrega")
        c1, c2 = st.columns([2, 1])
        
        with c1: 
            idx_padrao = 0
            if "VENDA A CONSUMIDOR" in lista_nomes:
                idx_padrao = lista_nomes.index("VENDA A CONSUMIDOR")
            
            cli = st.selectbox("Cliente:", lista_nomes, index=idx_padrao, key=f"c_{st.session_state.form_id}")
            
            cidade_cli = "Não informado"
            rota_cli = "-"
            
            if not df_clientes_completo.empty and "Cliente" in df_clientes_completo.columns:
                try:
                    row_cli = df_clientes_completo[df_clientes_completo["Cliente"].astype(str).str.upper() == str(cli).upper()]
                    if not row_cli.empty:
                        cidade_cli = row_cli.iloc[0].get("Nome Cidade", "SÃO CARLOS")
                        rota_cli = row_cli.iloc[0].get("ROTA", "-")
                except:
                    pass 

            rota_upper = str(rota_cli).strip().upper()
            if "RETIRADA" in rota_upper:
                st.info(f"📍 **Cidade:** {cidade_cli}  |  🏢 **Rota:** {rota_cli} (Cliente vem buscar)")
            elif rota_cli in ["-", "Não definido", "", "None"]:
                st.warning(f"📍 **Cidade:** {cidade_cli}  |  ⚠️ **Rota:** Pendente de Logística")
            else:
                st.success(f"📍 **Cidade:** {cidade_cli}  |  🚚 **Rota:** {rota_cli} (Entrega Externa)")

            @st.dialog("📜 Histórico Completo")
            def modal_historico(cliente_nome):
                st.markdown(f"### 👤 {cliente_nome}")
                st.caption("Visualizando os últimos pedidos encontrados.")
                st.markdown("---")
                
                try:
                    df_hist_bruto = db.buscar_pedidos_visualizacao()
                    itens_historico = db.obter_resumo_historico(df_hist_bruto, cliente_nome)
                    
                    if itens_historico:
                        for item in itens_historico[:10]:
                            components.render_history_item(
                                id_ped=item['id'],
                                data=item['data'],
                                status=item['status'],
                                descricao=item['descricao'],
                                pagamento=item['pagamento']
                            )
                        
                        restante = len(itens_historico) - 10
                        if restante > 0:
                            st.info(f"E mais {restante} pedidos antigos...")
                    else:
                        st.warning("📭 Nenhum histórico encontrado para este cliente.")
                except Exception as e:
                    st.error(f"Erro ao carregar: {e}")

            if st.button("📜 Ver Histórico", use_container_width=True):
                modal_historico(cli)
                
        with c2: 
            dt = st.date_input("Data de Entrega:", datetime.today(), format="DD/MM/YYYY", key=f"d_{st.session_state.form_id}")
            if dt < datetime.today().date():
                st.warning("⚠️ Atenção: Data retroativa!")
            st.write("")
            st.write("")
            try:
                df_vol = db.buscar_pedidos_visualizacao()
                if not df_vol.empty:
                    data_sel = dt.strftime("%d/%m/%Y")
                    pedidos_no_dia = len(df_vol[df_vol["DIA DA ENTREGA"] == data_sel])
                    st.metric("📅 Agendamentos do Dia", f"{pedidos_no_dia} Pedidos")
            except:
                pass

        st.divider()
        st.markdown("#### 2️⃣ Detalhes Comerciais")
        c3, c4 = st.columns(2)
        with c3: pg = st.selectbox("Forma de Pagamento:", LISTA_PAGAMENTO, key=f"p_{st.session_state.form_id}")
        with c4: stt = st.selectbox("Status Inicial:", LISTA_STATUS, index=2, key=f"s_{st.session_state.form_id}")
        
        usar_nr = st.checkbox("Informar NR do Pedido externo?", key=f"chk_{st.session_state.form_id}")
        nr_ped = ""
        if usar_nr:
            nr_ped = st.text_input("Digite o NR do Pedido:", placeholder="Ex: 12345", key=f"nr_{st.session_state.form_id}")

        st.divider()
        st.markdown("#### 3️⃣ Itens do Pedido")
        desc = st.text_area("Descrição (Quantidade e Produtos):", height=150, placeholder="Ex: 10kg de Tilápia...", key=f"de_{st.session_state.form_id}")
        form_invalido = len(desc.strip()) == 0

        if desc:
            st.markdown("---")
            components.render_preview_card(cli, dt, rota_cli, pg, stt, cor_principal)
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.caption("📝 *Preencha a descrição dos itens para liberar o botão de cadastro.*")

        # --- 4. PREVENÇÃO DE DUPLO CLIQUE ---
        c_btn1, c_btn2 = st.columns([3, 1])
        
        with c_btn1:
            if st.session_state.processando_envio:
                components.render_loader_action("🚀 Enviando pedido para o Google Sheets...")
                try:
                    db.salvar_pedido(cli, desc, dt, pg, stt, nr_pedido=nr_ped, usuario_logado=nome_user)
                    st.toast(f"✅ Pedido para **{cli}** salvo com sucesso!", icon="🎉")
                    time.sleep(1.5)
                    st.session_state.processando_envio = False
                    st.session_state.form_id += 1
                    st.rerun()
                except APIError as e:
                    components.render_error_details("Limite do Google (429). Aguarde e tente de novo.", e)
                    st.session_state.processando_envio = False 
                except ConnectionError as e:
                    components.render_error_details("Sem conexão com a internet.", e)
                    st.session_state.processando_envio = False
                except Exception as e:
                    components.render_error_details("Erro inesperado ao gravar.", e)
                    st.session_state.processando_envio = False

            else:
                def iniciar_envio():
                    st.session_state.processando_envio = True

                st.button("🚀 CADASTRAR PEDIDO", 
                          type="primary", 
                          use_container_width=True, 
                          disabled=form_invalido, 
                          on_click=iniciar_envio)
        
        with c_btn2:
            if st.button("🗑️ Limpar", 
                         use_container_width=True, 
                         disabled=st.session_state.processando_envio):
                st.session_state.form_id += 1
                st.rerun()