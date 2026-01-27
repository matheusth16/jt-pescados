import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError, WorksheetNotFound, GSpreadException
import pandas as pd
import streamlit as st
import os
import time
from datetime import datetime

# --- NOVOS IMPORTS DA ARQUITETURA ---
from core.config import SHEET_ID, FUSO_BR
from services.utils import limpar_texto

# --- CONEXÃO COM GOOGLE SHEETS ---
@st.cache_resource
def get_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    last_error = None
    for tentativa in range(3):
        try:
            if "gcp_service_account" in st.secrets:
                creds_dict = st.secrets["gcp_service_account"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            elif os.path.exists("credentials.json"):
                creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            else:
                raise FileNotFoundError("Credenciais não encontradas (secrets ou json).")
            
            gc = gspread.authorize(creds)
            return gc.open_by_key(SHEET_ID)
        except Exception as e:
            last_error = e
            if "429" in str(e): 
                time.sleep(2)
                continue
            else:
                break
    
    raise ConnectionError(f"Falha na conexão com Google Sheets: {last_error}")

# --- FUNÇÕES AUXILIARES LOCAIS ---
def get_col_indices(ws):
    """Mapeia nomes das colunas para índices."""
    cabecalhos = [c.upper().strip() for c in ws.row_values(1)]
    mapa = {}
    for idx, nome in enumerate(cabecalhos):
        mapa[nome] = idx + 1
    return mapa

# --- CONTROLE DE CACHE INTELIGENTE ---
def obter_versao_planilha():
    try:
        sh = get_connection()
        return sh.lastUpdateTime
    except Exception:
        return time.time()

# --- AUTENTICAÇÃO ---
def autenticar_usuario(login_digitado, senha_digitada):
    sh = get_connection()
    try:
        ws = sh.worksheet("Usuarios")
    except WorksheetNotFound:
        raise Exception("Aba 'Usuarios' não encontrada na planilha.")
        
    usuarios = ws.get_all_records()
    for u in usuarios:
        if str(u.get('LOGIN', '')).strip().lower() == str(login_digitado).strip().lower() and \
           str(u.get('SENHA', '')).strip() == str(senha_digitada).strip():
            return {"nome": u.get('NOME', 'Usuário'), "perfil": u.get('PERFIL', 'Operador')}
    return None

# --- LEITURAS COM CACHE INTELIGENTE ---
@st.cache_data
def listar_clientes(_hash_versao=None):
    sh = get_connection()
    ws = sh.worksheet("BaseClientes")
    col_valores = ws.col_values(2)
    if len(col_valores) > 1:
        return sorted(list(set([limpar_texto(n) for n in col_valores[1:] if n])))
    return []

def buscar_pedidos_visualizacao():
    sh = get_connection()
    ws = sh.worksheet("Pedidos")
    dados = ws.get_all_values()
    if len(dados) > 1:
        try:
            corrigiu = corrigir_ids_faltantes(ws, dados)
            if corrigiu: dados = ws.get_all_values()
        except: pass
        return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

def corrigir_ids_faltantes(ws, dados):
    cabecalhos = [str(c).upper().strip() for c in dados[0]]
    if "ID_PEDIDO" not in cabecalhos: return False
    idx_id = cabecalhos.index("ID_PEDIDO")
    coluna_ids = [linha[idx_id] for linha in dados[1:]]
    
    if any(not val or val == "" for val in coluna_ids):
        ids_corretos = [[str(i + 1)] for i in range(len(coluna_ids))]
        ws.update(f"A2:A{len(coluna_ids) + 1}", ids_corretos)
        return True
    return False

# --- HISTÓRICO ---
def obter_resumo_historico(df_bruto, nome_cliente):
    if df_bruto.empty or not nome_cliente:
        return []
    
    df = df_bruto.copy()
    df.columns = [str(c).strip().upper() for c in df.columns]
    
    cols_necessarias = ["NOME CLIENTE", "STATUS", "ID_PEDIDO"]
    if not all(c in df.columns for c in cols_necessarias):
        return []

    nome_alvo = limpar_texto(nome_cliente)
    df["_NOME_TEMP"] = df["NOME CLIENTE"].apply(limpar_texto)
    df_cli = df[df["_NOME_TEMP"] == nome_alvo]
    
    if df_cli.empty:
        return []

    col_data = next((c for c in df_cli.columns if "ENTREGA" in c), None)
    if col_data:
        df_cli[col_data] = pd.to_datetime(df_cli[col_data], dayfirst=True, errors='coerce')
        df_cli = df_cli.sort_values(col_data, ascending=False)

    historico = []
    for _, row in df_cli.iterrows():
        data_str = "-"
        if col_data and pd.notnull(row[col_data]):
            data_str = row[col_data].strftime("%d/%m/%Y")
        
        desc = row.get("PEDIDO") or row.get("DESCRIÇÃO") or row.get("OBSERVAÇÃO") or "Sem descrição"
        
        item = {
            "id": row.get("ID_PEDIDO", "?"),
            "data": data_str,
            "status": row.get("STATUS", "Desconhecido"),
            "descricao": str(desc),
            "pagamento": row.get("PAGAMENTO", "-")
        }
        historico.append(item)
        
    return historico

# --- GRAVAÇÃO ---
def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido, observacao="", nr_pedido="", usuario_logado="Sistema"):
    sh = get_connection()
    get_metricas.clear()
    listar_clientes.clear()
    
    try:
        ws_respostas = sh.worksheet("Respostas ao formulário 1")
        ws_pedidos = sh.worksheet("Pedidos")
        ws_logs = sh.worksheet("Historico_Logs")
    except WorksheetNotFound as e:
        raise Exception(f"Aba obrigatória não encontrada: {e}")

    nome_final = limpar_texto(nome)
    obs_final = limpar_texto(observacao)
    nr_final = limpar_texto(nr_pedido)
    desc_final = descricao.strip() 

    # 1. Respostas
    data_log = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    coluna_datas = ws_respostas.col_values(1)
    proxima_linha = len(coluna_datas) + 1 if len(coluna_datas) > 0 else 2
    ws_respostas.update(f"A{proxima_linha}:D{proxima_linha}", [[
        data_log, nome_final, desc_final, data_entrega.strftime("%d/%m/%Y")
    ]])
    time.sleep(1) 
    
    # 2. Pedidos
    mapa = get_col_indices(ws_pedidos)
    novo_id = proxima_linha - 1
    cells = []
    if "ID_PEDIDO" in mapa: cells.append(gspread.Cell(proxima_linha, mapa["ID_PEDIDO"], str(novo_id)))
    if "PAGAMENTO" in mapa: cells.append(gspread.Cell(proxima_linha, mapa["PAGAMENTO"], pagamento_escolhido))
    if "STATUS" in mapa: cells.append(gspread.Cell(proxima_linha, mapa["STATUS"], status_escolhido))
    if nr_final and "NR PEDIDO" in mapa: cells.append(gspread.Cell(proxima_linha, mapa["NR PEDIDO"], nr_final))
    
    col_obs = next((c for c in ["OBSERVAÇÃO", "DESCRIÇÃO"] if c in mapa), None)
    if col_obs and obs_final: cells.append(gspread.Cell(proxima_linha, mapa[col_obs], obs_final))

    if cells: ws_pedidos.update_cells(cells)

    # 3. Log
    try:
        ws_logs.append_row([
            data_log, str(novo_id), str(usuario_logado),
            "CRIAÇÃO", "-", f"Status: {status_escolhido}"
        ])
    except: pass

