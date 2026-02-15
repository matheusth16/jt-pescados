"""
Modais e componentes visuais da página de salmão.
"""
import streamlit as st
import pandas as pd
import time
from datetime import datetime

import services.database as db
import ui.components as components

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


@st.dialog("🐟 Detalhes da Tag")
def modal_detalhes_tag(row_dict, perfil, nome_user, range_atual):
    tag_id = row_dict.get("Tag")
    status_db = row_dict.get("Status")
    if not status_db or str(status_db).strip() in ["", "None"]:
        status_db = "Livre"

    peso_banco = float(row_dict.get("Peso", 0))
    key_input_peso = f"num_peso_{tag_id}"
    peso_considerado = st.session_state.get(key_input_peso, peso_banco)

    st.markdown(f"### 🏷️ TAG #{tag_id}")

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
        st.markdown(
            f"<span style='background-color:{cor}; color:{cor_txt}; padding: 4px 8px; "
            f"border-radius: 4px; font-weight:bold'>{status_db}</span>",
            unsafe_allow_html=True
        )

    st.divider()

    df_sub = db.buscar_subtags_por_tag(tag_id)
    if not df_sub.empty:
        st.caption("🧱 Histórico de Fracionamento (Subtags)")
        st.dataframe(df_sub, use_container_width=True, hide_index=True)
        st.divider()

    if perfil == "Admin":
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
        opcoes_status = ["Livre", "Reservado", "Orçamento", "Gerado", "Aberto"]
        idx_s = opcoes_status.index(status_db) if status_db in opcoes_status else 0
        novo_status = st.selectbox("Status da Tag:", opcoes_status, index=idx_s, key=f"sel_status_{tag_id}")

        abas_titulos = ["✏️ Editar Dados"]
        if novo_status == "Aberto":
            abas_titulos.insert(0, "✂️ Fracionar (Corte)")

        abas = st.tabs(abas_titulos)

        if novo_status == "Aberto":
            with abas[0]:
                st.info("🔪 Adicione unidades retiradas desta peça.")
                letras_usadas, peso_ja_consumido = db.get_consumo_tag(tag_id)
                saldo = max(0.0, peso_considerado - peso_ja_consumido)

                c_info1, c_info2 = st.columns(2)
                with c_info1:
                    st.metric("Já Usado", f"{peso_ja_consumido:.3f} kg")
                with c_info2:
                    st.metric("Saldo", f"{saldo:.3f} kg")

                with st.form(f"split_{tag_id}"):
                    c_f1, c_f2 = st.columns(2)
                    with c_f1:
                        letra_sug = components.proxima_letra_disponivel(letras_usadas)
                        novo_letra = st.text_input("Letra (Sufixo)", value=letra_sug, max_chars=2)
                    with c_f2:
                        novo_peso_sub = st.number_input(
                            "Peso (kg)", min_value=0.0, max_value=saldo, step=0.1, format="%.3f"
                        )
                    novo_cli_sub = st.text_input("Cliente Destino")

                    if st.form_submit_button("✅ CONFIRMAR UNIDADE", type="primary", use_container_width=True):
                        letra_limpa = novo_letra.strip().upper()

                        if not novo_cli_sub or novo_peso_sub <= 0 or letra_limpa in letras_usadas:
                            st.error("Dados inválidos (Peso zero ou Letra repetida).")
                        else:
                            s_cal_sel = st.session_state.get(f"sel_cal_{tag_id}")
                            s_cal_txt = st.session_state.get(f"txt_cal_{tag_id}")
                            FINAL_CAL = s_cal_txt if s_cal_sel == "Outro" else (s_cal_sel or row_dict.get("Calibre"))

                            s_val_obj = st.session_state.get(f"dt_val_{tag_id}")
                            FINAL_VAL = s_val_obj.strftime("%d/%m/%Y") if s_val_obj else row_dict.get("Validade")

                            FINAL_CLI = st.session_state.get(f"txt_cli_{tag_id}", row_dict.get("Cliente"))
                            FINAL_FORN = st.session_state.get(f"txt_forn_{tag_id}", row_dict.get("Fornecedor"))

                            df_pai_up = pd.DataFrame([{
                                "Tag": tag_id,
                                "Status": novo_status,
                                "Calibre": FINAL_CAL,
                                "Peso": peso_considerado,
                                "Validade": FINAL_VAL,
                                "Cliente": FINAL_CLI,
                                "Fornecedor": FINAL_FORN
                            }])

                            db.salvar_alteracoes_estoque(df_pai_up, nome_user)
                            ok = db.registrar_subtag(tag_id, letra_limpa, novo_cli_sub, novo_peso_sub, "Livre", nome_user)
                            if ok:
                                st.success("Unidade criada e Tag Pai atualizada!")
                                if range_atual:
                                    st.session_state.salmao_df = db.get_estoque_filtrado(range_atual[0], range_atual[1])
                                time.sleep(0.5)
                                st.session_state.salmao_editor_key += 1
                                st.session_state.tag_para_visualizar = None
                                st.rerun()

        with abas[-1]:
            c_e1, c_e2 = st.columns(2)
            with c_e1:
                cal_atual = str(row_dict.get("Calibre", "")).strip().replace("None", "") or ""
                opcoes_calibre = ["8/10", "10/12", "12/14", "14/16", "Outro"]
                if cal_atual in ["8/10", "10/12", "12/14", "14/16"]:
                    idx_cal = opcoes_calibre.index(cal_atual)
                    val_manual_inicial = ""
                else:
                    idx_cal = opcoes_calibre.index("Outro")
                    val_manual_inicial = cal_atual

                sel_calibre = st.selectbox("Calibre", opcoes_calibre, index=idx_cal, key=f"sel_cal_{tag_id}")
                if sel_calibre == "Outro":
                    calibre_final = st.text_input("Digite o Calibre:", value=val_manual_inicial, key=f"txt_cal_{tag_id}")
                else:
                    calibre_final = sel_calibre

            with c_e2:
                m_peso = st.number_input("Peso (kg)", value=peso_banco, format="%.3f", key=f"num_peso_{tag_id}")
                try:
                    d_val = datetime.strptime(str(row_dict.get("Validade")), "%d/%m/%Y")
                except Exception:
                    d_val = datetime.today()
                m_validade = st.date_input("Validade", value=d_val, format="DD/MM/YYYY", key=f"dt_val_{tag_id}")

            m_cli = st.text_input("Cliente", value=str(row_dict.get("Cliente") or "").replace("None", ""), key=f"txt_cli_{tag_id}")
            m_forn = st.text_input("Fornecedor", value=str(row_dict.get("Fornecedor") or "").replace("None", ""), key=f"txt_forn_{tag_id}")
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
                db.salvar_alteracoes_estoque(df_up, nome_user)
                if str(novo_status).strip().upper() == "GERADO":
                    db.arquivar_tags_geradas([tag_id], nome_user)
                    st.toast(f"Tag {tag_id} arquivada como GERADO!")
                st.success("Atualizado com sucesso!")
                if range_atual:
                    st.session_state.salmao_df = db.get_estoque_filtrado(range_atual[0], range_atual[1])
                time.sleep(0.5)
                st.session_state.salmao_editor_key += 1
                st.session_state.tag_para_visualizar = None
                st.rerun()
