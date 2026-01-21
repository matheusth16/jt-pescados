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
    try:
        ws = sh.worksheet("BaseClientes")
        # Pega valores da coluna 2 (Nomes), ignora cabeçalho
        nomes = sorted(list(set(ws.col_values(2)[1:])))
        return nomes
    except:
        return []

def get_dados_cliente(nome_cliente):
    """Busca ID e Cidade do cliente para preencher a tabela de Pedidos"""
    sh = get_connection()
    if not sh: return "", ""
    try:
        ws = sh.worksheet("BaseClientes")
        dados = ws.get_all_records() # Retorna lista de dicionários
        
        # Procura o cliente na lista (case insensitive se possível, mas aqui exato)
        for row in dados:
            if str(row.get("NOME CLIENTE", "")).upper() == str(nome_cliente).upper():
                return row.get("COD CLIENTE", ""), row.get("CIDADE", "")
        return "", "" # Não achou
    except:
        return "", ""

def salvar_pedido(nome, descricao, data_entrega, status_inicial):
    """
    Salva em dois lugares:
    1. Aba de Respostas (Log bruto)
    2. Aba de Pedidos (Painel de Gestão) com colunas dinâmicas
    """
    sh = get_connection()
    
    # 1. Salvar na aba de Log (Respostas ao formulário 1)
    # Tenta achar a aba pelo nome padrão ou pega a primeira
    try:
        ws_log = sh.worksheet("Respostas ao formulário 1")
    except:
        ws_log = sh.sheet1
        
    proxima_linha_log = len(ws_log.col_values(1)) + 1
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    nova_linha_log = [
        timestamp,
        nome,
        descricao,
        data_entrega.strftime("%d/%m/%Y")
    ]
    ws_log.insert_row(nova_linha_log, index=proxima_linha_log)
    
    # 2. Salvar na aba de Gestão (Pedidos)
    try:
        ws_gestao = sh.worksheet("Pedidos")
        headers = ws_gestao.row_values(1) # Lê a primeira linha (cabeçalhos)
        
        # Prepara uma linha vazia do tamanho dos cabeçalhos
        nova_linha_gestao = [""] * len(headers)
        
        # Busca dados extras do cliente
        cod_cliente, cidade_cliente = get_dados_cliente(nome)
        
        # Mapeamento Dinâmico: Preenche baseado no nome da coluna
        mapa_dados = {
            "COD CLIENTE": cod_cliente,
            "NOME CLIENTE": nome,
            "CIDADE": cidade_cliente,
            "PEDIDO": descricao,
            "DIA DA ENTREGA": data_entrega.strftime("%d/%m/%Y"),
            "STATUS": status_inicial,
            "CARIMBO DE DATA/HORA": timestamp, # Caso tenha essa coluna
            "ROTA": "" # Deixa em branco para preencher depois
        }
        
        # Preenche o vetor na posição correta
        for col_nome, valor in mapa_dados.items():
            # Tenta achar a coluna no cabeçalho (ignorando maiúsculas/minúsculas)
            indices = [i for i, h in enumerate(headers) if str(h).upper().strip() == col_nome.upper().strip()]
            if indices:
                nova_linha_gestao[indices[0]] = valor
        
        # Adiciona a linha preenchida na aba Pedidos
        ws_gestao.append_row(nova_linha_gestao)
        
    except Exception as e:
        # Se falhar na aba Pedidos (ex: aba não existe), não trava o app, mas avisa no console
        print(f"Aviso: Não foi possível salvar na aba Pedidos. Erro: {e}")

def buscar_todos_pedidos():
    """Retorna DataFrame da aba PEDIDOS para o Data Editor"""
    sh = get_connection()
    try:
        ws = sh.worksheet("Pedidos")
        dados = ws.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def atualizar_banco_completo(df):
    """Sobrescreve a planilha PEDIDOS com os dados editados"""
    sh = get_connection()
    ws = sh.worksheet("Pedidos")
    ws.clear()
    novos_dados = [df.columns.tolist()] + df.values.tolist()
    ws.update(range_name="A1", values=novos_dados)

def criar_novo_cliente(nome, cidade):
    """Gera ID automático e salva cliente na BaseClientes"""
    sh = get_connection()
    ws = sh.worksheet("BaseClientes")
    
    coluna_ids = ws.col_values(1)[1:] # Assume ID na coluna 1
    # Filtra apenas números válidos
    ids_ocupados = set()
    for x in coluna_ids:
        if str(x).isdigit():
            ids_ocupados.add(int(x))
            
    novo_id = 1
    while novo_id in ids_ocupados:
        novo_id += 1
    
    # Assume ordem: ID, NOME, CIDADE
    ws.append_row([novo_id, nome.upper(), cidade.upper()])

def get_metricas():
    """Retorna totais para o dashboard"""
    sh = get_connection()
    if not sh: return 0, 0
    
    try:
        qtd_clientes = len(sh.worksheet("BaseClientes").col_values(2)) - 1
    except:
        qtd_clientes = 0
        
    try:
        # Conta pedidos na aba de Gestão
        qtd_pedidos = len(sh.worksheet("Pedidos").col_values(1)) - 1
    except:
        # Fallback para aba de respostas
        qtd_pedidos = len(sh.sheet1.col_values(1)) - 1
        
    return qtd_clientes, qtd_pedidos
