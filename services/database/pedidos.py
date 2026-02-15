"""
Operações de pedidos.
"""
import pandas as pd
import streamlit as st
from datetime import datetime

from core.config import FUSO_BR
from services.database.client import get_db_client, get_max_id
from services.database.clientes import listar_clientes, get_metricas
from services.utils import limpar_texto

# Limites para performance
_LIMITE_PEDIDOS_FILTROS = 5000
_LIMITE_DASHBOARD = 5000


@st.cache_data(ttl=300, show_spinner=False)
def listar_dados_filtros():
    client = get_db_client()
    try:
        response = (
            client.table("pedidos")
            .select("CIDADE, ROTA")
            .order("ID_PEDIDO", desc=True)
            .limit(_LIMITE_PEDIDOS_FILTROS)
            .execute()
        )
        if response.data:
            df = pd.DataFrame(response.data)
            cidades = sorted([str(x) for x in df["CIDADE"].unique() if x and str(x).strip() != ''])
            rotas = sorted([str(x) for x in df["ROTA"].unique() if x and str(x).strip() != ''])
            return cidades, rotas
    except Exception:
        pass
    return [], []


@st.cache_data(ttl=300, show_spinner=False)
def buscar_pedidos_visualizacao(_hash_versao=None, _limite=None):
    limite = _limite if _limite is not None else _LIMITE_DASHBOARD
    client = get_db_client()
    try:
        cols = 'ID_PEDIDO, STATUS, PAGAMENTO, "DIA DA ENTREGA", "NOME CLIENTE"'
        response = (
            client.table("pedidos")
            .select(cols)
            .order("ID_PEDIDO", desc=True)
            .limit(limite)
            .execute()
        )
        if response.data:
            return pd.DataFrame(response.data)
    except Exception:
        pass
    return pd.DataFrame()


def obter_resumo_historico(nome_cliente, limite=5):
    if not nome_cliente:
        return []

    client = get_db_client()
    try:
        nome_alvo = limpar_texto(nome_cliente)
        cols = 'ID_PEDIDO, "DIA DA ENTREGA", STATUS, PEDIDO, OBSERVAÇÃO, PAGAMENTO, "NOME CLIENTE"'
        response = client.table("pedidos")\
            .select(cols)\
            .eq("NOME CLIENTE", nome_alvo)\
            .order("ID_PEDIDO", desc=True)\
            .limit(limite)\
            .execute()

        if not response.data:
            return []

        df_cli = pd.DataFrame(response.data)
        historico = []
        for _, row in df_cli.iterrows():
            data_str = "-"
            val_data = row.get("DIA DA ENTREGA")
            if pd.notnull(val_data):
                data_str = str(val_data)
            desc = row.get("PEDIDO") or row.get("OBSERVAÇÃO") or "Sem descrição"
            item = {
                "id": row.get("ID_PEDIDO", "?"),
                "data": data_str,
                "status": row.get("STATUS", "Desconhecido"),
                "descricao": str(desc),
                "pagamento": row.get("PAGAMENTO", "-")
            }
            historico.append(item)
        return historico
    except Exception:
        return []


def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido, observacao="", nr_pedido="", usuario_logado="Sistema"):
    client = get_db_client()
    get_metricas.clear()
    listar_clientes.clear()
    buscar_pedidos_visualizacao.clear()
    listar_dados_filtros.clear()

    nome_final = limpar_texto(nome)
    obs_final = limpar_texto(observacao)
    nr_final = limpar_texto(nr_pedido)
    desc_final = descricao.strip()
    data_entrega_str = data_entrega.strftime("%d/%m/%Y")
    data_log = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")

    novo_id = get_max_id("pedidos", "ID_PEDIDO") + 1

    cod_cliente = None
    cidade_dest = "NÃO DEFINIDO"
    rota_dest = "RETIRADA CD"

    try:
        resp_cli = client.table("clientes").select('"Código", "Nome Cidade", ROTA').eq("Cliente", nome).execute()
        if resp_cli.data:
            d = resp_cli.data[0]
            cod_cliente = d.get("Código")
            cidade_dest = d.get("Nome Cidade") or "NÃO DEFINIDO"
            rota_dest = d.get("ROTA") or "RETIRADA CD"
    except Exception:
        pass

    dados_pedido = {
        "ID_PEDIDO": novo_id,
        "CARIMBO DE DATA/HORA": data_log,
        "COD CLIENTE": cod_cliente,
        "NOME CLIENTE": nome_final,
        "PEDIDO": desc_final,
        "DIA DA ENTREGA": data_entrega_str,
        "PAGAMENTO": pagamento_escolhido,
        "STATUS": status_escolhido,
        "NR PEDIDO": nr_final,
        "OBSERVAÇÃO": obs_final,
        "CIDADE": cidade_dest,
        "ROTA": rota_dest
    }

    try:
        client.table("pedidos").insert(dados_pedido).execute()
        client.table("logs").insert({
            "DATA_HORA": data_log,
            "ID_PEDIDO": novo_id,
            "USUARIO": str(usuario_logado),
            "CAMPO": "CRIAÇÃO",
            "VALOR_ANTIGO": "-",
            "VALOR_NOVO": f"Status: {status_escolhido}"
        }).execute()
    except Exception as e:
        raise Exception(f"Erro ao salvar no Supabase: {e}")


