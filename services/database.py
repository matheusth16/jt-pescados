import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

# Removemos o cache para garantir que a conexão sempre pegue dados frescos
def get_connection():
    """Gerencia a conexão com o Google Sheets"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
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

def listar_clientes():
    sh = get_connection()
    if not sh: return []
    try:
        ws = sh.worksheet("BaseClientes")
        # Pega valores da coluna 2, ignora cabeçalho
        col_valores = ws.col_values(2)
        if len(col_valores) > 1:
            nomes = sorted(list(set(col_valores[1:])))
            return nomes
        return []
    except:
        return []

def salvar_pedido(nome, descricao, data_entrega, status_escolhido):
    """
    Salva o pedido calculando manualmente a próxima linha vazia
    para evitar sobrescrita de dados.
    """
    sh = get_connection()
    
    ws_respostas = sh.worksheet("Respostas ao formulário 1")
    ws_pedidos = sh.worksheet("Pedidos")
    
    # 1. FORÇA BRUTA: Conta quantas linhas têm na Coluna A (Data)
    # Isso garante que pegamos a última posição real
    coluna_datas = ws_respostas.col_values(1)
    
    # Se tiver cabeçalho e dados, o tamanho será > 1. 
    # A próxima linha é sempre o tamanho atual + 1.
    proxima_linha = len(coluna_datas) + 1
    
    # Validação extra de segurança: se por acaso a linha calculada for 1 ou 2 e já tiver gente lá
    if proxima_linha < 2: 
        proxima_linha = 2
    
    # 2. Preparar dados
    nova_linha_dados = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        nome,
        descricao.strip(),
        data_entrega.strftime("%d/%m/%Y")
    ]
    
    # 3. Gravar na aba Respostas usando RANGE ESPECÍFICO (Sem adivinhação)
    # Ex: Atualiza o range A5:D5 com os dados
    range_dados = f"A{proxima_linha}:D{proxima_linha}"
    ws_respostas.update(range_name=range_dados, values=[nova_linha_dados])
    
    # 4. Gravar o Status na aba Pedidos na MESMA linha
    # Coluna H é a 8ª coluna
    ws_pedidos.update_cell(proxima_linha, 8, status_escolhido)

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

def atualizar_apenas_status(df_editado):
    sh = get_connection()
    ws = sh.worksheet("Pedidos")
    
    # Tenta achar a coluna de status
    col_status = "STATUS" if "STATUS" in df_editado.columns else "Status"
    
    # Pega todos os status da tabela editada
    lista_status = [[s] for s in df_editado[col_status].tolist()]
    
    num_linhas = len(lista_status)
    
    # Começa da linha 2 (pula cabeçalho) até o fim da lista
    intervalo = f"H2:H{num_linhas + 1}"
    
    ws.update(range_name=intervalo, values=lista_status)

def criar_novo_cliente(nome, cidade):
    sh = get_connection()
    ws = sh.worksheet("BaseClientes")
    
    coluna_ids = ws.col_values(1)
    # Lógica segura para ID
    ids_ocupados = set()
    for x in coluna_ids:
        if x.isdigit():
            ids_ocupados.add(int(x))
            
    novo_id = 1
    while novo_id in ids_ocupados:
        novo_id += 1
    
    ws.append_row([novo_id, nome.upper(), cidade.upper()])

def get_metricas():
    sh = get_connection()
    if not sh: return 0, 0
    try:
        ws_clientes = sh.worksheet("BaseClientes")
        ws_pedidos = sh.worksheet("Pedidos")
        
        # Subtrai 1 do cabeçalho, garantindo que não dê negativo
        qtd_clientes = max(0, len(ws_clientes.col_values(1)) - 1)
        qtd_pedidos = max(0, len(ws_pedidos.col_values(1)) - 1)
        
        return qtd_clientes, qtd_pedidos
    except:
        return 0, 0