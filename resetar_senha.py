# resetar_senha.py
from supabase import create_client
from services.utils import hash_senha
from core.config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

LOGIN = "usuario_aqui"   # login do usuário
NOVA_SENHA = "SenhaNova123"  # senha nova que você define

hash_novo = hash_senha(NOVA_SENHA)
client.table("usuarios").update({"SENHA": hash_novo}).eq("LOGIN", LOGIN).execute()

print(f"Senha do usuário {LOGIN} atualizada com sucesso.")
print(f"Informe ao usuário a senha temporária: {NOVA_SENHA}")