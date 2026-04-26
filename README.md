# Workshop Management API

MVP de sistema integrado para gestão de oficina mecânica, construído com FastAPI seguindo Arquitetura em Camadas (Controller → Service → Repository).

## Requisitos

- Python 3.11+
- pip

---

## Execução local

### 1. Clone e acesse o projeto

```bash
git clone <url-do-repositorio>
cd workshop-management-api
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

O `.env` padrão já vem configurado para SQLite, sem necessidade de nenhum serviço externo:

```env
DATABASE_URL=sqlite+aiosqlite:///./workshop.db
SECRET_KEY=dev-secret-key-please-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 5. Inicie a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`.

---

## Documentação interativa

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| Redoc | http://localhost:8000/redoc |

---

## Autenticação

Todas as rotas administrativas exigem JWT. Siga os passos abaixo no Swagger:

1. **Crie um usuário** — `POST /auth/register`
2. **Faça login** — clique em **Authorize** (cadeado), preencha `username` e `password`, deixe `client_id` e `client_secret` em branco e clique em **Authorize**
3. Todas as requisições seguintes já enviam o token automaticamente

> A rota `GET /service-orders/{id}/status` é pública — clientes podem consultar o status da OS sem autenticação.

---

## Rotas disponíveis

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/auth/register` | Cadastrar usuário administrativo |
| POST | `/auth/login` | Autenticar e obter token |
| GET | `/auth/me` | Dados do usuário autenticado |
| GET / POST | `/clients` | Listar / cadastrar clientes |
| GET / PATCH / DELETE | `/clients/{id}` | Detalhar / atualizar / remover cliente |
| GET / POST | `/vehicles` | Listar / cadastrar veículos |
| GET / PATCH / DELETE | `/vehicles/{id}` | Detalhar / atualizar / remover veículo |
| GET | `/vehicles/client/{id}` | Veículos de um cliente |
| GET / POST | `/service-types` | Listar / cadastrar tipos de serviço |
| GET / PATCH / DELETE | `/service-types/{id}` | Detalhar / atualizar / remover serviço |
| GET / POST | `/parts` | Listar / cadastrar peças e insumos |
| GET / PATCH / DELETE | `/parts/{id}` | Detalhar / atualizar / remover peça |
| POST | `/parts/{id}/stock` | Ajustar estoque (positivo ou negativo) |
| GET / POST | `/service-orders` | Listar / criar ordens de serviço |
| GET | `/service-orders/{id}` | Detalhar ordem de serviço |
| PATCH | `/service-orders/{id}/status` | Atualizar status da OS |
| GET | `/service-orders/{id}/status` | Consultar status (rota pública) |
| GET | `/service-orders/metrics/average-execution-time` | Tempo médio de execução |

### Status possíveis da OS (em ordem)

```
RECEBIDA → EM_DIAGNOSTICO → AGUARDANDO_APROVACAO → EM_EXECUCAO → FINALIZADA → ENTREGUE
```

---

## Testes

```bash
pytest
```

Para ver a cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Execução com Docker

Necessário ter Docker e Docker Compose instalados.

```bash
# Copie e ajuste o .env para usar PostgreSQL
cp .env.example .env

# Suba o ambiente (banco + API)
docker-compose up --build
```

A API estará disponível em `http://localhost:8000`.

---

## Estrutura do projeto

```
app/
├── main.py               # Entrypoint FastAPI
├── core/                 # Config, banco, segurança, dependências
├── controllers/          # Camada HTTP (recebe request, retorna response)
├── services/             # Regras de negócio
├── repositories/         # Acesso ao banco de dados
├── models/               # Modelos ORM (SQLAlchemy)
├── schemas/              # Schemas de entrada/saída (Pydantic)
└── exceptions/           # Exceções de domínio
tests/
├── unit/                 # Testes unitários (validações, regras)
└── integration/          # Testes de integração (endpoints completos)
```
