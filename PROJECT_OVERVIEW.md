# Registro de Produtividade V2 — Visão Geral

## 1. Identidade

**Projeto:** Registro de Produtividade V2

Aplicação web para registrar sessões de produtividade, controlar tempo,
armazenar histórico e futuramente oferecer consultas e relatórios.

A V2 é a evolução profissional do projeto simplificado original, com
finalidade de portfólio e potencial de comercialização.


## 2. Objetivo

Construir primeiro um backend profissional, consistente, testado e seguro.
O backend é a fonte da verdade para o frontend posterior.

Fluxo:

1. consolidar o domínio;
2. garantir integridade e segurança;
3. testar;
4. congelar o MVP do backend;
5. somente então construir/refinar o frontend.

Não criar uma V3 para problemas pertencentes à V2.


## 3. Stack

### Backend

- Python 3.12
- Flask
- SQLAlchemy ORM
- Alembic
- PostgreSQL em produção
- SQLite para testes
- pytest
- Flask-JWT-Extended

### Frontend planejado

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui


## 4. Estado atual

### Concluído

- gerenciamento explícito de sessões SQLAlchemy;
- separação dos testes de API de sessões por endpoint;
- hardening da API de sessões com JWT e ownership;
- identidade derivada exclusivamente do JWT;
- operações de sessão concentradas em `session_service.py`;
- service independente de Flask;
- serialização mantida na camada de API;
- constraints de integridade do domínio de sessão no banco;
- garantia de uma única sessão ativa por usuário no banco;
- modelo temporal normalizado em UTC;
- cálculo determinístico da duração líquida;
- tratamento consistente de pausas acumuladas;
- testes temporais determinísticos.

### Último checkpoint conhecido

Os BLOCOs 1, 2, 3 e 4 do hardening do backend estão concluídos.

O BLOCO 3 adicionou garantias de integridade ao banco:

- `status` restrito a `running`, `paused` e `finished`;
- `session_type` restrito aos tipos válidos do domínio;
- coerência entre status, `paused_at` e `finished_at`;
- `started_at` obrigatório;
- valores temporais e quantitativos não negativos;
- índice único parcial `uq_session_active_per_user`, garantindo uma única
  sessão `running` ou `paused` por usuário.

A migration
`f8de7633e97d_add_session_integrity_constraints.py` foi validada no
PostgreSQL com upgrade, downgrade e novo upgrade.

Os testes são explicitamente isolados em SQLite em memória.

O BLOCO 4 consolidou o modelo temporal:

- UTC é o padrão temporal do domínio;
- `ensure_utc()` normaliza datetimes e trata valores naive retornados pelo
  SQLite como UTC;
- `utc_now()` centraliza a obtenção do horário atual e permite testes
  determinísticos;
- `duration_hours` permanece como representação persistida da duração
  líquida ativa;
- `paused_seconds` acumula o tempo total pausado;
- o cálculo da duração desconta integralmente as pausas;
- cálculos com `Decimal` evitam introduzir imprecisão pela conversão direta
  de `float`;
- duração líquida nunca é persistida como valor negativo;
- múltiplas pausas foram validadas deterministicamente;
- finalização durante uma pausa contabiliza corretamente a pausa ainda
  aberta.

Estado validado:

- 12 testes específicos do modelo temporal aprovados;
- 90 testes aprovados na suíte completa;
- nenhuma regressão identificada.

Próximo passo: **BLOCO 5 — Contrato final da API**.

O frontend permanece posterior ao congelamento do MVP do backend.

> ⚠️ **COMMIT:** após concluir e testar um processo, revisar
> `git diff`/`git status` e fazer commit com mensagem clara.


## 5. Roadmap

### BLOCO 1 — Segurança da API

**CONCLUÍDO**

JWT, ownership, identidade exclusivamente pelo JWT e testes de segurança.

### BLOCO 2 — Domínio / Service Layer

**CONCLUÍDO**

Operações de sessão concentradas no service, independente de Flask.

Commit: `b5743cd`

### BLOCO 3 — Integridade do banco

**CONCLUÍDO**

Constraints, invariantes temporais, índice único parcial, Alembic e testes.

Commit: `5560ce1`

### BLOCO 4 — Tempo

**CONCLUÍDO**

UTC, normalização de datetimes, precisão de duração, duração líquida,
pausas acumuladas e testes temporais determinísticos.

Validação:

- `tests/test_session_time.py`: 12 testes aprovados;
- suíte completa: 90 testes aprovados.

**Commit: PENDENTE — alterações concluídas e testadas.**

### BLOCO 5 — Contrato final da API

**PLANEJADO**

Revisar e congelar o contrato final do MVP, incluindo:

- resíduos de integração entre Session e Goal;
- comportamento de `questions` e `mock_exam`;
- serialização;
- listagem;
- filtros e ordenação;
- paginação, se necessária;
- erros e mensagens;
- documentação final da API;
- revisão final de segurança;
- congelamento do backend MVP.


## 6. Pendências / A DEFINIR

- tratamento definitivo de `goal_id` legado;
- regras finais de `questions`/`mock_exam`;
- listagem, filtros, ordenação e paginação;
- catálogo definitivo de erros/mensagens;
- revisão final de JWT/cookies/CSRF;
- contrato final da API antes do frontend.

A política temporal que anteriormente estava pendente foi definida no
BLOCO 4:

- UTC como padrão;
- `duration_hours` como duração líquida persistida;
- `paused_seconds` como acumulador das pausas;
- cálculo temporal determinístico e normalizado.


## 7. Fonte de verdade e continuidade

Git é a fonte de verdade do código.

A documentação persistente registra decisões, arquitetura e estado do
projeto.

`PROJECT_OVERVIEW.md` é o retrato resumido e evolutivo do estado do projeto
e deve permanecer versionado no repositório.

A cópia disponibilizada nas fontes do Projeto no ChatGPT deve ser
atualizada nos checkpoints relevantes para facilitar a continuidade entre
conversas.

Quando houver divergência entre memória de conversa e código real,
verificar o estado do Git antes de concluir.


## 8. Atualização obrigatória

> ⚠️ **ATUALIZAR `PROJECT_OVERVIEW.md` APÓS ETAPAS IMPORTANTES:** revisar
> este documento quando um bloco for concluído, uma decisão importante for
> fechada, houver mudança arquitetural relevante ou outro checkpoint
> significativo.

Não atualizar a cada pequena alteração. O objetivo é manter um estado atual
confiável.

Processo padrão:

**entender → alterar → testar especificamente → suíte completa → revisar
Git → commit → atualizar Overview no checkpoint.**
