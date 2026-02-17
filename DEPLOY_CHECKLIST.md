# 📋 CHECKLIST DE DEPLOY - JT Pescados

## ✅ Antes de Colocar em Produção

### 1. Ambiente Local ✅
- [x] Todos os 17 testes passando
- [x] Sem erros de sintaxe
- [x] Sem warnings críticos
- [x] Imports validados

### 2. Dependências ✅
- [x] `requirements.txt` atualizado
- [x] Todas as bibliotecas instaladas
  ```bash
  pip install -r requirements.txt
  ```

### 3. Configuração de Variáveis .env ✅
- [x] `.env` criado com configurações de email
- [x] **IMPORTANTE**: Não fazer commit do `.env` com credenciais reais
  
  Adicionar ao `.gitignore`:
  ```
  .env
  .env.local
  .env.*.local
  logs/
  __pycache__/
  *.pyc
  .pytest_cache/
  ```

### 4. Migração de Senhas (Uma Única Vez)
- [ ] Executar script de migração:
  ```bash
  python migrate_senhas.py
  ```
  **Nota**: Isso vai hashear todas as senhas antigas com Argon2
  
  **Output esperado**:
  ```
  ============================================================
  MIGRAÇÃO DE SENHAS PARA ARGON2
  ============================================================

  📊 Total de usuários: 3
  ────────────────────────────────────────────────────────────
  🔐 user1: migrado com sucesso para Argon2
  🔐 user2: migrado com sucesso para Argon2
  🔐 user3: migrado com sucesso para Argon2
  ────────────────────────────────────────────────────────────

  📈 RESUMO DA MIGRAÇÃO:
    ✅ Migrados: 3/3
    ✓ Já hashados: 0
    ⚠️  Vazios: 0
    Total processado: 3
  ────────────────────────────────────────────────────────────

  ✨ Migração concluída com sucesso!
  ```

### 5. Banco de Dados - Soft Delete (Opcional)
Se deseja usar soft delete, executar no Supabase SQL Editor:
```sql
-- Adicionar colunas para soft delete
ALTER TABLE pedidos ADD COLUMN DELETADO_EM TIMESTAMP NULL;
ALTER TABLE pedidos ADD COLUMN DELETADO_POR VARCHAR(100) NULL;

ALTER TABLE clientes ADD COLUMN DELETADO_EM TIMESTAMP NULL;
ALTER TABLE clientes ADD COLUMN DELETADO_POR VARCHAR(100) NULL;

ALTER TABLE estoque_salmao ADD COLUMN DELETADO_EM TIMESTAMP NULL;
ALTER TABLE estoque_salmao ADD COLUMN DELETADO_POR VARCHAR(100) NULL;
```

### 6. Configuração de Email (Produção)

#### Para Gmail:
1. Acessar: https://myaccount.google.com/apppasswords
2. Gerar "Senha de App" (16 caracteres)
3. Atualizar `.env`:
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_REMETENTE=seu-email@gmail.com
   SENHA_EMAIL=sua-senha-de-app-16-chars
   ```

#### Para Outlook:
   ```env
   SMTP_SERVER=smtp-mail.outlook.com
   SMTP_PORT=587
   EMAIL_REMETENTE=seu-email@outlook.com
   SENHA_EMAIL=sua-senha
   ```

#### Para Servidor Corporativo:
   ```env
   SMTP_SERVER=seu.servidor.com
   SMTP_PORT=587
   EMAIL_REMETENTE=sistema@empresa.com
   SENHA_EMAIL=sua-senha
   ```

### 7. Testes em Produção
- [ ] Testar login com rate limiting:
  1. Abrir app em nova aba
  2. Tentar 5 vezes errado
  3. Verificar bloqueio de 5 minutos
  
- [ ] Testar criação de pedido:
  1. Criar novo pedido
  2. Verificar validação Pydantic
  3. Verificar log em `/logs/JTpescados.log`
  
- [ ] Testar notificações (se email configurado):
  1. Criar novo pedido
  2. Verificar email de notificação

### 8. Monitoramento
- [ ] Verificar pasta `/logs/` existe e tem arquivos
- [ ] Revisar logs para erros:
  ```bash
  tail -f logs/JTpescados.log
  ```

### 9. Performance
- [ ] Testar operações lentas (> 2s aparecem aviso)
- [ ] Verificar cache de clientes (5 min TTL)
- [ ] Verificar cache de estoque (30s TTL)

---

## 🚀 Instruções de Deploy

### Deploy em Servidor Local:
```bash
# 1. Clonar repositório
git clone <seu-repo>
cd jt-pescados

