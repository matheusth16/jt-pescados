import streamlit as st
import pandas as pd
import time
import io
from datetime import datetime
import services.database as db
import ui.components as components
from core.config import PALETA_CORES
from services.utils import calcular_status_validade

# --- 1. CORES ESPECÍFICAS DO SALMÃO ---
PALETA_SALMAO = {
    "Livre": "#11734b", "Reservado": "#0a53a8", "Orçamento": "#e8eaed",
    "Gerado": "#ff8500", "Aberto": "#473822"
}

def highlight_status_salmao(val):
    val_limpo = str(val).strip()
    cor = PALETA_SALMAO.get(val_limpo, None)
    if cor:
        cor_texto = "black" if val_limpo in ["Orçamento"] else "white"
        return f'background-color: {cor}; color: {cor_texto}; font-weight: 600;'
    return ''

# --- CACHE ESTRATÉGICO: PROCESSAMENTO VISUAL ---
@st.cache_data(show_spinner=False)
def preparar_dataframe_view(df_input):
    """
    Realiza a limpeza e conversão de tipos do DataFrame para exibição.
    Cacheado para evitar reprocessamento a cada rerun da interface.
    """
    if df_input.empty:
        return df_input
        
    df_view = df_input.copy()
    
    # Sanitização de Textos (Remove None/Nan)
    cols_texto = ["Calibre", "Cliente", "Fornecedor"]
    for c in cols_texto:
        if c in df_view.columns:
            df_view[c] = df_view[c].fillna("").astype(str).replace("None", "").replace("nan", "")
    
    # Sanitização de Status
    if "Status" in df_view.columns:
        df_view["Status"] = df_view["Status"].fillna("Livre").astype(str).replace("None", "Livre").replace("nan", "Livre").replace("", "Livre")
    
    # Sanitização Numérica
    if "Peso" in df_view.columns:
        df_view["Peso"] = pd.to_numeric(df_view["Peso"], errors='coerce').fillna(0.0)
        
    # Conversão de Datas
    if "Validade" in df_view.columns:
        df_view["Validade"] = pd.to_datetime(df_view["Validade"], format="%d/%m/%Y", errors="coerce")
        
    return df_view