# --- ATUALIZAÇÃO ---
def atualizar_pedidos_editaveis(df_editado, usuario_logado="Sistema"):
    sh = get_connection()
    ws_pedidos = sh.worksheet("Pedidos")
    ws_logs = sh.worksheet("Historico_Logs")
    
    dados_atuais = ws_pedidos.get_all_values()
    if len(dados_atuais) < 2: return
    
    cabecalhos = [c.upper().strip() for c in dados_atuais[0]]
    mapa = {nome: idx + 1 for idx, nome in enumerate(cabecalhos)}
    
    idx_id = mapa.get("ID_PEDIDO")
    if not idx_id: raise Exception("ID_PEDIDO ausente.")
    
    snapshot = {}
    for i, row in enumerate(dados_atuais[1:]):
        pid = str(row[idx_id-1])
        if pid: snapshot[pid] = {"row": i+2, "data": row}

    cells = []
    logs = []
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    
    cols_check = {"STATUS": "STATUS", "PAGAMENTO": "PAGAMENTO", "NR PEDIDO": "NR PEDIDO", "OBSERVAÇÃO": "OBSERVAÇÃO"}

    for _, row in df_editado.iterrows():
        pid = str(row.get("ID_PEDIDO", ""))
        antigo = snapshot.get(pid)
        if antigo:
            for col_df, col_sheet in cols_check.items():
                if col_df in df_editado.columns and col_sheet in mapa:
                    val_novo = limpar_texto(row[col_df]) if col_df not in ["STATUS", "PAGAMENTO"] else str(row[col_df]).strip().upper()
                    
                    idx_col_antiga = mapa[col_sheet] - 1
                    val_antigo = ""
                    if idx_col_antiga < len(antigo["data"]):
                        val_antigo = limpar_texto(antigo["data"][idx_col_antiga])

                    if val_novo != val_antigo:
                        cells.append(gspread.Cell(antigo["row"], mapa[col_sheet], val_novo))
                        logs.append([timestamp, pid, usuario_logado, col_sheet, val_antigo, val_novo])
    
    if logs: ws_logs.append_rows(logs)
    if cells: ws_pedidos.update_cells(cells)

