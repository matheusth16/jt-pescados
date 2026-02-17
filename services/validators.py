"""
Módulo de validação com Pydantic.
Define modelos de entrada para todas as operações.
"""

from pydantic import BaseModel, Field, validator, root_validator
from datetime import date, datetime
from typing import Optional
import streamlit as st


class PedidoInput(BaseModel):
    """Modelo para validação de novo pedido."""
    
    nome_cliente: str = Field(..., min_length=3, max_length=100)
    descricao: str = Field(..., min_length=5, max_length=500)
    data_entrega: date = Field(...)
    pagamento: str = Field(..., pattern="^(A COMBINAR|PIX|BOLETO|CARTÃO)$")
    status: str = Field(..., pattern="^(GERADO|PENDENTE|NÃO GERADO|CANCELADO|ENTREGUE|ORÇAMENTO|RESERVADO)$")
    observacao: Optional[str] = Field(default="", max_length=300)
    nr_pedido: Optional[str] = Field(default="", max_length=50)
    
    @validator('nome_cliente')
    def validar_nome(cls, v):
        """Nome não pode ser vazio ou apenas espaços."""
        if not v or not v.strip():
            raise ValueError('Nome do cliente é obrigatório')
        return v.strip()
    
    @validator('descricao')
    def validar_descricao(cls, v):
        """Descrição não pode ser vazia."""
        if not v or not v.strip():
            raise ValueError('Descrição do pedido é obrigatória')
        return v.strip()
    
    @validator('data_entrega')
    def validar_data(cls, v):
        """Data não pode ser no passado."""
        if v < date.today():
            raise ValueError('Data de entrega não pode ser no passado')
        return v
    
    class Config:
        str_strip_whitespace = True


class ClienteInput(BaseModel):
    """Modelo para novo cliente."""
    
    nome: str = Field(..., min_length=3, max_length=100)
    cidade: str = Field(..., min_length=2, max_length=50)
    documento: Optional[str] = Field(default="", max_length=18)
    
    @validator('nome')
    def validar_nome(cls, v):
        if not v or not v.strip():
            raise ValueError('Nome do cliente é obrigatório')
        return v.strip()
    
    @validator('documento')
    def validar_documento(cls, v):
        """Valida CPF/CNPJ básico."""
        if not v:
            return ""
        
        v_limpo = ''.join(c for c in v if c.isdigit())
        
        if len(v_limpo) not in [11, 14]:
            raise ValueError('Documento deve ter 11 dígitos (CPF) ou 14 (CNPJ)')
        
        return v_limpo
    
    class Config:
        str_strip_whitespace = True


class SalmaoInput(BaseModel):
    """Modelo para edição de estoque de salmão."""
    
    tag: int = Field(..., gt=0)
    calibre: Optional[str] = Field(default="", max_length=20)
    peso: float = Field(..., gt=0, le=50)
    cliente: Optional[str] = Field(default="", max_length=100)
    fornecedor: Optional[str] = Field(default="", max_length=100)
    status: str = Field(default="Livre", pattern="^(Livre|Gerado|Orçamento|Reservado|Aberto)$")
    validade: Optional[date] = Field(default=None)
    
    @validator('peso')
    def validar_peso(cls, v):
        if v <= 0 or v > 50:
            raise ValueError('Peso deve estar entre 0.1 e 50 kg')
        return v
    
    class Config:
        str_strip_whitespace = True


class SubtagInput(BaseModel):
    """Modelo para registrar subtag."""
    
    id_pai: int = Field(..., gt=0)
    letra: str = Field(..., min_length=1, max_length=1)
    cliente: str = Field(..., min_length=1, max_length=100)
    peso: float = Field(..., gt=0, le=50)
    status: str = Field(default="Livre", pattern="^(Livre|Gerado)$")
    
    @validator('letra')
    def validar_letra(cls, v):
        v_upper = v.upper()
        if not v_upper.isalpha():
            raise ValueError('Letra deve ser um caractere alfabético')
        return v_upper
    
    class Config:
        str_strip_whitespace = True


def validar_entrada(modelo, dados: dict):
    """Valida dados usando Pydantic.
    
    Args:
        modelo: Classe Pydantic (ex: PedidoInput)
        dados: Dicionário com dados a validar
        
    Returns:
        Tuple (sucesso, dados_validados_ou_erro)
    """
    try:
        obj_validado = modelo(**dados)
        return True, obj_validado.dict()
    except Exception as e:
        mensagem_erro = str(e)
        return False, mensagem_erro


def renderizar_erro_validacao(erro: str):
    """Renderiza erro de validação no Streamlit.
    
    Args:
        erro: Mensagem de erro
    """
    st.error(f"❌ Erro de validação:\n{erro}")
