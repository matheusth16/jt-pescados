"""
Suite de testes para JT Pescados.
Execute com: pytest tests/
"""

import pytest
from datetime import date, datetime, timedelta
from services.auth import GerenciadorSenha, gerenciador_senha
from services.validators import PedidoInput, ClienteInput, SalmaoInput, SubtagInput, validar_entrada
from services.rate_limiter import RateLimiter, verificar_rate_limit_login
from pydantic import ValidationError


# ============================================================
# TESTES DE AUTENTICAÇÃO E SEGURANÇA
# ============================================================

class TestGerenciadorSenha:
    """Testes de hash e verificação de senhas."""
    
    def test_gerar_hash(self):
        """Testa geração de hash."""
        senha = "MinhaSenha123!"
        hash_gerado = gerenciador_senha.gerar_hash(senha)
        
        assert hash_gerado.startswith("$argon2")
        assert hash_gerado != senha  # Não armazena em texto plano
    
    def test_verificar_senha_correta(self):
        """Testa verificação de senha correta."""
        senha = "SenhaCorreta"
        hash_gerado = gerenciador_senha.gerar_hash(senha)
        
        assert gerenciador_senha.verificar(senha, hash_gerado) is True
    
    def test_verificar_senha_incorreta(self):
        """Testa verificação com senha errada."""
        senha_correta = "SenhaCorreta"
        senha_errada = "SenhaErrada"
        hash_gerado = gerenciador_senha.gerar_hash(senha_correta)
        
        assert gerenciador_senha.verificar(senha_errada, hash_gerado) is False
    
    def test_eh_hash_valido(self):
        """Testa identificação de hashes válidos."""
        hash_valido = gerenciador_senha.gerar_hash("teste")
        
        assert gerenciador_senha.eh_hash_valido(hash_valido) is True
        assert gerenciador_senha.eh_hash_valido("senha_em_texto_plano") is False


# ============================================================
# TESTES DE VALIDAÇÃO
# ============================================================

class TestValidadores:
    """Testes de validação com Pydantic."""
    
    def test_pedido_valido(self):
        """Testa validação de pedido válido."""
        dados = {
            "nome_cliente": "João Silva",
            "descricao": "Pedido de salmão fresco",
            "data_entrega": date.today() + timedelta(days=5),
            "pagamento": "PIX",
            "status": "PENDENTE"
        }
        
        sucesso, resultado = validar_entrada(PedidoInput, dados)
        assert sucesso is True
        assert resultado["nome_cliente"] == "João Silva"
    
    def test_pedido_nome_curto(self):
        """Testa rejeição de nome muito curto."""
        dados = {
            "nome_cliente": "Jo",  # Muito curto
            "descricao": "Pedido de salmão fresco",
            "data_entrega": date.today() + timedelta(days=5),
            "pagamento": "PIX",
            "status": "PENDENTE"
        }
        
        sucesso, resultado = validar_entrada(PedidoInput, dados)
        assert sucesso is False
        assert "min_length" in resultado or "3" in resultado
    
    def test_pedido_data_passada(self):
        """Testa rejeição de data no passado."""
        dados = {
            "nome_cliente": "João Silva",
            "descricao": "Pedido de salmão fresco",
            "data_entrega": date.today() - timedelta(days=1),  # Passado!
            "pagamento": "PIX",
            "status": "PENDENTE"
        }
        
        sucesso, resultado = validar_entrada(PedidoInput, dados)
        assert sucesso is False
        assert "passado" in resultado.lower()
    
    def test_cliente_valido(self):
        """Testa validação de cliente válida."""
        dados = {
            "nome": "Restaurante Silva",
            "cidade": "São Paulo",
            "documento": "12345678901"  # CPF válido
        }
        
        sucesso, resultado = validar_entrada(ClienteInput, dados)
        assert sucesso is True
    
    def test_cliente_documento_invalido(self):
        """Testa rejeição de documento inválido."""
        dados = {
            "nome": "Restaurante Silva",
            "cidade": "São Paulo",
            "documento": "123"  # Muito curto
        }
        
        sucesso, resultado = validar_entrada(ClienteInput, dados)
        assert sucesso is False
    
    def test_salmao_valido(self):
        """Testa validação de salmão válida."""
        dados = {
            "tag": 100,
            "peso": 5.5,
            "calibre": "Large",
            "cliente": "Restaurant X",
            "status": "Livre"
        }
        
        sucesso, resultado = validar_entrada(SalmaoInput, dados)
        assert sucesso is True
    
    def test_salmao_peso_invalido(self):
        """Testa rejeição de peso inválido."""
        dados = {
            "tag": 100,
            "peso": 100.0,  # Muito pesado!
            "calibre": "Large",
            "cliente": "Restaurant X"
        }
        
        sucesso, resultado = validar_entrada(SalmaoInput, dados)
        assert sucesso is False


