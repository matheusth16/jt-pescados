from pydantic import BaseModel, Field, validator
from typing import Optional

class PedidoSchema(BaseModel):
    ID_PEDIDO: int
    CARIMBO_DE_DATA_HORA: str = Field(..., alias="CARIMBO DE DATA/HORA")
    COD_CLIENTE: Optional[int] = Field(None, alias="COD CLIENTE")
    NOME_CLIENTE: str = Field(..., alias="NOME CLIENTE", min_length=2)
    PEDIDO: str = Field(..., min_length=1)
    DIA_DA_ENTREGA: str = Field(..., alias="DIA DA ENTREGA")
    PAGAMENTO: str
    STATUS: str
    NR_PEDIDO: Optional[str] = Field("", alias="NR PEDIDO")
    OBSERVAÇÃO: Optional[str] = Field("")
    CIDADE: str
    ROTA: str

    # Permite usar os nomes das variáveis (ID_PEDIDO) ou os nomes do banco (ID PEDIDO)
    class Config:
        populate_by_name = True 

    @validator('STATUS')
    def validar_status(cls, v):
        # Garante que o status está sempre em maiúsculas e é um dos permitidos
        permitidos = ["ORÇAMENTO", "GERADO", "ENTREGUE", "CANCELADO"]
        if v.upper() not in permitidos:
            raise ValueError(f"Status {v} não é permitido.")
        return v.upper()