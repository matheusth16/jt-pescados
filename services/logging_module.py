"""
Módulo de logging centralizado.
Gerencia logs estruturados da aplicação.
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
import json


class LoggerStructurado:
    """Logger com suporte a estrutura e contexto."""
    
    def __init__(self, nome: str = "jt_pescados"):
        self.logger = logging.getLogger(nome)
        self.logger.setLevel(logging.DEBUG)
        
        # Criar diretório de logs se não existir
        Path("logs").mkdir(exist_ok=True)
        
        # Handler para arquivo (rotativo)
        arquivo = logging.handlers.RotatingFileHandler(
            "logs/jt_pescados.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        arquivo.setLevel(logging.DEBUG)
        
        # Formato estruturado
        formato = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        arquivo.setFormatter(formato)
        
        if not self.logger.handlers:
            self.logger.addHandler(arquivo)
    
    def erro(self, funcao: str, mensagem: str, usuario: str = "sistema", dados: dict = None):
        """Registra erro com contexto.
        
        Args:
            funcao: Nome da função onde ocorreu
            mensagem: Descrição do erro
            usuario: Usuário que disparou a ação
            dados: Dados adicionais (ex: pedido_id)
        """
        contexto = {
            "funcao": funcao,
            "usuario": usuario,
            "timestamp": datetime.now().isoformat(),
            **(dados or {})
        }
        self.logger.error(f"[{funcao}] {mensagem} | Contexto: {json.dumps(contexto, ensure_ascii=False)}")
    
    def info(self, funcao: str, acao: str, usuario: str = "sistema", dados: dict = None):
        """Registra ação bem-sucedida.
        
        Args:
            funcao: Nome da função
            acao: Descrição da ação
            usuario: Usuário que executou
            dados: Dados adicionais
        """
        contexto = {
            "funcao": funcao,
            "usuario": usuario,
            "timestamp": datetime.now().isoformat(),
            **(dados or {})
        }
        self.logger.info(f"[{funcao}] {acao} | Contexto: {json.dumps(contexto, ensure_ascii=False)}")
    
    def aviso(self, funcao: str, mensagem: str, usuario: str = "sistema", dados: dict = None):
        """Registra aviso.
        
        Args:
            funcao: Nome da função
            mensagem: Descrição do aviso
            usuario: Usuário envolvido
            dados: Dados adicionais
        """
        contexto = {
            "funcao": funcao,
            "usuario": usuario,
            "timestamp": datetime.now().isoformat(),
            **(dados or {})
        }
        self.logger.warning(f"[{funcao}] {mensagem} | Contexto: {json.dumps(contexto, ensure_ascii=False)}")
    
    def seguranca(self, evento: str, usuario: str, detalhes: dict = None):
        """Registra evento de segurança.
        
        Args:
            evento: Tipo de evento (ex: login, falha_auth, acesso_negado)
            usuario: Usuário envolvido
            detalhes: Detalhes do evento
        """
        log_seguranca = {
            "evento": evento,
            "usuario": usuario,
            "timestamp": datetime.now().isoformat(),
            **(detalhes or {})
        }
        self.logger.warning(f"[SEGURANÇA] {evento} | {json.dumps(log_seguranca, ensure_ascii=False)}")


# Instância global
logger = LoggerStructurado()


def log_operacao_banco(operacao: str, tabela: str, usuario: str, resultado: bool, detalhes: dict = None):
    """Log de operações no banco de dados.
    
    Args:
        operacao: INSERT, UPDATE, DELETE, SELECT
        tabela: Nome da tabela
        usuario: Usuário que fez a operação
        resultado: True se sucesso, False se erro
        detalhes: Dados da operação
    """
    status = "✅ SUCESSO" if resultado else "❌ ERRO"
    log_data = {
        "operacao": operacao,
        "tabela": tabela,
        "usuario": usuario,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        **(detalhes or {})
    }
    
    logger.logger.info(f"[BD] {status} | {json.dumps(log_data, ensure_ascii=False)}")
