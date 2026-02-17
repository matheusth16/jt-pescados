"""
Módulo de rate limiting para proteção contra brute-force.
"""

import streamlit as st
from datetime import datetime, timedelta
import json


class RateLimiter:
    """Proteção contra brute-force usando session_state do Streamlit."""
    
    MAX_TENTATIVAS = 5
    TEMPO_BLOQUEIO_SEGUNDOS = 300  # 5 minutos
    
    @staticmethod
    def inicializar_session():
        """Inicializa variáveis de rate limiting na session."""
        if "rate_limit_tentativas" not in st.session_state:
            st.session_state.rate_limit_tentativas = {}
        if "rate_limit_bloqueios" not in st.session_state:
            st.session_state.rate_limit_bloqueios = {}
    
    @staticmethod
    def registrar_tentativa(chave: str, usuario: str = None) -> tuple[bool, int, int]:
        """Registra uma tentativa de acesso.
        
        Args:
            chave: Identificador único (ex: login, IP)
            usuario: Nome do usuário (opcional)
            
        Returns:
            Tuple (permitido, tentativas_restantes, segundos_para_desbloquear)
        """
        RateLimiter.inicializar_session()
        
        # Verificar se está bloqueado
        bloqueios = st.session_state.rate_limit_bloqueios
        if chave in bloqueios:
            tempo_bloqueio = bloqueios[chave]
            agora = datetime.now()
            
            if agora < tempo_bloqueio:
                segundos_restantes = int((tempo_bloqueio - agora).total_seconds())
                return False, 0, segundos_restantes
            else:
                # Desbloquear
                del bloqueios[chave]
                if chave in st.session_state.rate_limit_tentativas:
                    del st.session_state.rate_limit_tentativas[chave]
        
        # Registrar nova tentativa
        tentativas = st.session_state.rate_limit_tentativas
        tentativas[chave] = tentativas.get(chave, 0) + 1
        
        tentativas_atuais = tentativas[chave]
        tentativas_restantes = max(0, RateLimiter.MAX_TENTATIVAS - tentativas_atuais)
        
        # Bloquear se exceder máximo
        if tentativas_atuais > RateLimiter.MAX_TENTATIVAS:
            tempo_bloqueio = datetime.now() + timedelta(seconds=RateLimiter.TEMPO_BLOQUEIO_SEGUNDOS)
            bloqueios[chave] = tempo_bloqueio
            return False, 0, RateLimiter.TEMPO_BLOQUEIO_SEGUNDOS
        
        return True, tentativas_restantes, 0
    
    @staticmethod
    def limpar_tentativas(chave: str):
        """Limpa tentativas após login bem-sucedido.
        
        Args:
            chave: Identificador único
        """
        RateLimiter.inicializar_session()
        if chave in st.session_state.rate_limit_tentativas:
            del st.session_state.rate_limit_tentativas[chave]


def verificar_rate_limit_login(login: str) -> tuple[bool, str]:
    """Verifica rate limit para login.
    
    Args:
        login: Nome de usuário
        
    Returns:
        Tuple (permitido, mensagem)
    """
    permitido, restantes, bloqueado = RateLimiter.registrar_tentativa(f"login_{login}", usuario=login)
    
    if not permitido:
        mensagem = f"⛔ Muitas tentativas de login. Tente novamente em {bloqueado} segundos."
        return False, mensagem
    
    if restantes < 2:
        mensagem = f"⚠️ {restantes} tentativas restantes antes de bloqueio."
        return True, mensagem
    
    return True, ""


def limpar_rate_limit_login(login: str):
    """Limpa rate limit após login bem-sucedido.
    
    Args:
        login: Nome de usuário
    """
    RateLimiter.limpar_tentativas(f"login_{login}")


# --- ALIASES PARA COMPATIBILIDADE COM IMPORTS ---
# Permitir: from services.rate_limiter import registrar_tentativa, limpar_rate_limit_login
registrar_tentativa = lambda chave: RateLimiter.registrar_tentativa(chave)
