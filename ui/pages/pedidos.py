import streamlit as st
import pandas as pd
import time
from datetime import datetime
import services.database as db
import ui.components as components
import ui.styles as styles
from core.config import LISTA_STATUS, LISTA_PAGAMENTO

def render_page(hash_dados, perfil, nome_user):
    # Aplica estilos para pegar a cor principal
    cores = styles.aplicar_estilos(perfil)
    cor_principal = cores["principal"]

    st.markdown("### 📝 Novo Pedido")
    
    # --- CONTROLE DE ESTADO DO MODAL (AQUI ESTÁ A CORREÇÃO) ---
    # Essa variável garante que o modal fique aberto até mandarmos fechar
    if "show_modal_confirmar" not in st.session_state:
        st.session_state.show_modal_confirmar = False

    # Inicializa DataFrame vazio como fallback
    df_clientes_completo = pd.DataFrame() 
    
    try:
        # Busca dados no Supabase para pegar Cidade e Rota
        client = db.get_db_client()
        response = client.table("clientes").select("*").execute()
        
        if response.data:
            df_clientes_completo = pd.DataFrame(response.data)
            df_clientes_completo.columns = [str(c).strip() for c in df_clientes_completo.columns]
    except Exception:
        pass

    lista_nomes = []
    if not df_clientes_completo.empty:
        if "Cliente" in df_clientes_completo.columns:
            nomes_validos = df_clientes_completo["Cliente"].dropna().astype(str).str.upper().unique()
            lista_nomes = sorted([n for n in nomes_validos if n.strip() != ""])

    if not lista_nomes:
        lista_nomes = ["Nenhum cliente cadastrado"]

    # --- FUNÇÃO DO MODAL (CARD CENTRO DA TELA) ---
    @st.dialog("📋 Confirmar Detalhes do Pedido")
    def modal_confirmacao():
        # Inicializa variáveis internas se não existirem
        if "m_editando" not in st.session_state:
            st.session_state.m_editando = False
            
        # --- MODO DE VISUALIZAÇÃO (RESUMO) ---
        if not st.session_state.m_editando:
            st.markdown("### Resumo")
            st.write(f"**👤 Cliente:** {st.session_state.m_cli}")
            st.write(f"**📅 Entrega:** {st.session_state.m_dt.strftime('%d/%m/%Y')}")
            st.write(f"**💳 Pagamento:** {st.session_state.m_pg}")
            st.write(f"**📊 Status:** {st.session_state.m_stt}")
            if st.session_state.m_nr:
                st.write(f"**🔢 NR Pedido:** {st.session_state.m_nr}")
            
            st.info(f"**📝 Itens:**\n\n{st.session_state.m_desc}")
            st.divider()

            c_conf, c_edit = st.columns(2)
            
            with c_conf:
                if st.button("✅ Confirmar e Salvar", type="primary", use_container_width=True):
                    with st.spinner("Gravando pedido..."):
                        try:
                            db.salvar_pedido(
                                st.session_state.m_cli, 
                                st.session_state.m_desc, 
                                st.session_state.m_dt, 
                                st.session_state.m_pg, 
                                st.session_state.m_stt, 
                                nr_pedido=st.session_state.m_nr, 
                                usuario_logado=nome_user
                            )
                            st.toast(f"✅ Pedido salvo com sucesso!", icon="🎉")
                            time.sleep(1.5)
                            
                            # Limpa variáveis e fecha o modal
                            for key in ["m_cli", "m_dt", "m_pg", "m_stt", "m_nr", "m_desc", "m_editando", "show_modal_confirmar"]:
                                if key in st.session_state: del st.session_state[key]
                            
                            st.session_state.form_id += 1
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")

            with c_edit:
                if st.button("✏️ Editar", use_container_width=True):
                    st.session_state.m_editando = True
                    st.rerun()
        
        # --- MODO DE EDIÇÃO (ALTERAR DADOS DENTRO DO CARD) ---
        else:
            st.markdown("### ✏️ Editar Informações")
            
            # Recria os campos para edição
            # Garante que o índice existe na lista, senão usa 0
            idx_cli = lista_nomes.index(st.session_state.m_cli) if st.session_state.m_cli in lista_nomes else 0
            st.session_state.m_cli = st.selectbox("Cliente", lista_nomes, index=idx_cli, key="ed_cli")
            
            st.session_state.m_dt = st.date_input("Data Entrega", value=st.session_state.m_dt, min_value=datetime.today().date(), key="ed_dt")
            
            idx_pg = LISTA_PAGAMENTO.index(st.session_state.m_pg) if st.session_state.m_pg in LISTA_PAGAMENTO else 0
            st.session_state.m_pg = st.selectbox("Pagamento", LISTA_PAGAMENTO, index=idx_pg, key="ed_pg")
            
            idx_stt = LISTA_STATUS.index(st.session_state.m_stt) if st.session_state.m_stt in LISTA_STATUS else 2
            st.session_state.m_stt = st.selectbox("Status", LISTA_STATUS, index=idx_stt, key="ed_stt")
            
            st.session_state.m_nr = st.text_input("NR Pedido", value=st.session_state.m_nr, key="ed_nr")
            st.session_state.m_desc = st.text_area("Descrição", value=st.session_state.m_desc, height=150, key="ed_desc")

            if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                if not st.session_state.m_desc.strip():
                    st.error("A descrição não pode ficar vazia.")
                else:
                    st.session_state.m_editando = False
                    st.rerun()

    # --- INTERFACE PRINCIPAL ---
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
                st.caption("Visualizando histórico de pedidos.")
                st.markdown("---")
                
                key_limit = f"hist_limit_{cliente_nome}"
                if key_limit not in st.session_state:
                    st.session_state[key_limit] = 5 
                
                try:
                    df_hist_bruto = db.buscar_pedidos_visualizacao()
                    itens_historico = db.obter_resumo_historico(df_hist_bruto, cliente_nome)
                    
                    total_itens = len(itens_historico)
                    limite_atual = st.session_state[key_limit]

                    if itens_historico:
                        for item in itens_historico[:limite_atual]:
                            components.render_history_item(
                                id_ped=item['id'],
                                data=item['data'],
                                status=item['status'],
                                descricao=item['descricao'],
                                pagamento=item['pagamento']
                            )
                        
                        restante = total_itens - limite_atual
                        if restante > 0:
                            st.info(f"Ainda existem {restante} pedidos mais antigos.")
                            if st.button("🔄 Carregar mais antigos", use_container_width=True):
                                st.session_state[key_limit] += 5 
                                st.rerun()
                    else:
                        st.warning("📭 Nenhum histórico encontrado para este cliente.")
                except Exception as e:
                    st.error(f"Erro ao carregar: {e}")

            if st.button("📜 Ver Histórico", use_container_width=True):
                modal_historico(cli)
                
        with c2: 
            dt = st.date_input(
                "Data de Entrega:", 
                value=datetime.today(), 
                min_value=datetime.today().date(), 
                format="DD/MM/YYYY", 
                key=f"d_{st.session_state.form_id}"
            )
            
            st.write("")
            st.write("")
            try:
                df_vol = db.buscar_pedidos_visualizacao()
                if not df_vol.empty:
                    data_sel = dt.strftime("%d/%m/%Y")
                    col_entrega = next((c for c in df_vol.columns if "ENTREGA" in c.upper()), None)
                    if col_entrega:
                        pedidos_no_dia = len(df_vol[df_vol[col_entrega] == data_sel])
                        st.metric("📅 Agendamentos do Dia", f"{pedidos_no_dia} Pedidos")
            except:
                pass

        st.divider()
        st.markdown("#### 2️⃣ Detalhes Comerciais")
        c3, c4 = st.columns(2)
        with c3: pg = st.selectbox("Forma de Pagamento:", LISTA_PAGAMENTO, key=f"p_{st.session_state.form_id}")
        with c4: stt = st.selectbox("Status Inicial:", LISTA_STATUS, index=2, key=f"s_{st.session_state.form_id}")
        
        usar_nr = st.checkbox("Informar NR do Pedido?", key=f"chk_{st.session_state.form_id}")
        
        nr_ped = ""
        if usar_nr:
            nr_ped = st.text_input("Digite o NR do Pedido:", placeholder="Ex: 12345", key=f"nr_{st.session_state.form_id}")

        st.divider()
        st.markdown("#### 3️⃣ Itens do Pedido")
        desc = st.text_area("Descrição (Quantidade e Produtos):", height=150, placeholder="Ex: 10kg de Tilápia...", key=f"de_{st.session_state.form_id}")
        
        if desc:
            st.markdown("---")
            components.render_preview_card(cli, dt, rota_cli, pg, stt, cor_principal)
            st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.caption("📝 *Preencha a descrição dos itens para liberar o botão de cadastro.*")
        
        c_btn1, c_btn2 = st.columns([3, 1])
        
        with c_btn1:
            # BOTÃO GATILHO: SÓ DEFINE QUE O MODAL DEVE ABRIR
            if st.button("🚀 CADASTRAR PEDIDO", type="primary", use_container_width=True):
                if not desc.strip():
                    st.error("⚠️ Digite os itens do pedido antes de cadastrar!")
                else:
                    # Salva os dados no estado e ativa a flag do modal
                    st.session_state.m_cli = cli
                    st.session_state.m_dt = dt
                    st.session_state.m_pg = pg
                    st.session_state.m_stt = stt
                    st.session_state.m_nr = nr_ped
                    st.session_state.m_desc = desc
                    st.session_state.show_modal_confirmar = True
                    st.rerun()
        
        with c_btn2:
            if st.button("🗑️ Limpar", use_container_width=True):
                st.session_state.form_id += 1
                st.rerun()

    # --- VERIFICAÇÃO FINAL: SE A VARIÁVEL ESTIVER TRUE, ABRE O MODAL ---
    if st.session_state.show_modal_confirmar:
        modal_confirmacao()