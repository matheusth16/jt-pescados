def limpar_texto(texto):
    """
    Padroniza textos: Remove espaços extras e converte para Maiúsculas.
    Útil para garantir chaves de busca consistentes.
    """
    if not texto:
        return ""
    return str(texto).strip().upper()