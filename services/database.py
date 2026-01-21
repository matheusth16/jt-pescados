# services/database.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

@st.cache_resource
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
    """Retorna lista de nomes de clientes ordenados"""
    sh = get_connection()
    if not sh: return []
    ws = sh.worksheet("BaseClientes")
    # Pega valores da coluna 2, ignora cabeçalho, remove duplicatas e ordena
    nomes = sorted(list(set(ws.col_values(2)[1:])))
    return nomes

def salvar_pedido(nome, descricao, data_entrega):
    """Lógica para salvar novo pedido"""
    sh = get_connection()
    ws = sh.sheet1
    
    proxima_linha = len(ws.col_values(1)) + 1
    nova_linha = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        nome,
        descricao,
        data_entrega.strftime("%d/%m/%Y")
    ]
    ws.insert_row(nova_linha, index=proxima_linha)

def buscar_todos_pedidos():
    """Retorna DataFrame com todos os pedidos para o Data Editor"""
    sh = get_connection()
    ws = sh.sheet1
    dados = ws.get_all_values()
    if len(dados) > 1:
        return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

def atualizar_banco_completo(df):
    """Sobrescreve a planilha com os dados editados"""
    sh = get_connection()
    ws = sh.sheet1
    ws.clear()
    novos_dados = [df.columns.tolist()] + df.values.tolist()
    ws.update(range_name="A1", values=novos_dados)

def criar_novo_cliente(nome, cidade):
    """Gera ID automático e salva cliente"""
    sh = get_connection()
    ws = sh.worksheet("BaseClientes")
    
    coluna_ids = ws.col_values(1)[1:]
    ids_ocupados = {int(x) for x in coluna_ids if x.isdigit()}
    
    novo_id = 1
    while novo_id in ids_ocupados:
        novo_id += 1
    
    ws.append_row([novo_id, nome.upper(), cidade.upper()])

def get_metricas():
    """Retorna totais para o dashboard"""
    sh = get_connection()
    if not sh: return 0, 0
    
    # Exemplo de otimização: não precisa ler tudo se a API permitir contagem metadata
    # mas mantendo simples:
    qtd_clientes = len(sh.worksheet("BaseClientes").col_values(1)) - 1
    qtd_pedidos = len(sh.sheet1.col_values(1)) - 1
    return qtd_clientes, qtd_pedidos