# 🚀 QUICK START - Começar a Usar as Novas Funcionalidades

## 1️⃣ Instalação (30 segundos)

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar app
streamlit run app.py
```

✅ **Pronto!** Sistema roda com todas as novas funcionalidades.

---

## 2️⃣ Testar Autenticação Segura

### Teste Rate Limiting:
1. Abrir app em: `http://localhost:8501`
2. Na tela de login, digitar usuário correto + senha ERRADA
3. Tentar 5 vezes errado
4. Na 5ª tentativa: ❌ "Acesso bloqueado! Tente novamente em 300 segundos"
5. Verificar arquivo: `logs/JTpescados.log`

```json
// Log de exemplo
{
  "timestamp": "2025-02-17T12:30:45.123Z",
  "nivel": "SEGURANCA",
  "evento": "LOGIN_BLOQUEADO",
  "usuario": "admin",
  "motivo": "excesso_tentativas"
}
```

---

## 3️⃣ Testar Validação de Entrada

### Tentar criar pedido INVÁLIDO:
1. Ir para "📝 Novo Pedido"
2. Nome do cliente: vazio
3. Clicar em "Confirmar"
4. ❌ Vê erro: "Validação falhou: nome_cliente - campo obrigatório"

### Tentar criar cliente com CNPJ inválido:
1. Ir para "➕ Clientes"
2. Nome: "Empresa XYZ"
3. CNPJ: "12345" (apenas 5 dígitos)
4. Clicar em "SALVAR"
5. ❌ Vê erro: "⚠️ Documento Inválido! Detectamos 5 dígitos."

---

## 4️⃣ Monitorar Performance

### Verificar alertas de função lenta:
1. Criar vários pedidos
2. Ir para "👁️ Gerenciar" (atualiza dados)
3. Observar no console/stderr:
   ```
   ⚠️ AVISO: salvar_pedido levou 2.5s (> 2s)
   🔴 CRÍTICO: atualizar_pedidos_editaveis levou 5.8s (> 5s)
   ```

### Verificar logs de performance:
```bash
# Abrir arquivo de log
tail -f logs/JTpescados.log

# Procurar por performance
grep "PERFORMANCE" logs/JTpescados.log
```

---

## 5️⃣ Configurar Notificações por Email

### Para Gmail (recomendado):

1. **Gerar "Senha de App":**
   - Acessar: https://myaccount.google.com/apppasswords
   - Selecionar "App: Mail" e "Device: Windows Computer"
   - Clicar gerar (vai dar 16 caracteres)

2. **Atualizar .env:**
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   EMAIL_REMETENTE=seu-email@gmail.com
   SENHA_EMAIL=xxx xxx xxx xxx  # Cola aqui os 16 caracteres
   EMAIL_ADMIN=seu-email@gmail.com
   ```

3. **Testar:**
   ```python
   from services.notifications import GerenciadorNotificacoes
   
   notif = GerenciadorNotificacoes()
   sucesso = notif.enviar_email(
       para="seu-email@gmail.com",
       assunto="Teste de Email",
       corpo_html="<h1>Funcionou!</h1>"
   )
   print("Email enviado!" if sucesso else "Falhou")
   ```

---

## 6️⃣ Usar Logging Estruturado

### Adicionar logs em seu código:

```python
from services.logging_module import LoggerStructurado

# Criar logger para seu módulo
logger = LoggerStructurado("meu_modulo")

# Log simples (INFO)
logger.info("OPERACAO_INICIADA", {"operacao": "calcular_estoque"})

# Log de aviso
logger.aviso("ESTOQUE_BAIXO", {"produto": "salmao", "qtd": 5})

# Log de erro
try:
    resultado = 10 / 0
except Exception as e:
    logger.erro("ERRO_CALCULO", {"erro": str(e)})

# Log de segurança
logger.seguranca("ACESSO_NEGADO", {
    "usuario": "joao",
    "recurso": "relatorio_financeiro"
})
```

### Verificar logs:
```bash
# Ver todos os logs
tail -100 logs/JTpescados.log

# Ver apenas erros
grep "ERRO" logs/JTpescados.log

# Ver apenas eventos de segurança
grep "SEGURANCA" logs/JTpescados.log

# Com timestamps
grep "2025-02-17" logs/JTpescados.log
```

---

## 7️⃣ Usar Rate Limiting Customizado

### Implementar em sua função:

```python
from services.rate_limiter import registrar_tentativa, limpar_rate_limit_login
import streamlit as st

def minha_funcao_sensivel(usuario):
    # Registrar tentativa
    permitido, restantes, segundos = registrar_tentativa(usuario)
    
    if not permitido:
        st.error(f"🔒 Bloqueado por {segundos}s. Tente novamente depois.")
        return
    
    st.success("✅ Acesso permitido!")
    
    # ... fazer algo importante ...
    
    # Limpar rate limit após sucesso
    limpar_rate_limit_login(usuario)