# --- CLIENTES ---
def criar_novo_cliente(nome, cidade, documento=""):
    sh = get_connection()
    listar_clientes.clear()
    get_metricas.clear()
    
    ws = sh.worksheet("BaseClientes")
    nome_final = limpar_texto(nome)
    cidade_final = limpar_texto(cidade)
    doc_final = limpar_texto(documento)
    
    coluna_ids = ws.col_values(1)[1:] 
    ids_nums = [int(x) for x in coluna_ids if str(x).strip().isdigit()]
    novo_id = max(ids_nums) + 1 if ids_nums else 1
    
    ws.append_row([novo_id, nome_final, cidade_final, doc_final])

@st.cache_data
def get_metricas(_hash_versao=None):
    sh = get_connection()
    ws_cli = sh.worksheet("BaseClientes")
    ws_ped = sh.worksheet("Pedidos")
    return len(ws_cli.col_values(1))-1, len(ws_ped.col_values(1))-1

# ==============================================================================
# --- MÓDULO RECEBIMENTO SALMÃO ---
# ==============================================================================

@st.cache_data(ttl=30, show_spinner=False)
def get_estoque_filtrado(tag_inicio, tag_fim):
    sh = get_connection()
    try:
        ws = sh.worksheet("Recebimento_Salmão")
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        
        if not df.empty and "Tag" in df.columns:
            df["Tag"] = pd.to_numeric(df["Tag"], errors='coerce').fillna(0).astype(int)
            
            if "Peso" in df.columns:
                df["Peso"] = df["Peso"].astype(str).str.replace(",", ".")
                df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0)
            
            df_filtrado = df[(df["Tag"] >= tag_inicio) & (df["Tag"] <= tag_fim)]
            return df_filtrado.sort_values("Tag")
            
        return pd.DataFrame()
    except WorksheetNotFound:
        return pd.DataFrame()

