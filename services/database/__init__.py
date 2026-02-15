"""
Serviço de banco de dados Supabase.
Reexporta todas as funções para manter compatibilidade com `import services.database as db`.
"""
from services.database.client import get_db_client, get_max_id, obter_versao_planilha
from services.database.auth import autenticar_usuario
from services.database.clientes import (
    listar_clientes,
    criar_novo_cliente,
    get_metricas,
    buscar_clientes_paginado,
)
from services.database.pedidos import (
    listar_dados_filtros,
    buscar_pedidos_visualizacao,
    obter_resumo_historico,
    salvar_pedido,
    atualizar_pedidos_editaveis,
    buscar_pedidos_paginado,
)
from services.database.salmao import (
    get_estoque_filtrado,
    get_estoque_backup_filtrado,
    salvar_alteracoes_estoque,
    registrar_subtag,
    buscar_subtags_por_tag,
    get_consumo_tag,
    get_resumo_global_salmao,
    arquivar_tags_geradas,
)

__all__ = [
    "get_db_client",
    "get_max_id",
    "obter_versao_planilha",
    "autenticar_usuario",
    "listar_clientes",
    "criar_novo_cliente",
    "get_metricas",
    "buscar_clientes_paginado",
    "listar_dados_filtros",
    "buscar_pedidos_visualizacao",
    "obter_resumo_historico",
    "salvar_pedido",
    "atualizar_pedidos_editaveis",
    "buscar_pedidos_paginado",
    "get_estoque_filtrado",
    "get_estoque_backup_filtrado",
    "salvar_alteracoes_estoque",
    "registrar_subtag",
    "buscar_subtags_por_tag",
    "get_consumo_tag",
    "get_resumo_global_salmao",
    "arquivar_tags_geradas",
]
