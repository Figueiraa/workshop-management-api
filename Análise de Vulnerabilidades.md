# 🔐 Relatório com Análise de Vulnerabilidades

## 1. Visão Geral do Scan

A análise estática de segurança foi realizada com a ferramenta **Bandit** (versão 1.9.4), executada sobre o código-fonte do projeto **Workshop Management API**. O Bandit é uma ferramenta SAST (*Static Application Security Testing*) mantida pela comunidade PyCQA, especializada em identificar padrões inseguros em código Python a partir de regras pré-definidas mapeadas para identificadores **CWE** (*Common Weakness Enumeration*).

O relatório completo gerado pelo scan está disponível no arquivo [`relatorio_de_analise_de_vulnerabilidades-bandit.html`](../relatorio_de_analise_de_vulnerabilidades-bandit.html) na raiz do projeto.

### Resumo do Scan

| Métrica | Valor |
|---|---|
| Total de linhas analisadas | 875.390 |
| Linhas ignoradas (`# nosec`) | 9 |
| Ferramenta | Bandit 1.9.4 |
| Escopo | Diretório raiz do projeto (incluindo dependências em `venv/`) |

> 📌 **Observação:** o scan abrangeu também o diretório `venv/` por padrão, o que faz com que muitos achados se refiram a bibliotecas de terceiros. As vulnerabilidades discutidas a seguir foram selecionadas considerando a relevância didática e o impacto em segurança real.

---

## 2. Vulnerabilidades Selecionadas

A seguir, são detalhadas três vulnerabilidades representativas identificadas pelo Bandit. Cada uma é apresentada em três blocos: **definição**, **risco associado** e **estratégia de correção**.

---

### 🔴 Vulnerabilidade 1 — Uso de Algoritmo de Hash Fraco (SHA-1)