def atualizar_pedidos_editaveis(df_editado, usuario_logado="Sistema"):
    client = get_db_client()
    if df_editado.empty:
        return

    buscar_pedidos_visualizacao.clear()
    colunas_check = ["STATUS", "PAGAMENTO", "NR PEDIDO", "OBSERVAÇÃO"]

    if "ID_PEDIDO" not in df_editado.columns:
        st.error("ID_PEDIDO não encontrado na edição.")
        return

    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")

    for _, row in df_editado.iterrows():
        pid = row["ID_PEDIDO"]
        try:
            cols = 'ID_PEDIDO, STATUS, PAGAMENTO, "NR PEDIDO", OBSERVAÇÃO'
            resp = client.table("pedidos").select(cols).eq("ID_PEDIDO", pid).execute()
            if not resp.data:
                continue

            atual_db = resp.data[0]
            updates = {}
            logs_batch = []

            for col in colunas_check:
                if col in row:
                    val_novo = str(row[col]) if row[col] is not None else ""
                    val_novo = val_novo.strip()
                    if col in ["STATUS", "PAGAMENTO"]:
                        val_novo = val_novo.upper()
                    val_antigo = str(atual_db.get(col, ""))
                    val_antigo_limpo = val_antigo.strip()

                    if col == "NR PEDIDO" and val_antigo_limpo != "":
                        continue

                    if val_novo != val_antigo:
                        updates[col] = val_novo
                        logs_batch.append({
                            "DATA_HORA": timestamp,
                            "ID_PEDIDO": pid,
                            "USUARIO": usuario_logado,
                            "CAMPO": col,
                            "VALOR_ANTIGO": val_antigo,
                            "VALOR_NOVO": val_novo
                        })

            if updates:
                client.table("pedidos").update(updates).eq("ID_PEDIDO", pid).execute()
                if logs_batch:
                    client.table("logs").insert(logs_batch).execute()
        except Exception as e:
            print(f"Erro ao atualizar pedido {pid}: {e}")


def buscar_pedidos_paginado(pagina_atual=1, tamanho_pagina=20, filtros=None):
    client = get_db_client()
    inicio = (pagina_atual - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina - 1

    try:
        cols = 'ID_PEDIDO, "COD CLIENTE", "NOME CLIENTE", CIDADE, STATUS, "DIA DA ENTREGA", PEDIDO, PAGAMENTO, "NR PEDIDO", OBSERVAÇÃO, ROTA'
        query = client.table("pedidos").select(cols, count="exact")

        if filtros:
            if filtros.get("status") and len(filtros["status"]) > 0:
                query = query.in_("STATUS", filtros["status"])
            if filtros.get("cidade") and len(filtros["cidade"]) > 0:
                query = query.in_("CIDADE", filtros["cidade"])
            if filtros.get("rota") and len(filtros["rota"]) > 0:
                query = query.in_("ROTA", filtros["rota"])

        response = query.order("ID_PEDIDO", desc=True).range(inicio, fim).execute()
        total_registros = response.count if response.count is not None else 0
        df = pd.DataFrame(response.data)

        if df.empty:
            df = pd.DataFrame(columns=[
                "ID_PEDIDO", "COD CLIENTE", "NOME CLIENTE", "CIDADE",
                "STATUS", "DIA DA ENTREGA", "PEDIDO", "PAGAMENTO",
                "NR PEDIDO", "OBSERVAÇÃO", "ROTA"
            ])

        return df, total_registros
    except Exception as e:
        st.error(f"Erro na paginação: {e}")
        return pd.DataFrame(), 0
