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