def salvar_alteracoes_estoque(df_novo, usuario_logado):
    sh = get_connection()
    get_estoque_filtrado.clear()
    
    ws = sh.worksheet("Recebimento_Salmão")
    ws_logs = sh.worksheet("Historico_Logs")
    
    mapa_colunas = get_col_indices(ws)
    colunas_editaveis = ["Calibre", "Peso", "Cliente", "Fornecedor", "Validade", "Status"]
    
    updates = []
    logs = []
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    
    for idx, row_nova in df_novo.iterrows():
        tag_id = int(row_nova["Tag"])
        excel_row = tag_id + 1 
        
        for col in colunas_editaveis:
            val_novo = str(row_nova[col]).strip()
            if col == "Status": val_novo = val_novo.capitalize()
            
            col_idx = mapa_colunas.get(col.upper())
            if col_idx:
                updates.append(gspread.Cell(excel_row, col_idx, val_novo))

    if updates:
        ws.update_cells(updates)
        ws_logs.append_row([timestamp, "LOTE", usuario_logado, "EDICAO_ESTOQUE", "-", f"Atualizou {len(updates)} células"])
        return len(updates)
    return 0

def registrar_subtag(id_pai, letra, cliente, peso, status, usuario_logado):
    sh = get_connection()
    
    ws = sh.worksheet("Recebimento_SubTags")
    ws_logs = sh.worksheet("Historico_Logs")
    
    nova_linha = [int(id_pai), limpar_texto(letra), limpar_texto(cliente), float(peso), status.capitalize()]
    ws.append_row(nova_linha)
    
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    ws_logs.append_row([timestamp, f"TAG-{id_pai}", usuario_logado, "DESMEMBRAMENTO", "-", f"Letra {letra}: {peso}kg"])
    return True

# --- ADICIONE ISTO AO FINAL DO ARQUIVO services/database.py ---

def get_consumo_tag(tag_pai_id):
    """
    Retorna o peso total já consumido e a lista de letras usadas para uma Tag Pai.
    """
    sh = get_connection()
    try:
        ws = sh.worksheet("Recebimento_SubTags")
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        
        if df.empty:
            return [], 0.0
            
        # Padroniza colunas para evitar erro de caixa alta/baixa
        df.columns = [str(c).strip().upper() for c in df.columns]
        
        # Verifica se as colunas essenciais existem (Baseado no registrar_subtag)
        # ID_PAI, LETRA, PESO
        if "ID_PAI" in df.columns:
            # Filtra apenas as linhas dessa Tag
            df["ID_PAI"] = pd.to_numeric(df["ID_PAI"], errors='coerce').fillna(0).astype(int)
            df_tag = df[df["ID_PAI"] == int(tag_pai_id)]
            
            if df_tag.empty:
                return [], 0.0

            # Pega lista de letras já usadas
            letras_usadas = []
            if "LETRA" in df_tag.columns:
                letras_usadas = df_tag["LETRA"].astype(str).str.strip().str.upper().tolist()
            
            # Soma o peso já desmembrado
            peso_usado = 0.0
            if "PESO" in df_tag.columns:
                 # Garante que seja número
                 s = df_tag["PESO"].astype(str).str.replace(",", ".")
                 peso_usado = pd.to_numeric(s, errors='coerce').fillna(0.0).sum()
                 
            return letras_usadas, peso_usado
            
    except Exception:
        return [], 0.0
    
    return [], 0.0

# --- ADICIONE AO FINAL DE services/database.py ---

def get_resumo_global_salmao():
    """
    Retorna contagens totais de todo o estoque (sem filtro de tags).
    Retorna: (total, livre, gerado, orcamento, reservado)
    """
    sh = get_connection()
    try:
        ws = sh.worksheet("Recebimento_Salmão")
        # Pega todos os registros para contagem global
        dados = ws.get_all_records()
        df = pd.DataFrame(dados)
        
        if df.empty or "Status" not in df.columns:
            return 0, 0, 0, 0, 0
            
        # Normaliza para garantir contagem correta
        s = df["Status"].astype(str).str.strip().str.capitalize()
        
        total = len(df)
        livre = len(s[s == "Livre"])
        gerado = len(s[s == "Gerado"])
        
        # 'Orçamento' pode ter variações de encoding, garantimos com startswith ou contains se necessário, 
        # mas capitalize() deve resolver se estiver salvo corretamente.
        orcamento = len(s[s == "Orçamento"]) 
        reservado = len(s[s == "Reservado"])
        
        return total, livre, gerado, orcamento, reservado
    except:
        return 0, 0, 0, 0, 0