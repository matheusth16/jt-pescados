# ui/pages/gerenciar_edicao.py
import streamlit as st
import pandas as pd
import time

import services.database as db
import ui.styles as styles
import ui.components as components

from core.config import LISTA_STATUS, LISTA_PAGAMENTO, PALETA_CORES


def _normalizar_df(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza colunas (maiúsculas) e garante que existe ID_PEDIDO."""
    if df is None or df.empty:
        return pd.DataFrame()

    out = df.copy()
    out.columns = [c.upper().strip() for c in out.columns]

    # Alguns lugares podem vir com "ID" / "ID PEDIDO" etc.
    if "ID_PEDIDO" not in out.columns:
        possiveis = [c for c in out.columns if c.replace(" ", "_") in ("ID_PEDIDO", "IDPEDIDO")]
        if possiveis:
            out.rename(columns={possiveis[0]: "ID_PEDIDO"}, inplace=True)

    return out


def _carregar_pedido_por_id(pedido_id) -> dict | None:
    """Carrega um pedido único pelo ID a partir do dataset de visualização."""
    try:
        df = db.buscar_pedidos_visualizacao()
    except Exception:
        return None

    df = _normalizar_df(df)
    if df.empty or "ID_PEDIDO" not in df.columns:
        return None

    # Normaliza o tipo do ID para comparação
    try:
        pid = int(pedido_id)
        df["ID_PEDIDO"] = pd.to_numeric(df["ID_PEDIDO"], errors="coerce")
        linha = df[df["ID_PEDIDO"] == pid]
    except Exception:
        linha = df[df["ID_PEDIDO"].astype(str) == str(pedido_id)]

    if linha.empty:
        return None

    # retorna a primeira ocorrência
    return linha.iloc[0].to_dict()


def _voltar_para_tabela_op():
    """
    Volta para a tela de Operações (tabela do Gerenciar) no seu roteador manual (app.py).
    """
    # limpa seleção do pedido
    st.session_state.pop("pedido_para_visualizar", None)
    st.session_state.pop("pedido_id_edicao", None)

    # limpa rota interna da edição (se você usa no app.py)
    st.session_state["nav_page"] = None

    # força o menu voltar para Operações (OP)
    st.session_state["navegacao_principal"] = "🚚 Operações"

    # opcional: volta para página 1 da tabela
    if "pag_atual_gerenciar" in st.session_state:
        st.session_state["pag_atual_gerenciar"] = 1

    st.rerun()


def render_page(hash_dados, perfil, nome_user):
    """
    Página dedicada de edição (somente OP).

    Espera receber o pedido selecionado via session_state em:
      - st.session_state["pedido_para_visualizar"]  (Series/dict do gerenciar.py)
        OU
      - st.session_state["pedido_id_edicao"]        (int/str)

    Regra de negócio:
      OP pode editar: Status, Pagamento, Observação e NR Pedido APENAS se estiver vazio.
    """

    # CSS global
    styles.aplicar_estilos(perfil)

    # --- Segurança: somente OP ---
    if perfil == "Admin":
        st.error("⛔ Acesso negado. Esta tela é exclusiva para OP (edição).")
        if st.button("⬅️ Voltar", use_container_width=True):
            # volta para Gerenciar (Admin)
            st.session_state.pop("pedido_para_visualizar", None)
            st.session_state.pop("pedido_id_edicao", None)
            st.session_state["nav_page"] = None
            st.session_state["navegacao_principal"] = "👁️ Gerenciar"
            st.rerun()
        return

    st.markdown("### ✏️ Edição de Pedido (OP)")
    st.caption("Você pode alterar: **Status, Pagamento, Observação** e **NR Pedido (apenas se estiver vazio)**.")
    st.markdown("---")

    # --- Identifica o pedido vindo da tela anterior ---
    pedido_row = None

    if "pedido_para_visualizar" in st.session_state and st.session_state.pedido_para_visualizar is not None:
        raw = st.session_state.pedido_para_visualizar
        if hasattr(raw, "to_dict"):
            pedido_row = raw.to_dict()
        elif isinstance(raw, dict):
            pedido_row = raw

    if pedido_row is None and "pedido_id_edicao" in st.session_state and st.session_state.pedido_id_edicao:
        pedido_row = _carregar_pedido_por_id(st.session_state.pedido_id_edicao)

    # Fallback: permite buscar pelo ID caso entre direto na página
    if pedido_row is None:
        st.warning("Nenhum pedido foi selecionado. Informe o ID do pedido para editar.")
        pid = st.text_input("ID do Pedido", placeholder="Ex.: 123")

        c_buscar, c_voltar = st.columns(2)
        with c_buscar:
            if st.button("🔎 Buscar", use_container_width=True):
                if pid.strip():
                    pedido_row = _carregar_pedido_por_id(pid.strip())
                    if pedido_row is None:
                        st.error("Pedido não encontrado.")
                    else:
                        st.session_state["pedido_id_edicao"] = pid.strip()
                        st.rerun()
                else:
                    st.error("Informe um ID válido.")

        with c_voltar:
            if st.button("⬅️ Voltar", use_container_width=True):
                _voltar_para_tabela_op()
        return

    # Padroniza keys para bater com o resto do sistema
    pedido_row = {str(k).upper().strip(): v for k, v in pedido_row.items()}

    pedido_id = pedido_row.get("ID_PEDIDO", pedido_row.get("ID", ""))
    cliente = pedido_row.get("NOME CLIENTE", pedido_row.get("CLIENTE", ""))
    cidade = pedido_row.get("CIDADE", "")
    rota = pedido_row.get("ROTA", "")
    entrega = pedido_row.get("DIA DA ENTREGA", pedido_row.get("ENTREGA", "-"))

    val_status_atual = pedido_row.get("STATUS", "-")
    val_pagamento_atual = pedido_row.get("PAGAMENTO", "-")
    val_nr_atual = pedido_row.get("NR PEDIDO", "")
    val_obs_atual = pedido_row.get("OBSERVAÇÃO", "")

    if pd.isna(val_nr_atual): val_nr_atual = ""
    if pd.isna(val_obs_atual): val_obs_atual = ""

    # --- Header do pedido ---
    st.markdown(f"#### 🆔 Pedido #{pedido_id}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**👤 Cliente**")
        st.write(cliente)
    with c2:
        st.markdown("**📍 Cidade**")
        st.write(cidade)
    with c3:
        st.markdown("**🚚 Rota**")
        st.write(rota)
    with c4:
        st.markdown("**📅 Entrega**")
        st.write(entrega)

    st.markdown("---")
    st.warning("📝 **ITENS DO PEDIDO:**")
    st.markdown(f"#### {pedido_row.get('PEDIDO', 'Sem itens descritos')}")

    st.markdown("---")

    # --- Formulário de edição ---
    with st.form("form_edicao_op"):
        c_edit1, c_edit2 = st.columns(2)

        idx_stt = LISTA_STATUS.index(val_status_atual) if val_status_atual in LISTA_STATUS else 0
        idx_pg = LISTA_PAGAMENTO.index(val_pagamento_atual) if val_pagamento_atual in LISTA_PAGAMENTO else 0

        with c_edit1:
            novo_status = st.selectbox("Status:", LISTA_STATUS, index=idx_stt)
            # dica visual do status
            cor_st = PALETA_CORES["STATUS"].get(str(novo_status).strip(), None)
            if cor_st:
                st.markdown(
                    f"<div style='margin-top:-6px; font-weight:700; color:{cor_st};'>● {novo_status}</div>",
                    unsafe_allow_html=True
                )

        with c_edit2:
            novo_pg = st.selectbox("Pagamento:", LISTA_PAGAMENTO, index=idx_pg)

        st.markdown("")

        # Regra: NR Pedido só edita se estiver vazio
        nr_pedido_pode_editar = (str(val_nr_atual).strip() == "")
        if nr_pedido_pode_editar:
            novo_nr = st.text_input("NR Pedido (preencher uma vez):", value="")
            st.caption("⚠️ Depois de preenchido, não poderá ser alterado pelo OP.")
        else:
            novo_nr = st.text_input("NR Pedido (travado):", value=str(val_nr_atual), disabled=True)
            st.caption("🔒 NR Pedido já foi definido e não pode ser alterado pelo OP.")

        nova_obs = st.text_area("Observação:", value=str(val_obs_atual), height=120)

        st.markdown("")

        c_salvar, c_cancelar = st.columns(2)
        with c_salvar:
            salvar = st.form_submit_button("💾 SALVAR", type="primary", use_container_width=True)
        with c_cancelar:
            cancelar = st.form_submit_button("⬅️ VOLTAR", use_container_width=True)

    # --- Ações ---
    if cancelar:
        _voltar_para_tabela_op()

    if salvar:
        # Regra do NR Pedido:
        nr_final = str(novo_nr).strip() if nr_pedido_pode_editar else str(val_nr_atual).strip()

        df_update = pd.DataFrame([{
            "ID_PEDIDO": pedido_id,
            "STATUS": novo_status,
            "PAGAMENTO": novo_pg,
            "NR PEDIDO": nr_final,
            "OBSERVAÇÃO": str(nova_obs).strip()
        }])

        try:
            db.atualizar_pedidos_editaveis(df_update, usuario_logado=nome_user)

            # limpa cache de dados caso você use @st.cache_data em fetchs
            try:
                st.cache_data.clear()
            except Exception:
                pass

            st.success("✅ Pedido atualizado com sucesso!")
            time.sleep(0.6)

            # volta para a tabela
            _voltar_para_tabela_op()

        except Exception as e:
            st.error(f"Erro ao atualizar: {e}")
