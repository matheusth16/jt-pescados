import streamlit as st
from datetime import datetime
from core.config import DIAS_ALERTA_AMARELO, DIAS_ALERTA_VERMELHO

def limpar_texto(texto):
    """
    Padroniza textos: Remove espaços extras e converte para Maiúsculas.
    Útil para garantir chaves de busca consistentes.
    """
    if not texto:
        return ""
    return str(texto).strip().upper()

def calcular_status_validade(data_str):
    """
    Analisa uma data (DD/MM/YYYY) e retorna o nível de alerta:
    - 'CRITICO': Vencido ou vence em menos de X dias (DIAS_ALERTA_VERMELHO)
    - 'ALERTA': Vence em menos de Y dias (DIAS_ALERTA_AMARELO)
    - 'OK': Prazo seguro ou data inválida
    """
    if not data_str or str(data_str).strip() == "":
        return "OK"
        
    try:
        # Tenta converter string para data
        dt_validade = datetime.strptime(str(data_str).strip(), "%d/%m/%Y")
        hoje = datetime.now()
        
        # Diferença em dias
        diferenca = (dt_validade - hoje).days + 1 # +1 para contar o dia atual
        
        # Lógica de alerta (Se diferença for negativa, já venceu = Critico)
        if diferenca <= DIAS_ALERTA_VERMELHO:
            return "CRITICO"
        elif diferenca <= DIAS_ALERTA_AMARELO:
            return "ALERTA"
        else:
            return "OK"
            
    except ValueError:
        # Se a data estiver em formato errado ou inválido, retorna OK para não quebrar a tela
        return "OK"

def render_details(titulo: str, erro: Exception) -> None:
    """Mostra um erro amigável e expande detalhes técnicos (stacktrace).

    Útil para tratamento de exceções em telas Streamlit sem quebrar o fluxo.
    """
    st.error(titulo)
    # Mostra traceback de forma expansível no Streamlit
    st.exception(erro)
    
def hash_senha(senha: str) -> str:
    """Gera hash da senha para armazenamento seguro (Argon2)."""
    from argon2 import PasswordHasher
    ph = PasswordHasher()
    return ph.hash(senha.strip())

def verificar_senha(senha_digitada: str, hash_armazenado: str) -> bool:
    """Verifica se a senha digitada confere com o hash."""
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    if not hash_armazenado or not senha_digitada:
        return False
    try:
        ph = PasswordHasher()
        ph.verify(hash_armazenado, senha_digitada.strip())
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False