"""
Operações de estoque de salmão.
"""
import pandas as pd
import streamlit as st
from datetime import datetime

from core.config import FUSO_BR
from services.database.client import get_db_client
from services.utils import limpar_texto


@st.cache_data(ttl=30, show_spinner=False)
def get_estoque_filtrado(tag_inicio, tag_fim):
    client = get_db_client()
    try:
        response = client.table("estoque_salmao")\
            .select("*")\
            .gte("Tag", tag_inicio)\
            .lte("Tag", tag_fim)\
            .order("Tag")\
            .execute()

        if response.data:
            df = pd.DataFrame(response.data)
            df["Tag"] = pd.to_numeric(df["Tag"], errors='coerce').fillna(0).astype(int)
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0)
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def get_estoque_backup_filtrado(tag_inicio, tag_fim):
    client = get_db_client()
    try:
        response = client.table("estoque_salmao_backup")\
            .select("*")\
            .gte("Tag", tag_inicio)\
            .lte("Tag", tag_fim)\
            .order("Tag")\
            .execute()

        if response.data:
            df = pd.DataFrame(response.data)
            df["Tag"] = pd.to_numeric(df["Tag"], errors='coerce').fillna(0).astype(int)
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0)
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def salvar_alteracoes_estoque(df_novo, usuario_logado):
    client = get_db_client()
    get_estoque_filtrado.clear()
    get_resumo_global_salmao.clear()

    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    registros_para_atualizar = []

    for _, row in df_novo.iterrows():
        dados = {"Tag": int(row["Tag"])}
        changed = False
        colunas_editaveis = ["Calibre", "Peso", "Cliente", "Fornecedor", "Validade", "Status"]
        for col in colunas_editaveis:
            if col in row:
                val = row[col]
                if col == "Status" and isinstance(val, str):
                    val = val.capitalize()
                dados[col] = val
                changed = True
        if changed:
            registros_para_atualizar.append(dados)

    if registros_para_atualizar:
        try:
            client.table("estoque_salmao").upsert(registros_para_atualizar).execute()
            count_updates = len(registros_para_atualizar)
            client.table("logs").insert({
                "DATA_HORA": timestamp,
                "ID_PEDIDO": None,
                "USUARIO": usuario_logado,
                "CAMPO": "EDICAO_ESTOQUE",
                "VALOR_ANTIGO": "-",
                "VALOR_NOVO": f"Atualizou {count_updates} itens"
            }).execute()
        except Exception as e:
            st.error(f"Erro ao salvar estoque: {e}")

    return len(registros_para_atualizar)


def registrar_subtag(id_pai, letra, cliente, peso, status, usuario_logado):
    client = get_db_client()
    dados = {
        "ID_Pai": int(id_pai),
        "Letra": limpar_texto(letra),
        "Cliente": limpar_texto(cliente),
        "Peso": float(peso),
        "Status": status.capitalize(),
        "Calibre_Aux": ""
    }

    try:
        client.table("estoque_subtags").insert(dados).execute()
        timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
        client.table("logs").insert({
            "DATA_HORA": timestamp,
            "USUARIO": usuario_logado,
            "CAMPO": "DESMEMBRAMENTO",
            "VALOR_ANTIGO": f"TAG-{id_pai}",
            "VALOR_NOVO": f"Letra {letra}: {peso}kg"
        }).execute()
        return True
    except Exception as e:
        st.error(f"Erro subtag: {e}")
        return False


def buscar_subtags_por_tag(tag_pai_id):
    client = get_db_client()
    try:
        response = client.table("estoque_subtags")\
            .select("*")\
            .eq("ID_Pai", int(tag_pai_id))\
            .order("Letra")\
            .execute()
        if response.data:
            return pd.DataFrame(response.data)
    except Exception:
        pass
    return pd.DataFrame()


def get_consumo_tag(tag_pai_id):
    client = get_db_client()
    try:
        response = client.table("estoque_subtags").select("*").eq("ID_Pai", int(tag_pai_id)).execute()
        if not response.data:
            return [], 0.0
        df = pd.DataFrame(response.data)
        letras_usadas = df["Letra"].astype(str).str.strip().str.upper().tolist() if "Letra" in df.columns else []
        peso_usado = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0).sum() if "Peso" in df.columns else 0.0
        return letras_usadas, peso_usado
    except Exception:
        return [], 0.0


@st.cache_data(ttl=60, show_spinner=False)
def get_resumo_global_salmao():
    client = get_db_client()
    try:
        response = client.table("estoque_salmao").select("Status").execute()
        dados = response.data
        resp_backup = client.table("estoque_salmao_backup").select("Tag", count="exact", head=True).execute()
        qtd_historico = resp_backup.count if resp_backup.count is not None else 0

        if not dados:
            return 0, 0, qtd_historico, 0, 0, 0

        df = pd.DataFrame(dados)
        s = df["Status"].fillna("Livre").astype(str).str.strip().str.capitalize()
        ativos_gerado = len(s[s == "Gerado"])
        total_gerado_real = ativos_gerado + qtd_historico

        return (
            len(df),
            len(s[s == "Livre"]),
            total_gerado_real,
            len(s[s == "Orçamento"]),
            len(s[s == "Reservado"]),
            len(s[s == "Aberto"])
        )
    except Exception:
        return 0, 0, 0, 0, 0, 0


def arquivar_tags_geradas(ids_tags, usuario_logado="Sistema"):
    if not ids_tags:
        return

    client = get_db_client()
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    dados_reset = {
        "Status": None,
        "Calibre": None,
        "Peso": 0.0,
        "Cliente": None,
        "Fornecedor": None,
        "Validade": None
    }

    try:
        for tag_id in ids_tags:
            resp_pai = client.table("estoque_salmao").select("*").eq("Tag", int(tag_id)).execute()
            if resp_pai.data:
                dados_pai = resp_pai.data[0]
                client.table("estoque_salmao_backup").insert(dados_pai).execute()

            resp_sub = client.table("estoque_subtags").select("*").eq("ID_Pai", int(tag_id)).execute()
            if resp_sub.data:
                client.table("estoque_subtags_backup").insert(resp_sub.data).execute()
                client.table("estoque_subtags").delete().eq("ID_Pai", int(tag_id)).execute()

            client.table("estoque_salmao").update(dados_reset).eq("Tag", int(tag_id)).execute()
            client.table("logs").insert({
                "DATA_HORA": timestamp,
                "USUARIO": usuario_logado,
                "CAMPO": "ARQUIVAMENTO_RESET",
                "VALOR_ANTIGO": f"TAG-{tag_id}",
                "VALOR_NOVO": "Reset Total (Status None)"
            }).execute()

        get_estoque_filtrado.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao processar: {e}")
        return False
