# migrate_senhas.py (executar uma vez para migrar senhas antigas para Argon2)
# Uso: python migrate_senhas.py

from supabase import create_client
from services.auth import GerenciadorSenha
from services.logging_module import LoggerStructurado
from core.config import SUPABASE_URL, SUPABASE_KEY

# Inicializar
client = create_client(SUPABASE_URL, SUPABASE_KEY)
gerenciador = GerenciadorSenha()
logger = LoggerStructurado("migrate_senhas")

print("=" * 60)
print("MIGRAÇÃO DE SENHAS PARA ARGON2")
print("=" * 60)

try:
    # Buscar todos os usuários
    response = client.table("usuarios").select("LOGIN, SENHA").execute()
    
    if not response.data:
        print("❌ Nenhum usuário encontrado")
        exit(1)
    
    total = len(response.data)
    migrados = 0
    ja_hashados = 0
    vazios = 0
    
    print(f"\n📊 Total de usuários: {total}")
    print("-" * 60)
    
    for user in response.data:
        login = user["LOGIN"]
        senha_atual = user.get("SENHA", "")
        
        # Se a senha já é hash Argon2, pula
        if gerenciador.eh_hash_valido(senha_atual):
            print(f"✅ {login}: já possui hash Argon2")
            ja_hashados += 1
            continue
        
        # Se senha está vazia, pula
        if not senha_atual or senha_atual.strip() == "":
            print(f"⚠️  {login}: senha vazia, ignorando")
            vazios += 1
            continue
        
        # Gerar novo hash com Argon2
        try:
            hash_novo = gerenciador.gerar_hash(senha_atual)
            client.table("usuarios").update({"SENHA": hash_novo}).eq("LOGIN", login).execute()
            print(f"🔐 {login}: migrado com sucesso para Argon2")
            migrados += 1
            logger.info("USUARIO_MIGRADO", {"usuario": login})
        except Exception as e:
            print(f"❌ {login}: erro na migração: {e}")
            logger.erro("ERRO_MIGRACAO", {"usuario": login, "erro": str(e)})
    
    # Resumo
    print("-" * 60)
    print(f"\n📈 RESUMO DA MIGRAÇÃO:")
    print(f"  ✅ Migrados: {migrados}/{total}")
    print(f"  ✓ Já hashados: {ja_hashados}")
    print(f"  ⚠️  Vazios: {vazios}")
    print(f"  Total processado: {migrados + ja_hashados + vazios}")
    print("-" * 60)
    print("\n✨ Migração concluída com sucesso!\n")
    
except Exception as e:
    print(f"❌ Erro fatal na migração: {e}")
    logger.erro("ERRO_FATAL_MIGRACAO", {"erro": str(e)})
    exit(1)