```

---

## 8️⃣ Usar Monitoramento de Performance

### Decorar suas funções:

```python
from services.monitor_performance import MonitorPerformance

@MonitorPerformance.monitorar(nome_funcao="processar_grande_arquivo")
def processar_arquivo_grande(arquivo):
    # seu código aqui
    import time
    time.sleep(3)  # Vai mostrar aviso (> 2s)
    return "Processado!"

# Chamar função (vai rastrear tempo)
resultado = processar_arquivo_grande("dados.xlsx")
```

### Ver estatísticas:

```python
from services.monitor_performance import MonitorPerformance

# Executar função 100 vezes e obter estatísticas
stats = MonitorPerformance.benchmark(processar_arquivo_grande, iteracoes=100)

print(f"Tempo mínimo: {stats['min']}ms")
print(f"Tempo máximo: {stats['max']}ms")
print(f"Tempo médio: {stats['media']}ms")
print(f"Desvio padrão: {stats['stdev']}ms")
```

---

## 9️⃣ Usar Validação Pydantic

### Validar dados antes de salvar:

```python
from services.validators import validar_entrada, PedidoInput

# Dados que vêm do formulário
dados = {
    "nome_cliente": "João Silva",
    "descricao": "10kg de tilápia",
    "data_entrega": "2025-02-20",
    "pagamento": "PIX",
    "status": "PENDENTE"
}

# Validar
sucesso, resultado = validar_entrada(PedidoInput, dados)

if sucesso:
    print("✅ Dados válidos!")
    print(resultado)  # PedidoInput object
else:
    print("❌ Erro de validação!")
    print(resultado)  # Mensagem de erro
```

---

## 🔟 Rodar Testes

### Executar suite completa:

```bash
# Rodar todos os testes
python -m pytest tests/test_all.py -v

# Rodar com cobertura
python -m pytest tests/test_all.py -v --cov=services --cov=ui

# Rodar um teste específico
python -m pytest tests/test_all.py::TestGerenciadorSenha::test_gerar_hash -v

# Rodar apenas testes de segurança
python -m pytest tests/test_all.py -k "rate_limit" -v
```

### Resultado esperado:
```
======================== 17 passed in 0.97s ========================
✅ TODAS AS FUNCIONALIDADES FUNCIONANDO!
```

---

## 1️⃣1️⃣ Estrutura de Pastas Importante

```
jt-pescados/
├── services/              # Módulos principais
│   ├── auth.py            # Autenticação Argon2
│   ├── logging_module.py   # Logging JSON
│   ├── rate_limiter.py     # Rate limiting
│   ├── validators.py       # Validação Pydantic
│   ├── soft_delete.py      # Soft delete
│   ├── monitor_performance.py  # Performance
│   └── notifications.py    # Email
├── ui/
│   └── pages/
│       ├── pedidos.py      # Novo: validação integrada
│       └── clientes.py     # Novo: validação integrada
├── logs/                   # 📁 Gerado automaticamente
│   └── JTpescados.log      # Log principal (rotaciona em 5MB)
├── tests/
│   └── test_all.py         # 17 testes
├── .env                    # Configurações (EMAIL, SMTP)
├── requirements.txt        # Dependências
├── IMPLEMENTACOES.md       # Documentação detalhada
├── DEPLOY_CHECKLIST.md     # Guia de deploy
└── RESUMO_FINAL.md         # Este guia

```

---

## ⚠️ Troubleshooting Rápido

### "Erro: ModuleNotFoundError: No module named 'services.auth'"
```bash
pip install -r requirements.txt
```

### "Email não envia"
- Verificar .env tem EMAIL_REMETENTE e SENHA_EMAIL
- Usar "Senha de App" (não senha comum) para Gmail
- Porta 587 aberta

### "Rate limit não funciona"
- É esperado resetar ao reload do app (Streamlit behavior)
- Cada user tem seu próprio counter
- Limpa com `limpar_rate_limit_login(usuario)`

### "Logs não aparecem"
- Verificar pasta `logs/` existe
- Arquivo `JTpescados.log` deve ter sido criado
- Ver com: `tail -f logs/JTpescados.log`

---

## 📞 Próximas Ações Recomendadas

- [ ] Rodar `python -m pytest tests/test_all.py -v` (verificar tudo)
- [ ] Testar login com rate limit (5 tentativas)
- [ ] Criar pedido e verificar validação
- [ ] Configurar email (se necessário)
- [ ] Revisar arquivo `logs/JTpescados.log`
- [ ] Ler `IMPLEMENTACOES.md` para detalhes técnicos
- [ ] Seguir `DEPLOY_CHECKLIST.md` para deploy

---

## ✨ Você Está Pronto!

Sistema **100% funcional** com todas as melhorias.

**Bom trabalho!** 🚀

