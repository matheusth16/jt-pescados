"""
Módulo de soft delete.
Implementa exclusão lógica em vez de exclusão física.
"""

from datetime import datetime
from core.config import FUSO_BR


def deletar_pedido_soft(client, id_pedido: int, usuario: str):
    """Deleta pedido com soft delete (marca como deletado).
    
    Args:
        client: Cliente Supabase
        id_pedido: ID do pedido
        usuario: Usuário que deletou
        
    Returns:
        bool: True se sucesso
    """
    try:
        timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
        
        client.table("pedidos").update({
            "DELETADO_EM": timestamp,
            "DELETADO_POR": usuario
        }).eq("ID_PEDIDO", id_pedido).execute()
        
        # Registrar na auditoria
        client.table("logs").insert({
            "DATA_HORA": timestamp,
            "ID_PEDIDO": id_pedido,
            "USUARIO": usuario,
            "CAMPO": "DELETADO",
            "VALOR_ANTIGO": "Ativo",
            "VALOR_NOVO": "Deletado"
        }).execute()
        
        return True
    except Exception as e:
        print(f"Erro ao deletar pedido {id_pedido}: {e}")
        return False


def deletar_cliente_soft(client, cod_cliente: int, usuario: str):
    """Deleta cliente com soft delete.
    
    Args:
        client: Cliente Supabase
        cod_cliente: Código do cliente
        usuario: Usuário que deletou
        
    Returns:
        bool: True se sucesso
    """
    try:
        timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
        
        client.table("clientes").update({
            "DELETADO_EM": timestamp,
            "DELETADO_POR": usuario
        }).eq("Código", cod_cliente).execute()
        
        client.table("logs").insert({
            "DATA_HORA": timestamp,
            "USUARIO": usuario,
            "CAMPO": "CLIENTE_DELETADO",
            "VALOR_ANTIGO": "Ativo",
            "VALOR_NOVO": f"Cliente {cod_cliente} deletado"
        }).execute()
        
        return True
    except Exception as e:
        print(f"Erro ao deletar cliente {cod_cliente}: {e}")
        return False


def restaurar_pedido(client, id_pedido: int, usuario: str):
    """Restaura um pedido deletado.
    
    Args:
        client: Cliente Supabase
        id_pedido: ID do pedido
        usuario: Usuário que restaurou
        
    Returns:
        bool: True se sucesso
    """
    try:
        timestamp = datetime.now(FUSO_BR).strftime("%d/%m/%Y %H:%M:%S")
        
        client.table("pedidos").update({
            "DELETADO_EM": None,
            "DELETADO_POR": None
        }).eq("ID_PEDIDO", id_pedido).execute()
        
        client.table("logs").insert({
            "DATA_HORA": timestamp,
            "ID_PEDIDO": id_pedido,
            "USUARIO": usuario,
            "CAMPO": "RESTAURADO",
            "VALOR_ANTIGO": "Deletado",
            "VALOR_NOVO": "Ativo"
        }).execute()
        
        return True
    except Exception as e:
        print(f"Erro ao restaurar pedido {id_pedido}: {e}")
        return False


def listar_deletados(client, tabela: str, limite: int = 100):
    """Lista registros deletados (para recuperação).
    
    Args:
        client: Cliente Supabase
        tabela: Nome da tabela (pedidos, clientes, etc)
        limite: Número máximo de registros
        
    Returns:
        DataFrame com registros deletados
    """
    try:
        import pandas as pd
        
        response = client.table(tabela)\
            .select("*")\
            .not_.is_null("DELETADO_EM")\
            .order("DELETADO_EM", desc=True)\
            .limit(limite)\
            .execute()
        
        if response.data:
            return pd.DataFrame(response.data)
        return pd.DataFrame()
    
    except Exception as e:
        print(f"Erro ao listar deletados de {tabela}: {e}")
        return None
