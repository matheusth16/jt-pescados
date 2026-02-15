# 🐟 JT Pescados

Sistema interno de gestão de pedidos, clientes e estoque de salmão da JT Pescados.

## Tecnologias

- **Python** + Streamlit
- **Supabase** (banco de dados)
- **Pandas** + Plotly

## Requisitos

- Python 3.10+
- Conta no [Supabase](https://supabase.com) com as tabelas configuradas

## Instalação

1. **Clone o repositório**

   ```bash
   git clone https://github.com/seu-usuario/jt-pescados.git
   cd jt-pescados
   ```

2. **Crie um ambiente virtual** (recomendado)

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Instale as dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente**

   ```bash
   cp .env.example .env
   ```

   Edite o arquivo `.env` e preencha com suas credenciais do Supabase:

   ```
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua_service_role_key_aqui
   ```

   As credenciais estão em: **Supabase Dashboard → Project Settings → API**

5. **Execute a aplicação**

   ```bash
   streamlit run app.py
   ```

   Acesse em: **http://localhost:8501**

## Estrutura do projeto

```
jt-pescados/
├── app.py              # Entrada principal, login, roteamento
├── migrate_senhas.py   # Migração de senhas para hash (uso único)
├── resetar_senha.py    # Reset de senha de usuário
├── core/
│   └── config.py       # Configurações e constantes
├── services/
│   ├── database.py     # Acesso ao Supabase
│   └── utils.py        # Utilitários
├── ui/
│   ├── components.py   # Componentes reutilizáveis
│   ├── styles.py       # Estilos e tema
│   └── pages/          # Páginas do sistema
└── requirements.txt
```

## Perfis de acesso

- **Admin**: Novo Pedido, Dashboard, Gerenciar, Salmão, Clientes
- **Operador**: Operações, Salmão, Indicadores

## Manutenção (Scripts)

Scripts de linha de comando para administração do sistema. Execute na raiz do projeto, com o `.env` configurado.

### migrate_senhas.py

Converte senhas em texto plano para hash Argon2 na tabela `usuarios`. **Execute apenas uma vez** ao migrar de um sistema antigo.

```bash
python migrate_senhas.py
```

- Ignora usuários que já possuem hash (`$argon2` ou `$2b$`)
- Ignora usuários com senha vazia

### resetar_senha.py

Redefine a senha de um usuário. Use quando alguém esquecer a senha.

1. Abra `resetar_senha.py` e edite as variáveis:

   ```
   LOGIN = "usuario_aqui"      # login do usuário
   NOVA_SENHA = "SenhaNova123" # senha temporária
   ```

2. Execute:

   ```bash
   python resetar_senha.py
   ```

3. Informe a senha temporária ao usuário por um canal seguro.

## Deploy (Streamlit Cloud, Railway, etc.)

1. Configure as variáveis `SUPABASE_URL` e `SUPABASE_KEY` nas configurações do serviço.
2. O comando de início deve ser: `streamlit run app.py`
