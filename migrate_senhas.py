# migrate_senhas.py (executar uma vez)
from supabase import create_client
from services.utils import hash_senha
from core.config import SUPABASE_URL, SUPABASE_KEY

client = create_client(SUPABASE_URL, SUPABASE_KEY)

response = client.table("usuarios").select("LOGIN, SENHA").execute()

for user in response.data:
    login = user["LOGIN"]
    senha_atual = user.get("SENHA", "")
    
    # Se a senha parece hash (começa com $2b$ ou $argon2), pula
    if senha_atual and (senha_atual.startswith("$2b$") or senha_atual.startswith("$argon2")):
        print(f"{login}: já possui hash")
        continue
    
    if not senha_atual:
        print(f"{login}: senha vazia, ignorando")
        continue
    
    hash_novo = hash_senha(senha_atual)
    client.table("usuarios").update({"SENHA": hash_novo}).eq("LOGIN", login).execute()
    print(f"{login}: migrado com sucesso")