| Campo | Valor |
|---|---|
| **Test ID** | B324 (`hashlib`) |
| **CWE** | [CWE-327](https://cwe.mitre.org/data/definitions/327.html) — *Use of a Broken or Risky Cryptographic Algorithm* |
| **Severidade** | 🔴 **ALTA** |
| **Confiança** | ALTA |
| **Local** | `venv/Lib/site-packages/cryptography/x509/extensions.py:72` |
| **Trecho** | `return hashlib.sha1(data).digest()` |

#### O que é

A regra **B324** detecta o uso de algoritmos de hash criptograficamente quebrados ou desaconselhados, como **MD5** e **SHA-1**, em contextos de segurança. O **SHA-1** (*Secure Hash Algorithm 1*) foi publicado em 1995 e, ao longo dos anos, sofreu múltiplos ataques de colisão bem-sucedidos — o mais notório sendo o **SHAttered** (2017), realizado por pesquisadores do Google, que demonstrou ser computacionalmente viável produzir dois documentos distintos com o mesmo hash SHA-1.

#### Risco

O uso de algoritmos de hash fracos compromete diretamente garantias de integridade e autenticidade. Os principais riscos são:

- **Ataques de colisão:** um adversário pode forjar dois conteúdos diferentes que produzem o mesmo hash, permitindo, por exemplo, substituir um documento legítimo por um malicioso sem que a verificação acuse a alteração.
- **Falsificação de assinaturas digitais:** quando o hash é utilizado em conjunto com assinaturas, o atacante pode produzir uma assinatura válida para um conteúdo arbitrário.
- **Comprometimento de cadeias de certificação:** historicamente, certificados X.509 assinados com SHA-1 puderam ser falsificados, levando à sua deprecação pelos navegadores a partir de 2017.

#### Como corrigir

- Substituir o uso de SHA-1 por funções da família **SHA-2** (`sha256`, `sha384`, `sha512`) ou **SHA-3** quando o contexto envolver segurança.
- Quando o hash for utilizado para fins **não-criptográficos** (por exemplo, *fingerprint* de cache ou identificação de blob), explicitar essa intenção via parâmetro `usedforsecurity=False` (disponível a partir do Python 3.9), sinalizando à ferramenta de análise que o uso é seguro:

```python
# Uso seguro (não-criptográfico) — FIPS-compliant em Python 3.9+
digest = hashlib.sha1(data, usedforsecurity=False).digest()

# Uso criptográfico recomendado
digest = hashlib.sha256(data).digest()
```

> 💡 No caso específico apontado, o achado está dentro da biblioteca `cryptography` — uma dependência de terceiros amplamente auditada. A correção, portanto, depende do mantenedor da biblioteca. Cabe ao desenvolvedor manter a dependência atualizada e acompanhar avisos de segurança publicados pelo projeto.

---

### 🟡 Vulnerabilidade 2 — Senha em Texto Claro no Código-Fonte

| Campo | Valor |
|---|---|
| **Test ID** | B105 (`hardcoded_password_string`) |
| **CWE** | [CWE-259](https://cwe.mitre.org/data/definitions/259.html) — *Use of Hard-coded Password* |
| **Severidade** | 🟢 BAIXA (no contexto de testes) |
| **Confiança** | MÉDIA |
| **Local** | `tests/conftest.py:45-46` e `tests/integration/test_auth.py:7,11` |
| **Trecho** | `await c.post("/auth/login", data={"username": "admin", "password": "secret"})` |

#### O que é

A regra **B105** identifica strings que aparentam ser senhas declaradas diretamente no código-fonte (*hardcoded credentials*). No projeto, foram detectadas múltiplas ocorrências em arquivos de teste, com valores como `"secret"` e `"pass"` utilizados nas chamadas aos endpoints `/auth/register` e `/auth/login`.

Embora o Bandit classifique a severidade como baixa, o padrão é considerado relevante porque, em projetos reais, é comum que credenciais inicialmente colocadas em testes acabem migrando para arquivos de configuração, *fixtures* compartilhadas ou pipelines de CI/CD — onde sua exposição passa a representar risco real.

#### Risco

- **Vazamento de credenciais em repositórios públicos:** caso uma credencial real (não fictícia) seja inserida no código e o repositório seja exposto, o atacante obtém acesso direto ao recurso protegido. O incidente conhecido como *"GitHub credential leak"* afeta milhares de repositórios todos os anos.
- **Reutilização indevida em ambientes:** uma senha definida como `"dev-secret-key"` para desenvolvimento pode acidentalmente ser promovida para produção (situação observada no próprio projeto, em [`app/core/config.py:6`](../app/core/config.py#L6), onde `SECRET_KEY` possui um valor padrão hardcoded).
- **Dificuldade de rotação:** senhas embutidas exigem alteração de código e novo *deploy* para serem rotacionadas, prática contrária às recomendações da OWASP A07:2021 (*Identification and Authentication Failures*).

#### Como corrigir

- **Para arquivos de teste:** centralizar credenciais em *fixtures* nomeadas e tratá-las como dados de teste explícitos. Adicionar o comentário `# nosec B105` na linha sinaliza ao Bandit que o valor é proposital e seguro:

```python
TEST_PASSWORD = "secret"  # nosec B105 — credencial fictícia de teste
```

- **Para código de produção:** carregar segredos exclusivamente de variáveis de ambiente, *secret managers* (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault) ou arquivos `.env` excluídos do versionamento. No projeto, o [`Settings`](../app/core/config.py) já utiliza `pydantic-settings` com leitura de `.env`, porém o valor padrão `"dev-secret-key"` deveria ser removido e a aplicação deveria **falhar explicitamente** caso a variável não esteja definida em produção:

```python
class Settings(BaseSettings):
    SECRET_KEY: str  # sem valor padrão — obrigatório no .env
    model_config = SettingsConfigDict(env_file=".env")
```

- Garantir que o arquivo `.env` esteja listado no `.gitignore` (já configurado no projeto).

---

### 🟢 Vulnerabilidade 3 — Uso de `assert` em Código de Aplicação

| Campo | Valor |
|---|---|
| **Test ID** | B101 (`assert_used`) |
| **CWE** | [CWE-703](https://cwe.mitre.org/data/definitions/703.html) — *Improper Check or Handling of Exceptional Conditions* |
| **Severidade** | 🟢 BAIXA |
| **Confiança** | ALTA |
| **Local** | `tests/integration/test_auth.py:8,9,12,13,...` (e demais arquivos de teste) |
| **Trecho** | `assert r.status_code == 201` |

#### O que é

A regra **B101** identifica o uso da instrução `assert` no código Python. O ponto crítico apontado pelo Bandit é que o interpretador Python **remove todas as instruções `assert` quando executado em modo otimizado** (`python -O` ou `python -OO`). Nesse modo, a expressão associada ao `assert` simplesmente não é avaliada, o que pode invalidar verificações de segurança que dependam dela.

No contexto do projeto, todos os achados de B101 estão localizados em **arquivos de teste**, onde o uso de `assert` é o padrão idiomático esperado pelo *framework* `pytest`. Portanto, a vulnerabilidade não se materializa neste caso específico — mas é importante compreendê-la para evitar que o padrão se propague para o código de produção.

#### Risco

Quando `assert` é utilizado em **código de produção** para validar condições de segurança, o risco é direto:

- **Bypass de validações em produção:** se a aplicação for executada com `python -O`, validações como `assert user.is_authenticated` são silenciosamente removidas, permitindo que código posterior seja executado sem a checagem prevista.
- **Falsa sensação de segurança:** o desenvolvedor presume que a verificação está protegendo o fluxo, mas em ambiente otimizado a barreira não existe.
- **Comportamento divergente entre ambientes:** o sistema funciona em desenvolvimento (modo *debug*) e falha em produção (modo otimizado), tornando a vulnerabilidade difícil de reproduzir e diagnosticar.

#### Como corrigir

- **Em código de aplicação:** substituir `assert` por verificações explícitas que levantem exceções controladas:

```python
# ❌ Inseguro — removido em modo otimizado
assert user.is_admin, "Usuário não é administrador"

# ✅ Seguro — sempre executado
if not user.is_admin:
    raise PermissionError("Usuário não é administrador")
```

- **Em código de teste:** o uso de `assert` é correto e esperado pelo `pytest`. Para suprimir os falsos positivos do Bandit, recomenda-se configurar a ferramenta para ignorar a regra B101 dentro do diretório de testes, criando um arquivo `.bandit` ou `pyproject.toml` na raiz do projeto:

```toml
# pyproject.toml
[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]  # apenas se desejar ignorar globalmente
```

Ou, executando o scan com a flag adequada:

```bash
bandit -r app/ -x ./tests,./venv
```

---

## 3. Síntese e Recomendações

A análise estática do código com Bandit revelou um conjunto de achados que pode ser agrupado em três naturezas distintas:

| Natureza | Exemplo | Tratamento Recomendado |
|---|---|---|
| **Risco real em produção** | SHA-1 (B324) em dependências | Manter dependências atualizadas e auditadas |
| **Padrão inseguro replicável** | Senhas hardcoded (B105) | Migrar segredos para variáveis de ambiente; remover defaults inseguros |
| **Falso positivo contextual** | `assert` em testes (B101) | Configurar exclusões na ferramenta para reduzir ruído |

### Recomendações Gerais

1. **Excluir o diretório `venv/` do escopo do scan** — concentra a análise no código de fato sob responsabilidade do time, eliminando centenas de achados de bibliotecas de terceiros que confundem a leitura do relatório.
2. **Remover o valor padrão de `SECRET_KEY`** em [`app/core/config.py`](../app/core/config.py) e tornar a variável obrigatória, prevenindo que ambientes de produção sejam inadvertidamente inicializados com a chave de desenvolvimento.
3. **Integrar o Bandit ao pipeline de CI/CD**, falhando o *build* em caso de achados de severidade alta e média, de forma a garantir que novas vulnerabilidades sejam detectadas antes da fusão na branch principal.
4. **Adotar uma política de revisão periódica de dependências** com ferramentas complementares como `pip-audit` ou `safety`, que verificam CVEs publicados contra as versões em uso.

A combinação dessas práticas eleva o projeto de uma postura **reativa** (corrigir após ser apontado) para uma postura **preventiva** (impedir a entrada de vulnerabilidades), alinhando-se ao princípio de *Shift-Left Security* defendido por frameworks como OWASP SAMM e NIST SSDF.
