import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
import time
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

def numero_para_coluna(n):
    """Converte 1 -> A, 2 -> B, ... 27 -> AA"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

@st.cache_resource
def get_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
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
            if "429" in str(e): 
                time.sleep(2)
                continue
            else:
                st.error(f"Erro ao conectar no banco de dados: {e}")
                return None
    return None

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

def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido, nr_pedido=""):
    sh = get_connection()
    get_metricas.clear()
    
    ws_respostas = sh.worksheet("Respostas ao formulário 1")
    ws_pedidos = sh.worksheet("Pedidos")
    
    coluna_datas = ws_respostas.col_values(1)
    proxima_linha = len(coluna_datas) + 1
    if proxima_linha < 2: proxima_linha = 2
    
    nova_linha_dados = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        nome,
        descricao.strip(),
        data_entrega.strftime("%d/%m/%Y")
    ]
    range_dados = f"A{proxima_linha}:D{proxima_linha}"
    ws_respostas.update(range_name=range_dados, values=[nova_linha_dados])
    
    time.sleep(1)
    
    # Busca cabeçalhos para localizar colunas
    cabecalhos = [c.upper().strip() for c in ws_pedidos.row_values(1)]
    
    def get_idx(nome, padrao):
        try: return cabecalhos.index(nome) + 1
        except: return padrao

    idx_id = get_idx("ID_PEDIDO", 1)
    idx_pagto = get_idx("PAGAMENTO", 7)
    idx_status = get_idx("STATUS", 10)
    idx_nr = get_idx("NR PEDIDO", 11)
    
    # ID Sequencial = Linha - 1 (Ex: Linha 2 vira ID 1)
    novo_id = proxima_linha - 1
    
    ws_pedidos.update_cell(proxima_linha, idx_id, novo_id)
    ws_pedidos.update_cell(proxima_linha, idx_pagto, pagamento_escolhido)
    ws_pedidos.update_cell(proxima_linha, idx_status, status_escolhido)
    
    if nr_pedido:
        ws_pedidos.update_cell(proxima_linha, idx_nr, nr_pedido)

def corrigir_ids_faltantes(ws, dados):
    """
    Função interna de auto-correção.
    Se detectar IDs vazios, preenche toda a coluna A sequencialmente.
    """
    try:
        cabecalhos = [str(c).upper().strip() for c in dados[0]]
        if "ID_PEDIDO" not in cabecalhos:
            return

        idx_id = cabecalhos.index("ID_PEDIDO") # Índice 0 based (para o dataframe)
        
        # Verifica se há algum ID faltando nas primeiras 20 linhas (amostragem rápida)
        # ou se há "gaps" óbvios
        precisa_corrigir = False
        
        # Converte a coluna de IDs para lista
        coluna_ids = [linha[idx_id] for linha in dados[1:]] # Ignora header
        
        for i, val in enumerate(coluna_ids):
            if not val or val == "" or val == "None":
                precisa_corrigir = True
                break
        
        if precisa_corrigir:
            # Gera lista sequencial: [[1], [2], [3]...]
            qtd_linhas = len(coluna_ids)
            ids_corretos = [[str(i + 1)] for i in range(qtd_linhas)]
            
            # Descobre a letra da coluna (A, B, C...)
            letra_col = numero_para_coluna(idx_id + 1)
            
            # Atualiza no Google Sheets de uma vez só (Batch Update)
            range_update = f"{letra_col}2:{letra_col}{qtd_linhas + 1}"
            ws.update(range_name=range_update, values=ids_corretos)
            
            # Pequeno delay para garantir sincronia
            time.sleep(1)
            return True # Sinaliza que houve correção
            
    except Exception as e:
        print(f"Erro na autocorreção: {e}")
    
    return False

def buscar_pedidos_visualizacao():
    """
    Busca os pedidos e executa a AUTOCORREÇÃO de IDs se necessário.
    """
    sh = get_connection()
    try:
        ws = sh.worksheet("Pedidos")
        dados = ws.get_all_values()
        
        if len(dados) > 1:
            # --- TENTATIVA DE AUTOCORREÇÃO ---
            # Se corrigir, buscamos os dados de novo para mostrar atualizado
            corrigiu = corrigir_ids_faltantes(ws, dados)
            if corrigiu:
                dados = ws.get_all_values() # Recarrega dados atualizados
            # ---------------------------------

            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao ler aba Pedidos: {e}")
        return pd.DataFrame()

def atualizar_pedidos_editaveis(df_editado):
    sh = get_connection()
    ws = sh.worksheet("Pedidos")
    
    cabecalhos_sheet = [c.upper().strip() for c in ws.row_values(1)]
    df_editado.columns = [c.strip().upper() for c in df_editado.columns]
    
    def atualizar_coluna_dinamica(nome_coluna, dados_coluna):
        if nome_coluna in cabecalhos_sheet:
            idx_col = cabecalhos_sheet.index(nome_coluna) + 1
            letra_col = numero_para_coluna(idx_col)
            valores_formatados = [[str(v) if v else ""] for v in dados_coluna]
            range_update = f"{letra_col}2:{letra_col}{len(valores_formatados) + 1}"
            ws.update(range_name=range_update, values=valores_formatados)

    if "PAGAMENTO" in df_editado.columns:
        atualizar_coluna_dinamica("PAGAMENTO", df_editado["PAGAMENTO"].tolist())

    if "STATUS" in df_editado.columns:
        atualizar_coluna_dinamica("STATUS", df_editado["STATUS"].tolist())
        
    if "NR PEDIDO" in df_editado.columns:
        atualizar_coluna_dinamica("NR PEDIDO", df_editado["NR PEDIDO"].tolist())

def criar_novo_cliente(nome, cidade):
    sh = get_connection()
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
    
    sh.batch_update({
        "requests": [{
            "sortRange": {
                "range": {"sheetId": ws.id, "startRowIndex": 1},
                "sortSpecs": [{"dimensionIndex": 1, "sortOrder": "ASCENDING"}]
            }
        }]
    })

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