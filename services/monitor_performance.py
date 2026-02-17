"""
Módulo de monitoramento de performance.
Rastreia tempo de execução e alerta sobre gargalos.
"""

import time
import functools
import streamlit as st
from services.logging_module import logger


class MonitorPerformance:
    """Monitora performance de funções."""
    
    LIMITE_AVISO_SEGUNDOS = 2.0
    LIMITE_CRITICO_SEGUNDOS = 5.0
    
    @staticmethod
    def monitorar(nome_funcao: str = None, limiar_aviso: float = None):
        """Decorator para monitorar tempo de execução.
        
        Args:
            nome_funcao: Nome customizado para logging
            limiar_aviso: Limite em segundos para mostrar aviso (padrão: 2s)
        """
        if limiar_aviso is None:
            limiar_aviso = MonitorPerformance.LIMITE_AVISO_SEGUNDOS
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                inicio = time.time()
                nome = nome_funcao or func.__name__
                
                try:
                    resultado = func(*args, **kwargs)
                    duracao = time.time() - inicio
                    
                    # Log de sucesso
                    if duracao > limiar_aviso:
                        if duracao > MonitorPerformance.LIMITE_CRITICO_SEGUNDOS:
                            logger.aviso(
                                nome,
                                f"Função demorou {duracao:.2f}s (crítico!)",
                                dados={"tempo_segundos": round(duracao, 2)}
                            )
                            # Mostrar alerta no Streamlit
                            st.warning(f"⏱️ {nome} demorou {duracao:.2f}s - Considere otimizar")
                        else:
                            logger.info(
                                nome,
                                f"Função executada em {duracao:.2f}s",
                                dados={"tempo_segundos": round(duracao, 2)}
                            )
                    
                    return resultado
                
                except Exception as e:
                    duracao = time.time() - inicio
                    logger.erro(
                        nome,
                        str(e),
                        dados={"tempo_segundos": round(duracao, 2), "erro": str(e)}
                    )
                    raise
            
            return wrapper
        
        return decorator


def perfil_execucao(funcao):
    """Decorator simples que mostra tempo de execução."""
    @functools.wraps(funcao)
    def wrapper(*args, **kwargs):
        inicio = time.time()
        resultado = funcao(*args, **kwargs)
        duracao = time.time() - inicio
        
        print(f"⏱️ {funcao.__name__}: {duracao:.3f}s")
        return resultado
    
    return wrapper


def benchmark(funcao, *args, num_repeticoes: int = 10, **kwargs):
    """Executa função múltiplas vezes e calcula estatísticas.
    
    Args:
        funcao: Função a testar
        args: Argumentos posicionais
        num_repeticoes: Número de vezes a executar
        kwargs: Argumentos nomeados
        
    Returns:
        Dict com estatísticas (min, max, média, etc)
    """
    import statistics
    
    tempos = []
    
    for _ in range(num_repeticoes):
        inicio = time.time()
        funcao(*args, **kwargs)
        duracao = time.time() - inicio
        tempos.append(duracao)
    
    return {
        "minimo": min(tempos),
        "maximo": max(tempos),
        "media": statistics.mean(tempos),
        "mediana": statistics.median(tempos),
        "desvio_padrao": statistics.stdev(tempos) if len(tempos) > 1 else 0,
        "total": sum(tempos),
        "repeticoes": num_repeticoes
    }