# --- 2. MODAL UNIFICADO ---
@st.dialog("🐟 Detalhes da Tag")
def modal_detalhes_tag(row_dict, perfil, nome_user, range_atual):
    tag_id = row_dict.get('Tag')
    # Recupera o status original do banco
    status_db = row_dict.get('Status')
    if not status_db or str(status_db).strip() in ["", "None"]: status_db = "Livre"

    # 1. Definimos o peso original do banco
    peso_banco = float(row_dict.get('Peso', 0))
    
    # 2. Definimos a chave do input para checar o session_state
    key_input_peso = f"num_peso_{tag_id}"
    
    # 3. Lógica para pegar o valor em tempo real
    if key_input_peso in st.session_state:
        peso_considerado = st.session_state[key_input_peso]
    else:
        peso_considerado = peso_banco
        
    st.markdown(f"### 🏷️ TAG #{tag_id}")
    
    # --- CABEÇALHO ---
    c1, c2, c3 = st.columns(3)
    with c1: 
        st.caption("Calibre")
        st.write(f"**{row_dict.get('Calibre', '')}**")
    with c2: 
        st.caption("Peso Atual")
        st.write(f"**{peso_considerado:.3f} kg**")
    with c3: 
        st.caption("Status Atual (Banco)")
        cor = PALETA_SALMAO.get(status_db, "#333")
        cor_txt = "black" if status_db == "Orçamento" else "white"
        st.markdown(f"<span style='background-color:{cor}; color:{cor_txt}; padding: 4px 8px; border-radius: 4px; font-weight:bold'>{status_db}</span>", unsafe_allow_html=True)

    st.divider()

    # --- SUBTAGS (Sem cache local pois é altamente dinâmico) ---
    df_sub = db.buscar_subtags_por_tag(tag_id)
    if not df_sub.empty:
        st.caption("🧱 Histórico de Fracionamento (Subtags)")
        st.dataframe(df_sub, use_container_width=True, hide_index=True)
        st.divider()

    if perfil == "Admin":
        # MODO LEITURA
        c_adm1, c_adm2 = st.columns(2)
        with c_adm1:
            st.markdown(f"**👤 Cliente:** {row_dict.get('Cliente', '-')}")
            st.markdown(f"**🏭 Fornecedor:** {row_dict.get('Fornecedor', '-')}")
        with c_adm2:
            st.markdown(f"**📅 Validade:** {row_dict.get('Validade', '-')}")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Fechar", use_container_width=True):
            st.session_state.tag_para_visualizar = None 
            st.rerun()
    else:
        # --- MODO INTERATIVO ---
        
        # 1. Seletor de Status
        opcoes_status = ["Livre", "Reservado", "Orçamento", "Gerado", "Aberto"]
        idx_s = opcoes_status.index(status_db) if status_db in opcoes_status else 0
        
        novo_status = st.selectbox("Status da Tag:", opcoes_status, index=idx_s, key=f"sel_status_{tag_id}")
        
        # 2. Definição das Abas
        abas_titulos = ["✏️ Editar Dados"]
        if novo_status == "Aberto":
            abas_titulos.insert(0, "✂️ Fracionar (Corte)")
            
        abas = st.tabs(abas_titulos)

        # --- ABA FRACIONAR (Só aparece se Status == Aberto) ---
        if novo_status == "Aberto":
            with abas[0]:
                st.info("🔪 Adicione unidades retiradas desta peça.")
                letras_usadas, peso_ja_consumido = db.get_consumo_tag(tag_id)
                
                # Saldo dinâmico
                saldo = max(0.0, peso_considerado - peso_ja_consumido)
                
                c_info1, c_info2 = st.columns(2)
                with c_info1: st.metric("Já Usado", f"{peso_ja_consumido:.3f} kg")
                with c_info2: st.metric("Saldo", f"{saldo:.3f} kg")

                with st.form(f"split_{tag_id}"):
                    c_f1, c_f2 = st.columns(2)
                    with c_f1: 
                        letra_sug = components.proxima_letra_disponivel(letras_usadas)
                        novo_letra = st.text_input("Letra (Sufixo)", value=letra_sug, max_chars=2)
                    with c_f2:
                        novo_peso_sub = st.number_input("Peso (kg)", min_value=0.0, max_value=saldo, step=0.1, format="%.3f")
                    novo_cli_sub = st.text_input("Cliente Destino")
                    
                    if st.form_submit_button("✅ CONFIRMAR UNIDADE", type="primary", use_container_width=True):
                        letra_limpa = novo_letra.strip().upper()
                        
                        if not novo_cli_sub or novo_peso_sub <= 0 or letra_limpa in letras_usadas:
                            st.error("Dados inválidos (Peso zero ou Letra repetida).")
                        else:
                            # >>> NOVA LÓGICA: SALVAR O PAI PRIMEIRO <<<
                            # Recuperamos os valores que estão nos inputs da outra aba via session_state
                            
                            # 1. Recupera Calibre
                            s_cal_sel = st.session_state.get(f"sel_cal_{tag_id}")
                            s_cal_txt = st.session_state.get(f"txt_cal_{tag_id}")
                            if s_cal_sel == "Outro": FINAL_CAL = s_cal_txt
                            elif s_cal_sel: FINAL_CAL = s_cal_sel
                            else: FINAL_CAL = row_dict.get('Calibre')
                            
                            # 2. Recupera Validade (Formatando para String)
                            s_val_obj = st.session_state.get(f"dt_val_{tag_id}")
                            if s_val_obj: FINAL_VAL = s_val_obj.strftime("%d/%m/%Y")
                            else: FINAL_VAL = row_dict.get('Validade')

                            # 3. Recupera Clientes/Forn
                            FINAL_CLI = st.session_state.get(f"txt_cli_{tag_id}", row_dict.get('Cliente'))
                            FINAL_FORN = st.session_state.get(f"txt_forn_{tag_id}", row_dict.get('Fornecedor'))
                            
                            # Monta o DataFrame de Atualização do Pai
                            df_pai_up = pd.DataFrame([{
                                "Tag": tag_id, 
                                "Status": novo_status, # Garante que salva como 'Aberto'
                                "Calibre": FINAL_CAL, 
                                "Peso": peso_considerado, # Salva o peso novo digitado
                                "Validade": FINAL_VAL, 
                                "Cliente": FINAL_CLI, 
                                "Fornecedor": FINAL_FORN
                            }])
                            
                            # Salva o Pai no Banco
                            db.salvar_alteracoes_estoque(df_pai_up, nome_user)
                            # ------------------------------------------

                            # Agora salva a Subtag
                            ok = db.registrar_subtag(tag_id, letra_limpa, novo_cli_sub, novo_peso_sub, "Livre", nome_user)
                            if ok:
                                st.success("Unidade criada e Tag Pai atualizada!")
                                # Atualiza o cache local forçando busca nova
                                if range_atual:
                                    st.session_state.salmao_df = db.get_estoque_filtrado(range_atual[0], range_atual[1])
                                time.sleep(0.5)
                                # [CORREÇÃO] Força o reset da tabela
                                st.session_state.salmao_editor_key += 1
                                st.session_state.tag_para_visualizar = None
                                st.rerun()

        # --- ABA EDITAR (Sempre a última) ---
        with abas[-1]:
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                cal_atual = str(row_dict.get('Calibre', '')).strip()
                if cal_atual == "None": cal_atual = ""
                
                opcoes_calibre = ["8/10", "10/12", "12/14", "14/16", "Outro"]
                
                if cal_atual in ["8/10", "10/12", "12/14", "14/16"]:
                    idx_cal = opcoes_calibre.index(cal_atual)
                    val_manual_inicial = ""
                else:
                    idx_cal = opcoes_calibre.index("Outro")
                    val_manual_inicial = cal_atual if cal_atual else ""
                
                sel_calibre = st.selectbox("Calibre", opcoes_calibre, index=idx_cal, key=f"sel_cal_{tag_id}")
                
                if sel_calibre == "Outro":
                    calibre_final = st.text_input("Digite o Calibre:", value=val_manual_inicial, key=f"txt_cal_{tag_id}")
                else:
                    calibre_final = sel_calibre

            with c_e2:
                # O 'value' é o do banco, mas a 'key' permite o Streamlit lembrar o que você digitou
                m_peso = st.number_input("Peso (kg)", value=peso_banco, format="%.3f", key=f"num_peso_{tag_id}")
                
                try: d_val = datetime.strptime(str(row_dict.get('Validade')), "%d/%m/%Y")
                except: d_val = datetime.today()
                m_validade = st.date_input("Validade", value=d_val, format="DD/MM/YYYY", key=f"dt_val_{tag_id}")

            m_cli = st.text_input("Cliente", value=str(row_dict.get('Cliente') or "").replace("None", ""), key=f"txt_cli_{tag_id}")
            m_forn = st.text_input("Fornecedor", value=str(row_dict.get('Fornecedor') or "").replace("None", ""), key=f"txt_forn_{tag_id}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("💾 SALVAR ALTERAÇÕES", type="primary", use_container_width=True, key=f"btn_save_{tag_id}"):
                df_up = pd.DataFrame([{
                    "Tag": tag_id, 
                    "Status": novo_status, 
                    "Calibre": calibre_final, 
                    "Peso": m_peso,
                    "Validade": m_validade.strftime("%d/%m/%Y"), 
                    "Cliente": m_cli, 
                    "Fornecedor": m_forn
                }])
                
                # Salva e limpa os caches relevantes
                db.salvar_alteracoes_estoque(df_up, nome_user)
                
                if str(novo_status).strip().upper() == "GERADO":
                    db.arquivar_tags_geradas([tag_id], nome_user)
                    st.toast(f"Tag {tag_id} arquivada como GERADO!")

                st.success("Atualizado com sucesso!")
                
                # Atualiza sessão com dados frescos do banco
                if range_atual:
                        st.session_state.salmao_df = db.get_estoque_filtrado(range_atual[0], range_atual[1])
                
                time.sleep(0.5)
                # [CORREÇÃO] Força o reset da tabela
                st.session_state.salmao_editor_key += 1
                st.session_state.tag_para_visualizar = None 
                st.rerun()

# --- NOVO: FRAGMENTO DA TABELA (Interface Isolada) ---
@st.fragment
def painel_tabela_interativa(df_base, perfil, range_str):
    """
    Fragmento que isola a tabela e seus filtros do resto da página.
    Interações aqui (como filtrar) NÃO recarregam o script inteiro.
    """
    # OTIMIZAÇÃO: Usa a função de cache local para evitar reprocessamento do DF
    df_view = preparar_dataframe_view(df_base)

    with st.expander("🌪️ Filtros Avançados", expanded=False):
        c_f1, c_f2 = st.columns(2)
        with c_f1: 
            cal_ops = sorted([str(x) for x in df_view["Calibre"].unique() if x])
            f_cal = st.multiselect("Calibre", cal_ops)
        with c_f2:
            forn_ops = sorted([str(x) for x in df_view["Fornecedor"].unique() if x])
            f_forn = st.multiselect("Fornecedor", forn_ops)
            
        # Filtro Pandas (Local) - Rápido para <200 linhas
        if f_cal: df_view = df_view[df_view["Calibre"].astype(str).isin(f_cal)]
        if f_forn: df_view = df_view[df_view["Fornecedor"].astype(str).isin(f_forn)]

    st.markdown(f"### 📋 Tabela Geral: {range_str}")
    
    with st.container():
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_view.to_excel(writer, index=False, sheet_name='Salmao')
        
        st.download_button(
            label="📥 Baixar Tabela em Excel",
            data=buffer,
            file_name=f"estoque_salmao_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
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
        "Fornecedor": st.column_config.TextColumn("Fornecedor", width="medium")
    }
    
    travadas = list(cfg_colunas.keys())
    df_view.insert(0, "VER", False)
    cfg_colunas["VER"] = st.column_config.CheckboxColumn("Editar" if perfil != "Admin" else "Ver", width="small")

    df_styled = df_view.style.map(highlight_status_salmao, subset=["Status"])

    tabela = st.data_editor(
        df_styled,
        key=f"editor_salmao_{st.session_state.salmao_editor_key}",
        use_container_width=True, 
        height=500, 
        hide_index=True,
        column_config=cfg_colunas, 
        disabled=travadas
    )

    # Detecção de Clique (Seleção)
    selecionado = tabela[tabela["VER"] == True]
    if not selecionado.empty:
        dados_linha = selecionado.iloc[0].to_dict()
        
        # Formatação segura de validade para o modal
        val_validade = dados_linha.get('Validade')
        if pd.notna(val_validade) and hasattr(val_validade, 'strftime'):
            dados_linha['Validade'] = val_validade.strftime("%d/%m/%Y")
        else:
            dados_linha['Validade'] = ""

        st.session_state.tag_para_visualizar = dados_linha
        st.session_state.salmao_editor_key += 1 
        # Força rerun GLOBAL para abrir o modal fora do fragmento
        st.rerun()

def render_page(hash_dados, perfil, nome_user):
    if "salmao_editor_key" not in st.session_state:
        st.session_state.salmao_editor_key = 0
    if "tag_para_visualizar" not in st.session_state:
        st.session_state.tag_para_visualizar = None
    if "range_salmao_atual" not in st.session_state:
        st.session_state.range_salmao_atual = None

    st.subheader("🐟 Recebimento de Salmão")
    
    # OTIMIZAÇÃO: Usa a função cacheada (TTL 60s) para métricas globais
    qtd_total, qtd_livre, qtd_gerado, qtd_orc, qtd_reservado, qtd_aberto = db.get_resumo_global_salmao()
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1: components.render_metric_card("📦 Total", qtd_total, "#8b949e")
    with m2: components.render_metric_card("✅ Livre", qtd_livre, "#11734b")
    with m3: components.render_metric_card("✂️ Aberto", qtd_aberto, "#473822")
    with m4: components.render_metric_card("⚙️ Gerado", qtd_gerado, "#ff8500")
    with m5: components.render_metric_card("📝 Orçamento", qtd_orc, "#e8eaed")
    with m6: components.render_metric_card("🔵 Reservado", qtd_reservado, "#0a53a8")

    st.markdown("---")
    msg_acao = "Ver Detalhes" if perfil == "Admin" else "Editar ou Fracionar"
    st.info(f"👆 Clique na caixa da primeira coluna para **{msg_acao}**.")

    with st.container(border=True):
        c_in, c_fim, c_btn = st.columns([1, 1, 2], vertical_alignment="bottom")
        with c_in: tag_start = st.number_input("Tag Inicial", min_value=1, value=1, step=1)
        with c_fim: tag_end = st.number_input("Tag Final", min_value=1, value=200, step=1)
        with c_btn: carregar = st.button("🔍 Carregar Intervalo", type="primary", use_container_width=True)

    if carregar:
        qtd = tag_end - tag_start + 1
        if qtd > 200: st.error("Limite de 200 tags.")
        elif tag_end < tag_start: st.error("Erro no Intervalo.")
        else:
            with st.spinner("Buscando..."):
                # Busca do banco (Função cacheada no database.py)
                st.session_state.salmao_df = db.get_estoque_filtrado(tag_start, tag_end)
                st.session_state.salmao_range_str = f"Tags {tag_start} a {tag_end}"
                st.session_state.range_salmao_atual = (tag_start, tag_end)

    if not st.session_state.salmao_df.empty:
        # CHAMADA DO FRAGMENTO ISOLADO
        # Passamos os dados necessários para o fragmento renderizar a tabela
        painel_tabela_interativa(
            st.session_state.salmao_df, 
            perfil, 
            st.session_state.salmao_range_str
        )

        # Modal é chamado no nível da página (fora do fragmento) para garantir contexto correto
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