# 2. Criar virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar .env com valores reais
# (não usar o template, substituir com credenciais reais)

# 5. Migrar senhas (uma única vez!)
python migrate_senhas.py

# 6. Executar app
streamlit run app.py
```

### Deploy em Streamlit Cloud:
1. Fazer push do código para GitHub
2. No Streamlit Cloud, conectar repositório
3. Configurar secrets em "Advanced Settings":
   ```
   SUPABASE_URL = "..."
   SUPABASE_KEY = "..."
   SMTP_SERVER = "..."
   EMAIL_REMETENTE = "..."
   SENHA_EMAIL = "..."
   ```
4. Deploy automático!

### Deploy em Docker:
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t jt-pescados .
docker run -p 8501:8501 --env-file .env jt-pescados
```

---

## 📊 Verificação Pós-Deploy

### 1. Health Check
- [ ] App carrega sem erro
- [ ] Login funciona
- [ ] Dashboard carrega
- [ ] Criação de pedido funciona

### 2. Segurança
- [ ] Senhas hasheadas com Argon2
- [ ] Rate limiting funcionando
- [ ] Logs de segurança sendo gravados
- [ ] Email seguro (não expõe credenciais)

### 3. Logs
- [ ] Arquivo `logs/JTpescados.log` existe
- [ ] Rotação automática funcionando (5MB)
- [ ] Informações úteis nos logs

### 4. Performance
- [ ] Cache de clientes funcionando (5 min)
- [ ] Cache de estoque funcionando (30s)
- [ ] Monitoramento de funções lentas ativo

---

## 🔍 Troubleshooting

### Problema: "ModuleNotFoundError: No module named 'services.auth'"
**Solução**:
```bash
pip install -r requirements.txt
```

### Problema: Email não envia
**Checklist**:
- [ ] SMTP_SERVER está correto
- [ ] EMAIL_REMETENTE está correto
- [ ] SENHA_EMAIL é "Senha de App" (não senha comum) para Gmail
- [ ] Porta 587 está aberta
- [ ] Variáveis estão em `.env` (não em código)

### Problema: Rate limiting não funciona
**Causa**: Session state do Streamlit reseta ao recarregar app
**Solução**: Comportamento esperado - cada sessão tem seu próprio rate limit

### Problema: Testes falhando
**Solução**:
```bash
# Reinstalar dependências
pip install --upgrade pytest pydantic

# Rodar testes com verbose
python -m pytest tests/test_all.py -v --tb=short
```

---

## 📈 Métricas para Monitorar

### Em Produção, Acompanhar:
1. **Taxa de Erro de Login**: Deve ser < 5%
2. **Tempo de Resposta**: Pedidos < 2s
3. **Tamanho de Logs**: Rotam em 5MB automaticamente
4. **Taxa de Bloqueio**: Deve ser baixa se usuários usam senha correta

---

## 🔐 Segurança - Checklist Final

- [ ] `.env` com credenciais não está no Git
- [ ] Senhas no banco estão hasheadas (Argon2)
- [ ] Rate limiting ativo (5 tentativas/5 min)
- [ ] Logs de segurança funcionando
- [ ] Email usa autenticação segura (Senha de App)
- [ ] Validação Pydantic em todas as entradas
- [ ] HTTPS ativo (se em servidor remoto)

---

## ✨ Conclusão

Sistema pronto para produção com:
- ✅ Segurança reforçada
- ✅ Logs estruturados
- ✅ Testes automatizados
- ✅ Notificações automáticas
- ✅ Monitoramento de performance

**Esperado: Deploy suave e sem incidentes** 🚀

---

## 📞 Suporte

Em caso de problemas:
1. Verificar arquivo de log: `logs/JTpescados.log`
2. Rodar testes: `pytest tests/test_all.py -v`
3. Verificar configuração `.env`
4. Consultar documentação em `IMPLEMENTACOES.md`
