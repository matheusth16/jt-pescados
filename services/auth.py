"""
Módulo de autenticação e segurança.
Gerencia hash de senhas, verificação e migração.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError
import streamlit as st


class GerenciadorSenha:
    """Gerencia hashing e verificação segura de senhas com Argon2."""
    
    def __init__(self):
        self.ph = PasswordHasher()
    
    def gerar_hash(self, senha: str) -> str:
        """Gera hash Argon2 de uma senha.
        
        Args:
            senha: Senha em texto plano
            
        Returns:
            Hash Argon2 da senha
        """
        return self.ph.hash(senha.strip())
    
    def verificar(self, senha: str, hash_armazenado: str) -> bool:
        """Verifica se uma senha corresponde ao hash.
        
        Args:
            senha: Senha em texto plano
            hash_armazenado: Hash Argon2 armazenado no BD
            
        Returns:
            True se a senha é válida, False caso contrário
        """
        try:
            self.ph.verify(hash_armazenado, senha.strip())
            return True
        except (InvalidHash, VerificationError, Exception):
            return False
    
    def eh_hash_valido(self, valor: str) -> bool:
        """Verifica se uma string é um hash Argon2 válido.
        
        Usado para identificar senhas já hashadas na migração.
        
        Args:
            valor: String a verificar
            
        Returns:
            True se é um hash Argon2, False caso contrário
        """
        try:
            # Hashes Argon2 começam com $argon2
            return valor.startswith("$argon2")
        except:
            return False


# Instância global
gerenciador_senha = GerenciadorSenha()


def autenticar_usuario_seguro(client, login_digitado: str, senha_digitada: str) -> dict | None:
    """Autentica usuário com verificação segura de hash.
    
    Args:
        client: Cliente Supabase
        login_digitado: Login fornecido pelo usuário
        senha_digitada: Senha fornecida pelo usuário
        
    Returns:
        Dict com nome e perfil do usuário, ou None se inválido
    """
    try:
        # Buscar usuário pelo login
        response = client.table("usuarios")\
            .select("NOME, PERFIL, SENHA")\
            .eq("LOGIN", str(login_digitado).strip())\
            .execute()
        
        if not response.data:
            return None
        
        user = response.data[0]
        hash_armazenado = user.get("SENHA", "")
        
        # Verificar senha com hash
        if not gerenciador_senha.verificar(senha_digitada, hash_armazenado):
            return None
        
        return {
            "nome": user.get('NOME', 'Usuário'),
            "perfil": user.get('PERFIL', 'Operador')
        }
        
    except Exception as e:
        st.error(f"❌ Erro ao autenticar: {e}")
        return None


def migrar_senhas_para_hash(client):
    """Migra senhas em texto plano para Argon2.
    
    Ignora usuários que já possuem hash ou senhas vazias.
    
    Args:
        client: Cliente Supabase
        
    Returns:
        Tuple (total_migrado, total_ignorado)
    """
    try:
        # Buscar todos os usuários
        response = client.table("usuarios").select("LOGIN, SENHA, NOME").execute()
        
        if not response.data:
            return 0, 0
        
        migrado = 0
        ignorado = 0
        
        for user in response.data:
            login = user.get("LOGIN")
            senha = user.get("SENHA", "")
            
            # Ignorar se vazio ou já é hash
            if not senha or gerenciador_senha.eh_hash_valido(senha):
                ignorado += 1
                continue
            
            # Gerar hash
            novo_hash = gerenciador_senha.gerar_hash(senha)
            
            # Atualizar no BD
            try:
                client.table("usuarios").update({
                    "SENHA": novo_hash
                }).eq("LOGIN", login).execute()
                
                migrado += 1
                print(f"✅ Migrado: {login}")
            except Exception as e:
                print(f"❌ Erro ao migrar {login}: {e}")
                ignorado += 1
        
        return migrado, ignorado
    
    except Exception as e:
        st.error(f"❌ Erro na migração: {e}")
        return 0, 0
