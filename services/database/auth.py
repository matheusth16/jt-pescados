"""
Autenticação de usuários.
"""
import streamlit as st

from services.database.client import get_db_client


def autenticar_usuario(login_digitado, senha_digitada):
    from services.utils import verificar_senha

    client = get_db_client()
    try:
        response = client.table("usuarios")\
            .select("LOGIN, SENHA, NOME, PERFIL")\
            .eq("LOGIN", str(login_digitado).strip())\
            .limit(1)\
            .execute()

        if not response.data:
            return None

        user = response.data[0]
        hash_armazenado = user.get("SENHA") or ""

        if verificar_senha(senha_digitada, hash_armazenado):
            return {"nome": user.get('NOME', 'Usuário'), "perfil": user.get('PERFIL', 'Operador')}
    except Exception as e:
        st.error(f"Erro ao autenticar: {e}")
    return None
