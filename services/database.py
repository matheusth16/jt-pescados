# services/database.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

ABA_PEDIDOS = "Pedidos"
ABA_CLIENTES = "BaseClientes"

COL_TIMESTAMP = "Data/Hora"
COL_CLIENTE = "Cliente"
COL_DESCRICAO = "Descrição"
COL_DATA_ENTREGA = "Data Entrega"
COL_STATUS = "STATUS"

STATUS_PADRAO = "PENDENTE"


@st.cache_resource
def get_connection():
    """Gerencia a conexão com o Google Sheets"""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        if os.path.exists("credentials.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        else:
            creds_dict = st.secrets["gcp_service_account"]
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

        gc = gspread.authorize(creds)
        return gc.open_by_key(SHEET_ID)
    except Exception as e:
        st.error(f"Erro ao conectar no banco de dados: {e}")
        return None


def _get_ws(nome_aba: str):
    sh = get_connection()
    if not sh:
        return None
    return sh.worksheet(nome_aba)


def _ensure_coluna_status(ws):
    """
    Garante que exista a coluna STATUS no cabeçalho.
    Se não existir, adiciona no final.
    Também garante que linhas antigas sem STATUS fiquem com PENDENTE.
    """
    valores = ws.get_all_values()
    if not valores:
        # Planilha vazia: cria cabeçalho mínimo
        cab = [COL_TIMESTAMP, COL_CLIENTE, COL_DESCRICAO, COL_DATA_ENTREGA, COL_STATUS]
        ws.update("A1", [cab])
        return

    cabecalho = valores[0]
    if COL_STATUS not in cabecalho:
        # Adiciona STATUS no final do cabeçalho
        nova_col_idx = len(cabecalho) + 1
        ws.update_cell(1, nova_col_idx, COL_STATUS)

        # Preenche status padrão nas linhas existentes (a partir da linha 2)
        total_linhas = len(valores)
        if total_linhas >= 2:
            # escreve PENDENTE em todas as linhas existentes
            start_row = 2
            end_row = total_linhas
            # Atualiza em batch numa coluna só
            col_letter = _col_to_letter(nova_col_idx)
            rng = f"{col_letter}{start_row}:{col_letter}{end_row}"
            ws.update(rng, [[STATUS_PADRAO] for _ in range(end_row - start_row + 1)])
        return

    # Se STATUS existe, garante que células vazias virem PENDENTE (opcional, mas útil)
    status_idx = cabecalho.index(COL_STATUS) + 1
    total_linhas = len(valores)
    if total_linhas <= 1:
        return

    # Verifica se há vazios e corrige
    col_vals = ws.col_values(status_idx)
    # col_vals inclui cabeçalho na posição 0
    updates = []
    for i in range(2, total_linhas + 1):
        v = col_vals[i - 1] if (i - 1) < len(col_vals) else ""
        if not v.strip():
            updates.append(gspread.Cell(i, status_idx, STATUS_PADRAO))

    if updates:
        ws.update_cells(updates)


def _col_to_letter(col: int) -> str:
    """1 -> A, 2 -> B, ..."""
    result = ""
    while col:
        col, rem = divmod(col - 1, 26)
        result = chr(65 + rem) + result
    return result


def listar_clientes():
    """Retorna lista de nomes de clientes ordenados"""
    ws = _get_ws(ABA_CLIENTES)
    if not ws:
        return []

    # Pega valores da coluna 2 (Nome), ignora cabeçalho
    nomes = ws.col_values(2)[1:]
    nomes = sorted(list(set([n for n in nomes if n.strip()])))
    return nomes


def salvar_pedido(nome, descricao, data_entrega, status):
    """
    Salva novo pedido na ABA 'Pedidos' com a coluna STATUS.
    """
    ws = _get_ws(ABA_PEDIDOS)
    if not ws:
        raise RuntimeError("Não foi possível acessar a aba 'Pedidos'.")

    # Garante que a coluna STATUS exista
    _ensure_coluna_status(ws)

    # Lê cabeçalho para montar a linha na ordem correta
    cab = ws.row_values(1)
    if not cab:
        cab = [COL_TIMESTAMP, COL_CLIENTE, COL_DESCRICAO, COL_DATA_ENTREGA, COL_STATUS]
        ws.update("A1", [cab])

    # Monta registro base
    registro = {
        COL_TIMESTAMP: datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        COL_CLIENTE: str(nome).strip(),
        COL_DESCRICAO: str(descricao).strip(),
        COL_DATA_ENTREGA: data_entrega.strftime("%d/%m/%Y"),
        COL_STATUS: str(status).strip(),
    }

    # Garante que cabeçalho tenha as colunas mínimas
    for col in [COL_TIMESTAMP, COL_CLIENTE, COL_DESCRICAO, COL_DATA_ENTREGA, COL_STATUS]:
        if col not in cab:
            cab.append(col)
            ws.update_cell(1, len(cab), col)

    # Constrói a linha na ordem do cabeçalho
    nova_linha = [registro.get(col, "") for col in cab]

    # Append no final (não sobrescreve validações existentes no intervalo já configurado)
    ws.append_row(nova_linha, value_input_option="USER_ENTERED")


def buscar_todos_pedidos():
    """Retorna DataFrame com todos os pedidos (aba Pedidos)"""
    ws = _get_ws(ABA_PEDIDOS)
    if not ws:
        return pd.DataFrame()

    # Garante STATUS (para consistência)
    _ensure_coluna_status(ws)

    dados = ws.get_all_values()
    if len(dados) > 1:
        return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame(columns=dados[0] if dados else [])


def atualizar_banco_completo(df_editado: pd.DataFrame):
    """
    Atualiza SOMENTE as células alteradas na aba Pedidos, sem limpar/sobrescrever tudo.

    Observação: considera que df_editado tem as mesmas colunas do cabeçalho da planilha.
    """
    ws = _get_ws(ABA_PEDIDOS)
    if not ws:
        raise RuntimeError("Não foi possível acessar a aba 'Pedidos'.")

    # Estado atual do sheet
    dados_atual = ws.get_all_values()
    if not dados_atual:
        # Se estiver vazio, escreve tudo
        ws.update("A1", [df_editado.columns.tolist()] + df_editado.values.tolist())
        return

    cab_atual = dados_atual[0]
    df_atual = pd.DataFrame(dados_atual[1:], columns=cab_atual)

    # Alinha colunas: se df_editado tiver colunas novas, adiciona ao sheet
    for col in df_editado.columns:
        if col not in cab_atual:
            cab_atual.append(col)
            ws.update_cell(1, len(cab_atual), col)
            df_atual[col] = ""

    # Se o sheet tiver colunas que df_editado não tem, preserva no df_editado
    for col in cab_atual:
        if col not in df_editado.columns:
            df_editado[col] = df_atual[col] if col in df_atual.columns else ""

    # Reordena ambos
    df_editado = df_editado[cab_atual]
    df_atual = df_atual.reindex(columns=cab_atual).fillna("")

    # Ajusta tamanho de linhas: se aumentou, append; se diminuiu, não apaga automaticamente
    # (para não perder histórico acidentalmente). Você pode mudar isso depois.
    n_edit = len(df_editado)
    n_atual = len(df_atual)

    # Garante que df_atual tenha pelo menos n_edit linhas (com vazios)
    if n_edit > n_atual:
        extra = pd.DataFrame([["" for _ in cab_atual]] * (n_edit - n_atual), columns=cab_atual)
        df_atual = pd.concat([df_atual, extra], ignore_index=True)

    # Detecta diferenças e atualiza só o que mudou
    cells_to_update = []
    for r in range(n_edit):
        for c, col in enumerate(cab_atual):
            old = str(df_atual.iloc[r, c]) if r < len(df_atual) else ""
            new = str(df_editado.iloc[r, c])

            if old != new:
                # +2 porque linha 1 é cabeçalho e pandas index começa em 0
                row_num = r + 2
                col_num = c + 1
                cells_to_update.append(gspread.Cell(row_num, col_num, new))

    if cells_to_update:
        ws.update_cells(cells_to_update, value_input_option="USER_ENTERED")


def criar_novo_cliente(nome, cidade):
    """Gera ID automático e salva cliente"""
    ws = _get_ws(ABA_CLIENTES)
    if not ws:
        raise RuntimeError("Não foi possível acessar a aba 'BaseClientes'.")

    coluna_ids = ws.col_values(1)[1:]
    ids_ocupados = {int(x) for x in coluna_ids if x.isdigit()}

    novo_id = 1
    while novo_id in ids_ocupados:
        novo_id += 1

    ws.append_row([novo_id, str(nome).upper(), str(cidade).upper()], value_input_option="USER_ENTERED")


def get_metricas():
    """Retorna totais para o dashboard"""
    sh = get_connection()
    if not sh:
        return 0, 0

    try:
        qtd_clientes = len(sh.worksheet(ABA_CLIENTES).col_values(1)) - 1
    except:
        qtd_clientes = 0

    try:
        qtd_pedidos = len(sh.worksheet(ABA_PEDIDOS).col_values(1)) - 1
    except:
        qtd_pedidos = 0

    return qtd_clientes, qtd_pedidos
