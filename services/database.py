import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
import time
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

@st.cache_resource
def get_connection():
    """
    Gerencia a conexão com o Google Sheets com Cache e Tentativas (Retry).
    O Cache evita re-autenticar a cada clique.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Tenta conectar até 3 vezes se der erro de "Quota"
    for tentativa in range(3):
        try:
            if os.path.exists("credentials.json"):
                creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            else:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            
            gc = gspread.authorize(creds)
            return gc.open_by_key(SHEET_ID)
        except Exception as e:
            if "429" in str(e): # Se for erro de cota, espera e tenta de novo
                time.sleep(2)
                continue
            else:
                st.error(f"Erro ao conectar no banco de dados: {e}")
                return None
    return None

# Cache de 5 minutos (300s) para a lista de clientes.
# Não precisamos ler isso a todo segundo.
@st.cache_data(ttl=300)
def listar_clientes():
    sh = get_connection()
    if not sh: return []
    try:
        ws = sh.worksheet("BaseClientes")
        col_valores = ws.col_values(2)
        if len(col_valores) > 1:
            nomes = sorted(list(set(col_valores[1:])))
            return nomes
        return []
    except:
        return []

def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido):
    """
    Salva dados na aba Respostas e injeta Pagamento (Col F) e Status (Col I)
    """
    sh = get_connection()
    # Limpa o cache das métricas para atualizar o número de pedidos na hora
    get_metricas.clear()
    
    ws_respostas = sh.worksheet("Respostas ao formulário 1")
    ws_pedidos = sh.worksheet("Pedidos")
    
    # 1. FORÇA BRUTA: Conta linhas pela coluna A da aba Respostas
    coluna_datas = ws_respostas.col_values(1)
    proxima_linha = len(coluna_datas) + 1
    if proxima_linha < 2: proxima_linha = 2
    
    # 2. Prepara e salva dados na aba Respostas
    nova_linha_dados = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        nome,
        descricao.strip(),
        data_entrega.strftime("%d/%m/%Y")
    ]
    range_dados = f"A{proxima_linha}:D{proxima_linha}"
    ws_respostas.update(range_name=range_dados, values=[nova_linha_dados])
    
    # Pequena pausa para o Google respirar
    time.sleep(1)
    
    # 3. Grava Pagamento e Status na aba Pedidos (Linha exata)
    # Coluna F = 6 (Pagamento)
    # Coluna I = 9 (Status)
    ws_pedidos.update_cell(proxima_linha, 6, pagamento_escolhido)
    ws_pedidos.update_cell(proxima_linha, 9, status_escolhido)

def buscar_pedidos_visualizacao():
    sh = get_connection()
    try:
        ws = sh.worksheet("Pedidos")
        dados = ws.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler aba Pedidos: {e}")
        return pd.DataFrame()

def atualizar_pedidos_editaveis(df_editado):
    """
    Atualiza as colunas de PAGAMENTO (F) e STATUS (I) em lote
    """
    sh = get_connection()
    ws = sh.worksheet("Pedidos")
    
    # Normaliza nomes das colunas
    df_editado.columns = [c.strip().upper() for c in df_editado.columns]
    
    # Prepara dados do Pagamento
    col_pagto = "PAGAMENTO" if "PAGAMENTO" in df_editado.columns else None
    if col_pagto:
        lista_pagto = [[p] for p in df_editado[col_pagto].tolist()]
        range_pagto = f"F2:F{len(lista_pagto) + 1}"
        ws.update(range_name=range_pagto, values=lista_pagto)

    # Prepara dados do Status
    col_status = "STATUS" if "STATUS" in df_editado.columns else None
    if col_status:
        lista_status = [[s] for s in df_editado[col_status].tolist()]
        range_status = f"I2:I{len(lista_status) + 1}"
        ws.update(range_name=range_status, values=lista_status)

def criar_novo_cliente(nome, cidade):
    sh = get_connection()
    # Limpa o cache de clientes para o novo nome aparecer na lista imediatamente
    listar_clientes.clear()
    get_metricas.clear()
    
    ws = sh.worksheet("BaseClientes")
    
    coluna_ids = ws.col_values(1)
    ids_ocupados = set()
    for x in coluna_ids:
        if x.isdigit():
            ids_ocupados.add(int(x))
    novo_id = 1
    while novo_id in ids_ocupados:
        novo_id += 1
    
    ws.append_row([novo_id, nome.upper(), cidade.upper()])
    
    # Ordenação Automática A-Z
    sh.batch_update({
        "requests": [{
            "sortRange": {
                "range": {"sheetId": ws.id, "startRowIndex": 1},
                "sortSpecs": [{"dimensionIndex": 1, "sortOrder": "ASCENDING"}]
            }
        }]
    })

# Cache de 30 segundos para as métricas.
# Assim o sidebar não trava o sistema.
@st.cache_data(ttl=30)
def get_metricas():
    sh = get_connection()
    if not sh: return 0, 0
    try:
        ws_clientes = sh.worksheet("BaseClientes")
        ws_pedidos = sh.worksheet("Pedidos")
        qtd_clientes = max(0, len(ws_clientes.col_values(1)) - 1)
        qtd_pedidos = max(0, len(ws_pedidos.col_values(1)) - 1)
        return qtd_clientes, qtd_pedidos
    except:
        return 0, 0