# ============================================================
# TESTES DE RATE LIMITING
# ============================================================

class TestRateLimiter:
    """Testes de rate limiting."""
    
    def test_inicializar_session(self):
        """Testa inicialização de session."""
        RateLimiter.inicializar_session()
        # Se não lançar exceção, passou
        assert True
    
    def test_rate_limit_permitido(self):
        """Testa primeiras tentativas permitidas."""
        RateLimiter.inicializar_session()
        
        for i in range(5):
            permitido, restantes, bloqueado = RateLimiter.registrar_tentativa(f"teste_{i}")
            assert permitido is True
            assert restantes > 0
    
    def test_rate_limit_bloqueado(self):
        """Testa bloqueio após excesso de tentativas."""
        RateLimiter.inicializar_session()
        chave = "teste_bloqueio"
        
        # Realizar 6 tentativas (máximo é 5)
        for i in range(6):
            RateLimiter.registrar_tentativa(chave)
        
        # 7ª tentativa deve ser bloqueada
        permitido, restantes, bloqueado = RateLimiter.registrar_tentativa(chave)
        assert permitido is False
        assert bloqueado > 0
    
    def test_limpar_tentativas(self):
        """Testa limpeza de tentativas após sucesso."""
        RateLimiter.inicializar_session()
        chave = "teste_limpar"
        
        # Registrar tentativa
        RateLimiter.registrar_tentativa(chave)
        
        # Limpar
        RateLimiter.limpar_tentativas(chave)
        
        # Nova tentativa deve começar do zero
        permitido, restantes, _ = RateLimiter.registrar_tentativa(chave)
        assert permitido is True
        assert restantes == 4  # Max - 1


# ============================================================
# TESTES DE INTEGRAÇÃO
# ============================================================

class TestIntegracao:
    """Testes de integração entre módulos."""
    
    def test_fluxo_login_seguro(self):
        """Testa fluxo completo de login seguro."""
        # 1. Gerar hash de senha
        senha_usuario = "Senha123!"
        hash_armazenado = gerenciador_senha.gerar_hash(senha_usuario)
        
        # 2. Verificar login
        senha_digitada = "Senha123!"
        assert gerenciador_senha.verificar(senha_digitada, hash_armazenado) is True
        
        # 3. Senha errada deve falhar
        assert gerenciador_senha.verificar("SenhaErrada", hash_armazenado) is False
    
    def test_validacao_e_rate_limit(self):
        """Testa validação + rate limit juntos."""
        RateLimiter.inicializar_session()
        
        # 1. Validar entrada
        dados = {
            "nome_cliente": "Cliente Teste",
            "descricao": "Descrição",
            "data_entrega": date.today() + timedelta(days=1),
            "pagamento": "PIX",
            "status": "PENDENTE"
        }
        
        sucesso, resultado = validar_entrada(PedidoInput, dados)
        assert sucesso is True
        
        # 2. Rate limit
        permitido, msg = verificar_rate_limit_login("cliente_teste")
        assert permitido is True


# ============================================================
# FIXTURES E UTILITÁRIOS
# ============================================================

@pytest.fixture
def gerenciador():
    """Fixture para GerenciadorSenha."""
    return GerenciadorSenha()


@pytest.fixture
def dados_pedido_valido():
    """Fixture com dados de pedido válido."""
    return {
        "nome_cliente": "João Silva",
        "descricao": "Pedido de salmão fresco",
        "data_entrega": date.today() + timedelta(days=5),
        "pagamento": "PIX",
        "status": "PENDENTE"
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
