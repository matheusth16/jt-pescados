import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st
import os
import time
from datetime import datetime

# Constantes
SHEET_ID = "1IenRiZI1TeqCFk4oB-r2WrqGsk0muUACsQA-kkvP4tc"

# --- FUNÇÕES AUXILIARES ---
def numero_para_coluna(n):
    """Converte 1 -> A, 2 -> B, ... 27 -> AA"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def get_col_indices(ws):
    """
    Mapeia os nomes das colunas para seus índices numéricos (1-based).
    Ex: {'ID_PEDIDO': 1, 'STATUS': 10, 'PAGAMENTO': 7}
    """
    cabecalhos = [c.upper().strip() for c in ws.row_values(1)]
    mapa = {}
    for idx, nome in enumerate(cabecalhos):
        mapa[nome] = idx + 1
    return mapa

# --- CONEXÃO COM GOOGLE SHEETS ---
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
                # Retorna None silenciosamente para tentar reconexão depois
                return None
    return None

# --- AUTENTICAÇÃO (LOGIN) ---
def autenticar_usuario(login_digitado, senha_digitada):
    """
    Verifica se o login e senha existem na aba 'Usuarios'
    """
    sh = get_connection()
    if not sh: return None
    try:
        ws = sh.worksheet("Usuarios")
        usuarios = ws.get_all_records()
        
        for u in usuarios:
            # Compara login (sem case sensitive) e senha (exata)
            u_login = str(u.get('LOGIN', '')).strip().lower()
            u_senha = str(u.get('SENHA', '')).strip()
            
            input_login = str(login_digitado).strip().lower()
            input_senha = str(senha_digitada).strip()

            if u_login == input_login and u_senha == input_senha:
                return {
                    "nome": u.get('NOME', 'Usuário'),
                    "perfil": u.get('PERFIL', 'Operador')
                }
        return None
    except Exception as e:
        st.error(f"Erro ao acessar usuários: {e}")
        return None

# --- LEITURAS ---
@st.cache_data(ttl=300)
def listar_clientes():
    sh = get_connection()
    if not sh: return []
    try:
        ws = sh.worksheet("BaseClientes")
        col_valores = ws.col_values(2) # Coluna B é o Nome
        if len(col_valores) > 1:
            nomes = sorted(list(set(col_valores[1:])))
            return nomes
        return []
    except:
        return []

def buscar_pedidos_visualizacao():
    sh = get_connection()
    if not sh: return pd.DataFrame()
    try:
        ws = sh.worksheet("Pedidos")
        dados = ws.get_all_values()
        
        if len(dados) > 1:
            corrigiu = corrigir_ids_faltantes(ws, dados)
            if corrigiu: dados = ws.get_all_values()
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

def corrigir_ids_faltantes(ws, dados):
    """Auto-preenche IDs se estiverem vazios na coluna A"""
    try:
        cabecalhos = [str(c).upper().strip() for c in dados[0]]
        if "ID_PEDIDO" not in cabecalhos: return False

        idx_id = cabecalhos.index("ID_PEDIDO")
        coluna_ids = [linha[idx_id] for linha in dados[1:]]
        
        precisa_corrigir = False
        for val in coluna_ids:
            if not val or val == "" or val == "None":
                precisa_corrigir = True
                break
        
        if precisa_corrigir:
            qtd_linhas = len(coluna_ids)
            ids_corretos = [[str(i + 1)] for i in range(qtd_linhas)]
            ws.update(f"A2:A{qtd_linhas + 1}", ids_corretos)
            return True
    except:
        pass
    return False

# --- GRAVAÇÃO (CRIAÇÃO DE PEDIDO) ---
def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido, observacao="", nr_pedido="", usuario_logado="Sistema"):
    """
    Cria pedido novo.
    Agora grava também a 'observacao' na coluna correta da aba Pedidos.
    """
    sh = get_connection()
    get_metricas.clear()
    
    ws_respostas = sh.worksheet("Respostas ao formulário 1")
    ws_pedidos = sh.worksheet("Pedidos")
    ws_logs = sh.worksheet("Historico_Logs")
    
    # 1. Salvar na aba de Respostas (Para ativar as fórmulas de Rota/Preço)
    coluna_datas = ws_respostas.col_values(1)
    proxima_linha = len(coluna_datas) + 1
    if proxima_linha < 2: proxima_linha = 2
    
    nova_linha_respostas = [
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        nome,
        descricao.strip(),
        data_entrega.strftime("%d/%m/%Y")
    ]
    ws_respostas.update(f"A{proxima_linha}:D{proxima_linha}", [nova_linha_respostas])
    
    time.sleep(1) # Delay técnico para o Google Sheets processar
    
    # 2. Salvar na aba Pedidos (Campos Manuais: Status, Pagamento, Obs)
    mapa_colunas = get_col_indices(ws_pedidos)
    novo_id = proxima_linha - 1
    
    celulas_para_gravar = []
    
    def add_cell(nome_col, valor):
        if nome_col in mapa_colunas:
            col_idx = mapa_colunas[nome_col]
            celulas_para_gravar.append(
                gspread.Cell(proxima_linha, col_idx, str(valor))
            )

    add_cell("ID_PEDIDO", novo_id)
    add_cell("PAGAMENTO", pagamento_escolhido)
    add_cell("STATUS", status_escolhido)
    
    if nr_pedido:
        add_cell("NR PEDIDO", nr_pedido)
        
    # Grava a Observação na coluna certa
    possiveis_obs = ["OBSERVAÇÃO", "OBSERVACAO", "DESCRIÇÃO", "DESCRICAO"]
    col_obs = next((c for c in possiveis_obs if c in mapa_colunas), None)
    if col_obs and observacao:
         add_cell(col_obs, observacao.strip())

    if celulas_para_gravar:
        ws_pedidos.update_cells(celulas_para_gravar)

    # 3. Log de Auditoria
    try:
        log_entry = [
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            str(novo_id),
            str(usuario_logado),
            "CRIAÇÃO",
            "-",
            f"Status: {status_escolhido} | Obs: {observacao[:30]}..."
        ]
        ws_logs.append_row(log_entry)
    except:
        pass

# --- ATUALIZAÇÃO (EDIÇÃO COM AUDITORIA) ---
def atualizar_pedidos_editaveis(df_editado, usuario_logado="Sistema"):
    """
    Atualiza apenas as células alteradas, mantendo o resto intacto.
    """
    sh = get_connection()
    ws_pedidos = sh.worksheet("Pedidos")
    ws_logs = sh.worksheet("Historico_Logs")
    
    # Snapshot Antes
    dados_atuais = ws_pedidos.get_all_values()
    if len(dados_atuais) < 2: return
    
    cabecalhos_sheet = [c.upper().strip() for c in dados_atuais[0]]
    mapa_colunas = {nome: idx + 1 for idx, nome in enumerate(cabecalhos_sheet)}
    
    idx_id_sheet = mapa_colunas.get("ID_PEDIDO")
    if not idx_id_sheet: return
    
    snapshot_antes = {}
    for i, linha in enumerate(dados_atuais[1:]): 
        linha_safe = linha + [""] * (len(cabecalhos_sheet) - len(linha))
        id_ped = str(linha_safe[idx_id_sheet - 1])
        if id_ped:
            snapshot_antes[id_ped] = {
                header: linha_safe[h_idx] 
                for h_idx, header in enumerate(cabecalhos_sheet)
            }
            snapshot_antes[id_ped]["__LINHA_SHEET__"] = i + 2

    # Lista de colunas permitidas para edição
    allowed_cols = {
        "STATUS": ["STATUS"],
        "PAGAMENTO": ["PAGAMENTO"],
        "NR PEDIDO": ["NR PEDIDO", "NR_PEDIDO"],
        "OBSERVAÇÃO": ["OBSERVAÇÃO", "OBSERVACAO"]
    }
    
    df_editado.columns = [c.strip().upper() for c in df_editado.columns]
    
    celulas_para_atualizar = []
    logs_para_registrar = []
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    if "ID_PEDIDO" not in df_editado.columns: return
        
    for index, row in df_editado.iterrows():
        id_pedido = str(row["ID_PEDIDO"])
        dados_antigos = snapshot_antes.get(id_pedido)
        
        if dados_antigos:
            linha_sheet = dados_antigos["__LINHA_SHEET__"]
            
            for chave, lista_sinonimos in allowed_cols.items():
                col_df = next((c for c in df_editado.columns if c in lista_sinonimos), None)
                nome_sheet = next((s for s in lista_sinonimos if s in mapa_colunas), None)
                
                if col_df and nome_sheet:
                    col_idx_sheet = mapa_colunas[nome_sheet]
                    
                    novo_val = str(row[col_df]).strip() if row[col_df] is not None else ""
                    antigo_val = str(dados_antigos.get(nome_sheet, "")).strip()
                    
                    if novo_val != antigo_val:
                        celulas_para_atualizar.append(
                            gspread.Cell(linha_sheet, col_idx_sheet, novo_val)
                        )
                        logs_para_registrar.append([
                            timestamp, id_pedido, usuario_logado, chave, antigo_val, novo_val
                        ])
    
    if logs_para_registrar:
        ws_logs.append_rows(logs_para_registrar)
    if celulas_para_atualizar:
        ws_pedidos.update_cells(celulas_para_atualizar)

# --- CLIENTES E MÉTRICAS ---
def criar_novo_cliente(nome, cidade, documento=""):
    """
    Cria cliente novo. Agora aceita documento (CPF/CNPJ).
    Grava em: [ID, NOME, CIDADE, DOCUMENTO]
    """
    sh = get_connection()
    listar_clientes.clear()
    get_metricas.clear()
    
    ws = sh.worksheet("BaseClientes")
    
    coluna_ids = ws.col_values(1)
    novo_id = 1
    
    # LÓGICA ATUALIZADA AQUI -----------------------------------------
    # Procura o menor ID disponível (preenche buracos)
    if len(coluna_ids) > 1:
        # Cria um conjunto (set) de IDs existentes para verificação rápida
        ids_existentes = set()
        for x in coluna_ids[1:]:
            if str(x).strip().isdigit():
                ids_existentes.add(int(x))
        
        # Começa do 1 e vai subindo até achar um número que NÃO está na lista
        while novo_id in ids_existentes:
            novo_id += 1
    # ----------------------------------------------------------------
    
    # Adiciona a linha com o Documento na 4ª posição
    ws.append_row([novo_id, nome.upper(), cidade.upper(), documento])
    
    # Ordena a planilha por Nome (Coluna B) - Mantido conforme seu pedido
    try:
        sh.batch_update({
            "requests": [{
                "sortRange": {
                    "range": {"sheetId": ws.id, "startRowIndex": 1},
                    "sortSpecs": [{"dimensionIndex": 1, "sortOrder": "ASCENDING"}]
                }
            }]
        })
    except:
        pass

@st.cache_data(ttl=30)
def get_metricas():
    sh = get_connection()
    if not sh: return 0, 0
    try:
        ws_clientes = sh.worksheet("BaseClientes")
        ws_pedidos = sh.worksheet("Pedidos")
        qtd_clientes = len(ws_clientes.col_values(1)) - 1
        qtd_pedidos = len(ws_pedidos.col_values(1)) - 1
        return max(0, qtd_clientes), max(0, qtd_pedidos)
    except:
        return 0, 0