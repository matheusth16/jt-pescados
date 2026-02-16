import pandas as pd
import streamlit as st
import time
from datetime import datetime
from supabase import create_client, Client

# --- IMPORTS DA CONFIGURAÇÃO ---
from core.config import SUPABASE_URL, SUPABASE_KEY, FUSO_BR
from services.utils import limpar_texto

# --- CONEXÃO COM SUPABASE ---
@st.cache_resource
def get_db_client() -> Client:
    """Retorna o cliente do Supabase (Singleton)."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FUNÇÕES AUXILIARES LOCAIS ---
def get_max_id(table_name, id_column):
    """Busca o maior ID numérico de uma tabela para simular auto-incremento manual."""
    try:
        client = get_db_client()
        response = client.table(table_name)\
            .select(id_column)\
            .order(id_column, desc=True)\
            .limit(1)\
            .execute()
        if response.data:
            return int(response.data[0][id_column])
        return 0
    except Exception:
        return 0

# --- CONTROLE DE CACHE INTELIGENTE ---
def obter_versao_planilha():
    return time.time()

# --- AUTENTICAÇÃO ---
def autenticar_usuario(login_digitado, senha_digitada):
    client = get_db_client()
    try:
        # Busca usuário exato
        response = client.table("usuarios")\
            .select("*")\
            .eq("LOGIN", str(login_digitado).strip())\
            .eq("SENHA", str(senha_digitada).strip())\
            .execute()
        
        if response.data:
            user = response.data[0]
            return {"nome": user.get('NOME', 'Usuário'), "perfil": user.get('PERFIL', 'Operador')}
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
    return None

# --- LEITURAS ---
@st.cache_data(ttl=300)
def listar_clientes(_hash_versao=None):
    client = get_db_client()
    try:
        # Mantém apenas a coluna Cliente para preencher listas simples
        response = client.table("clientes").select("Cliente").order("Cliente").execute()
        if response.data:
            lista = [c["Cliente"] for c in response.data if c["Cliente"]]
            return sorted(list(set(lista)))
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def listar_dados_filtros():
    """
    Retorna listas únicas de Cidades e Rotas dos pedidos para preencher filtros.
    Cache longo (5 min) pois esses dados variam pouco.
    """
    client = get_db_client()
    try:
        # Busca apenas colunas de filtro para ser extremamente leve
        response = client.table("pedidos").select("CIDADE, ROTA").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Extrai únicos e remove vazios
            cidades = sorted([str(x) for x in df["CIDADE"].unique() if x and str(x).strip() != ''])
            rotas = sorted([str(x) for x in df["ROTA"].unique() if x and str(x).strip() != ''])
            return cidades, rotas
    except Exception:
        pass
    return [], []

@st.cache_data(ttl=300)
def buscar_pedidos_visualizacao():
    """
    Busca apenas colunas essenciais para indicadores visuais (Dashboard/KPIs).
    OTIMIZAÇÃO: Removeu select("*") para reduzir tráfego de dados.
    """
    client = get_db_client()
    try:
        # Seleciona apenas o necessário para gráficos e contagens
        cols = 'ID_PEDIDO, STATUS, PAGAMENTO, "DIA DA ENTREGA", "NOME CLIENTE"'
        
        response = client.table("pedidos").select(cols).order("ID_PEDIDO", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            return df
    except Exception:
        pass
    return pd.DataFrame()

# --- HISTÓRICO ---
def obter_resumo_historico(nome_cliente, limite=5):
    """
    Busca o histórico de um cliente específico diretamente no banco.
    """
    if not nome_cliente:
        return []

    client = get_db_client()
    try:
        nome_alvo = limpar_texto(nome_cliente)
        
        # OTIMIZAÇÃO: Seleciona apenas colunas exibidas no modal de histórico
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

    except Exception as e:
        return []

# --- GRAVAÇÃO ---
def salvar_pedido(nome, descricao, data_entrega, pagamento_escolhido, status_escolhido, observacao="", nr_pedido="", usuario_logado="Sistema"):
    client = get_db_client()
    
    # LIMPEZA DE CACHE ESTRATÉGICA
    get_metricas.clear()
    listar_clientes.clear()
    buscar_pedidos_visualizacao.clear()
    listar_dados_filtros.clear() # Limpa filtros pois nova cidade/rota pode ter surgido
    
    nome_final = limpar_texto(nome)
    obs_final = limpar_texto(observacao)
    nr_final = limpar_texto(nr_pedido)
    desc_final = descricao.strip() 
    data_entrega_str = data_entrega.strftime("%d/%m/%Y")
    data_log = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    
    # 1. Gerar ID do Pedido
    novo_id = get_max_id("pedidos", "ID_PEDIDO") + 1

    # 2. Buscar Dados do Cliente
    cod_cliente = None
    cidade_dest = "NÃO DEFINIDO"
    rota_dest = "RETIRADA CD"
    
    try:
        # Busca apenas os campos necessários para preencher o pedido
        resp_cli = client.table("clientes")\
            .select('"Código", "Nome Cidade", ROTA')\
            .eq("Cliente", nome)\
            .execute()
            
        if resp_cli.data:
            d = resp_cli.data[0]
            cod_cliente = d.get("Código")
            cidade_dest = d.get("Nome Cidade") or "NÃO DEFINIDO"
            rota_dest = d.get("ROTA") or "RETIRADA CD"
    except:
        pass

    # 3. Inserir no Banco
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
        
        log_entry = {
            "DATA_HORA": data_log,
            "ID_PEDIDO": novo_id,
            "USUARIO": str(usuario_logado),
            "CAMPO": "CRIAÇÃO",
            "VALOR_ANTIGO": "-",
            "VALOR_NOVO": f"Status: {status_escolhido}"
        }
        client.table("logs").insert(log_entry).execute()
        
    except Exception as e:
        raise Exception(f"Erro ao salvar no Supabase: {e}")

# --- ATUALIZAÇÃO ---
def atualizar_pedidos_editaveis(df_editado, usuario_logado="Sistema"):
    client = get_db_client()
    if df_editado.empty: return
    
    buscar_pedidos_visualizacao.clear()

    colunas_check = ["STATUS", "PAGAMENTO", "NR PEDIDO", "OBSERVAÇÃO"]
    
    if "ID_PEDIDO" not in df_editado.columns:
        st.error("ID_PEDIDO não encontrado na edição.")
        return

    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")

    for _, row in df_editado.iterrows():
        pid = row["ID_PEDIDO"]
        try:
            # Seleciona apenas as colunas que podem ser comparadas
            cols = 'ID_PEDIDO, STATUS, PAGAMENTO, "NR PEDIDO", OBSERVAÇÃO'
            resp = client.table("pedidos").select(cols).eq("ID_PEDIDO", pid).execute()
            
            if not resp.data: continue
            
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

                    # ✅ REGRA: NR PEDIDO só pode ser definido se estiver vazio no banco
                    if col == "NR PEDIDO":
                        # Se já existe NR no banco, NÃO deixa alterar
                        if val_antigo_limpo != "":
                            continue  # ignora qualquer tentativa de mudança no NR

                        # Se estava vazio, você pode normalizar/limpar aqui se quiser
                        # val_novo = limpar_texto(val_novo)

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

# --- CLIENTES ---
def criar_novo_cliente(nome, cidade, documento=""):
    client = get_db_client()
    listar_clientes.clear()
    get_metricas.clear()
    
    nome_final = limpar_texto(nome)
    cidade_final = limpar_texto(cidade)
    doc_final = limpar_texto(documento)
    
    novo_id = get_max_id("clientes", "Código") + 1
    
    dados = {
        "Código": novo_id,
        "Cliente": nome_final,
        "Nome Cidade": cidade_final,
        "CPF/CNPJ": doc_final,
        "ROTA": "NÃO DEFINIDO", 
        "PRAZO": "A VISTA"
    }
    
    try:
        client.table("clientes").insert(dados).execute()
    except Exception as e:
        st.error(f"Erro ao criar cliente: {e}")

@st.cache_data(ttl=300)
def get_metricas(_hash_versao=None):
    client = get_db_client()
    try:
        count_cli = client.table("clientes").select("Código", count="exact", head=True).execute().count
        count_ped = client.table("pedidos").select("ID_PEDIDO", count="exact", head=True).execute().count
        return count_cli, count_ped
    except:
        return 0, 0

# --- ESTOQUE (SALMÃO) ---
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
    """Busca o histórico de itens 'Gerados' (arquivados) no intervalo de tags."""
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
            # Mesmas conversões de tipo da tabela principal para garantir compatibilidade
            df["Tag"] = pd.to_numeric(df["Tag"], errors='coerce').fillna(0).astype(int)
            df["Peso"] = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0)
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def salvar_alteracoes_estoque(df_novo, usuario_logado):
    client = get_db_client()
    
    # Limpa cache de estoque e resumo global
    get_estoque_filtrado.clear()
    get_resumo_global_salmao.clear()
    
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    count_updates = 0
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

    return count_updates

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

# --- SUBTAGS ---
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
        if not response.data: return [], 0.0
        df = pd.DataFrame(response.data)
        letras_usadas = df["Letra"].astype(str).str.strip().str.upper().tolist() if "Letra" in df.columns else []
        peso_usado = pd.to_numeric(df["Peso"], errors='coerce').fillna(0.0).sum() if "Peso" in df.columns else 0.0
        return letras_usadas, peso_usado
    except Exception:
        return [], 0.0

@st.cache_data(ttl=60)
def get_resumo_global_salmao():
    client = get_db_client()
    try:
        response = client.table("estoque_salmao").select("Status").execute()
        dados = response.data
        resp_backup = client.table("estoque_salmao_backup").select("*", count="exact", head=True).execute()
        qtd_historico = resp_backup.count if resp_backup.count is not None else 0

        if not dados: return 0, 0, qtd_historico, 0, 0, 0
        
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
    except Exception as e:
        return 0, 0, 0, 0, 0, 0

# --- PAGINAÇÃO PEDIDOS ---
def buscar_pedidos_paginado(pagina_atual=1, tamanho_pagina=20, filtros=None):
    """
    Busca pedidos com paginação E filtros aplicados no Banco de Dados.
    OTIMIZAÇÃO: Traz apenas colunas necessárias para o 'Gerenciar'.
    """
    client = get_db_client()
    inicio = (pagina_atual - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina - 1
    
    try:
        # Colunas estritamente necessárias para a tabela de gestão
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

# --- PAGINAÇÃO CLIENTES ---
def buscar_clientes_paginado(pagina_atual=1, tamanho_pagina=20):
    client = get_db_client()
    inicio = (pagina_atual - 1) * tamanho_pagina
    fim = inicio + tamanho_pagina - 1
    
    try:
        # OTIMIZAÇÃO: Traz apenas dados da tabela (sem metadados extras)
        cols = '"Código", Cliente, "Nome Cidade", "CPF/CNPJ", ROTA'
        
        response = client.table("clientes")\
            .select(cols, count="exact")\
            .order("Cliente", desc=False)\
            .range(inicio, fim)\
            .execute()
            
        total_registros = response.count if response.count is not None else 0
        df = pd.DataFrame(response.data)
        if df.empty:
            df = pd.DataFrame(columns=["Código", "Cliente", "Nome Cidade", "ROTA"])
        return df, total_registros
    except Exception as e:
        st.error(f"Erro clientes: {e}")
        return pd.DataFrame(), 0
    
def arquivar_tags_geradas(ids_tags, usuario_logado="Sistema"):
    """
    Move dados para backup e LIMPA a tag no estoque para novo uso.
    """
    if not ids_tags:
        return
    
    client = get_db_client()
    timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
    
    # Limpa o cache para garantir atualização imediata
    get_estoque_filtrado.clear()
    get_resumo_global_salmao.clear() # Limpa métricas globais
    
    # RESET TOTAL: Agora incluindo o Status como None
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
            # 1. Backup da Tag principal
            resp_pai = client.table("estoque_salmao").select("*").eq("Tag", int(tag_id)).execute()
            if resp_pai.data:
                dados_pai = resp_pai.data[0]
                client.table("estoque_salmao_backup").insert(dados_pai).execute()
                
                # 2. Backup e Eliminação das Subtags
                resp_sub = client.table("estoque_subtags").select("*").eq("ID_Pai", int(tag_id)).execute()
                if resp_sub.data:
                    client.table("estoque_subtags_backup").insert(resp_sub.data).execute()
                    client.table("estoque_subtags").delete().eq("ID_Pai", int(tag_id)).execute()
                
                # 3. RESET da Tag (Limpa todos os campos)
                client.table("estoque_salmao").update(dados_reset).eq("Tag", int(tag_id)).execute()
                
                # 4. Registo de Log
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