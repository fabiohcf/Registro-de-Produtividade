# Registro de Produtividade V2 — Visão Geral

## 1. Identidade

**Projeto:** Registro de Produtividade V2.

Aplicação web para registrar sessões de produtividade, controlar o tempo líquido de atividade, armazenar histórico e, futuramente, oferecer consultas e relatórios.

A V2 é a evolução profissional do projeto simplificado original, com finalidade de portfólio e potencial de comercialização. Não criar uma V3 para resolver problemas pertencentes à V2.

## 2. Objetivo e estratégia

Construir um backend profissional, seguro, consistente e testado antes de desenvolver ou integrar definitivamente o frontend.

Sequência de trabalho:

1. Consolidar o domínio de sessões.
2. Garantir segurança e integridade dos dados.
3. Validar o comportamento por testes automatizados.
4. Consolidar e congelar o contrato do MVP do backend.
5. Desenvolver ou refinar o frontend com base no contrato validado.

O backend é a fonte de verdade para o frontend.

## 3. Stack e arquitetura

### Backend

- Python 3.12;
- Flask;
- SQLAlchemy ORM com gerenciamento explícito de sessões, sem Flask-SQLAlchemy como camada de persistência;
- Alembic para migrations;
- PostgreSQL em produção;
- SQLite em memória nos testes;
- pytest;
- Flask-JWT-Extended, com JWT em cookies.

### Frontend planejado

- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- shadcn/ui.

### Responsabilidades das camadas

- **Routes/API:** requisições e respostas HTTP, autenticação, identidade do JWT, validação de formato do payload, status HTTP, serialização e logging aplicável.
- **Services:** regras de negócio, transições de estado, ownership e persistência; independentes de Flask.
- **Models:** entidades SQLAlchemy e restrições estruturais.
- **Database:** engine, `Base` e `SessionLocal`.
- **Tests:** regras de domínio, comportamento da API, segurança e regressões.

Operações de sessão: `app/routes/session_service.py`.

Rotas e serialização de sessões: `app/routes/api_sessions.py`, incluindo `_serialize_session()`.

Os testes de API de sessões são separados por endpoint. Os fixtures de testes isolam os dados com criação e remoção do esquema em SQLite.

## 4. Estado atual

**Estado do backend:** Blocos 1, 2, 3 e 4 concluídos. Bloco 5 em andamento.

**Último checkpoint confirmado:** implementação, testes, documentação e commit do endpoint `PATCH /api/sessions/<session_id>`.

**Última suíte completa executada:** **152 testes aprovados** em 26,03 segundos, sem falhas.

**Git:** commit `7aacb34` confirmado; branch `main` sincronizada com `origin/main`; diretório de trabalho limpo no último `git status` informado.

### Funcionalidades e garantias concluídas

- Gerenciamento explícito de sessões SQLAlchemy.
- Autenticação JWT nas operações de sessão.
- Identidade obtida exclusivamente do JWT, sem confiar em `user_id` do cliente.
- Ownership para operações por `session_id`, com HTTP 404 para sessão inexistente ou pertencente a outro usuário.
- Regras de domínio e persistência concentradas no service.
- Serialização JSON mantida na camada de API.
- Máquina de estados de sessões validada.
- Exclusividade de uma sessão ativa por usuário garantida também no banco.
- Constraints de integridade de status, tipo, timestamps e valores não negativos.
- Tempo padronizado em UTC, com normalização de datetimes.
- Cálculo determinístico de duração líquida e de pausas acumuladas.
- Validação QT/QC na finalização de sessões de questões e simulados.
- Edição segura e parcial de QT/QC por PATCH em sessões finalizadas.
- Testes específicos e suíte completa aprovados.

### Domínio consolidado

**Estados:** `running`, `paused`, `finished` e `cancelled` (conceitual; cancelamento remove fisicamente a sessão).

**Transições permitidas:**

- `running` → `paused`, `finished` ou `cancelled`;
- `paused` → `running`, `finished` ou `cancelled`.

Sessões `finished` não voltam a estados ativos e não podem ser canceladas pelas operações de sessão existentes. A edição de QT/QC de uma sessão finalizada não modifica seu estado.

**Tipos:** `study`, `revision`, `questions`, `essay` e `mock_exam`.

**Sessão ativa:** apenas `running` ou `paused`; no máximo uma por usuário.

**Tempo:** `duration_hours` armazena a duração líquida ativa, excluindo pausas; `paused_seconds` acumula os segundos pausados.

**Goal:** Session V2 não possui relacionamento com Goal e não usa `goal_id` para controlar sessões. A revisão dos resíduos legados permanece pendente.

## 5. Roadmap e checkpoints

### BLOCO 1 — Segurança da API

**CONCLUÍDO**

- JWT obrigatório nas operações de sessão.
- Identidade exclusivamente pelo JWT.
- Verificação de ownership.
- HTTP 404 para recurso inexistente ou pertencente a outro usuário.
- Testes de autenticação e isolamento entre usuários.

A revisão final de JWT/cookies/CSRF e da segurança de Goal permanece pendente antes do congelamento do MVP; isso não reabre a implementação já concluída das proteções de sessão.

### BLOCO 2 — Domínio e Service Layer

**CONCLUÍDO**

- Operações `start`, `pause`, `resume`, `finish` e `cancel` centralizadas no service.
- Transições de estado explícitas.
- Separação entre regras de negócio e tratamento HTTP.
- Services independentes de `request` e `jsonify`.

**Commit:** `b5743cd` — `refactor: move session operations to service layer`.

### BLOCO 3 — Integridade do banco

**CONCLUÍDO**

Garantias implementadas:

- `status` restrito a `running`, `paused` e `finished` no banco;
- `session_type` restrito aos cinco tipos válidos;
- coerência entre `status`, `paused_at` e `finished_at`;
- `started_at` obrigatório;
- `paused_seconds`, `duration_hours`, `questions_total` e `questions_correct` não negativos quando aplicáveis;
- índice único parcial `uq_session_active_per_user` para impedir duas sessões ativas por usuário.

A migration `f8de7633e97d_add_session_integrity_constraints.py` foi validada em PostgreSQL com upgrade, downgrade e novo upgrade.

**Commit:** `5560ce1` — `feat: enforce session database integrity`.

**Limite conhecido:** as constraints existentes ainda não expressam integralmente a relação entre QT, QC, tipo e status. Esse complemento é uma etapa pendente do Bloco 5.

### BLOCO 4 — Tempo

**CONCLUÍDO**

- UTC como padrão temporal do domínio.
- `ensure_utc()` para normalizar datetimes, tratando como UTC valores naive retornados pelo SQLite.
- `utc_now()` para centralizar o horário atual e permitir testes determinísticos.
- Persistência de duração líquida em `duration_hours`.
- Acúmulo de pausas em `paused_seconds`.
- Cálculo de duração descontando todas as pausas, inclusive a pausa aberta no momento da finalização.
- Uso de `Decimal` para evitar imprecisões decorrentes de conversões diretas de `float`.
- Duração líquida nunca negativa.
- Testes determinísticos de múltiplas pausas e finalização durante pausa.

**Checkpoint histórico:** 12 testes temporais específicos e 90 testes na suíte completa aprovados.

**Commit:** `1e7a52d` — `refactor: harden session time handling`.

### BLOCO 5 — Contrato final da API

**EM ANDAMENTO**

#### Etapa concluída — `POST /api/sessions/finish`

- `questions` e `mock_exam` exigem `questions_total` inteiro positivo.
- `questions_correct` aceita `null` (correção pendente) ou inteiro de 0 até QT.
- Booleanos, frações, números negativos e strings são rejeitados nos campos numéricos.
- `study`, `revision` e `essay` rejeitam QT/QC no payload, inclusive quando explicitamente enviados como `null`.
- Validações ocorrem antes da finalização e persistência.
- Permanecem as verificações de JWT, ownership e estado da sessão.

**Validação:** 28 testes específicos de `/finish` aprovados; checkpoint histórico de 112 testes na suíte completa.

**Commit:** `1d40491` — `feat: validate question results on session finish`.

**Commit documental relacionado:** `b41a7c4` — `docs: update project overview with block 5 progress`.

#### Etapa concluída — `PATCH /api/sessions/<session_id>`

- Atualiza exclusivamente `questions_total` e `questions_correct`.
- Permite edição apenas em sessões `finished` dos tipos `questions` e `mock_exam`.
- Exige JWT e obtém a identidade exclusivamente do token.
- Verifica ownership; sessão inexistente ou alheia retorna HTTP 404.
- Rejeita campos desconhecidos, mesmo combinados com campos válidos.
- Rejeita payload vazio ou que não seja objeto JSON.
- Preserva campos omitidos.
- Exige QT inteiro positivo; não aceita QT `null`.
- Permite QC `null` (correção pendente) ou inteiro de zero até QT.
- Rejeita valores booleanos, fracionários, negativos e strings.
- Valida QT e QC resultantes em conjunto, inclusive ao reduzir QT quando QC já está armazenado.
- Preserva `status`, `session_type`, `started_at`, `finished_at`, `duration_hours` e `paused_seconds`.
- Mantém validação de domínio no service e resposta HTTP na rota.

**Validação:** 40 testes específicos do PATCH aprovados; **152 testes na suíte completa** aprovados, sem regressões identificadas; `git diff --check` sem problemas.

**Commit:** `7aacb34` — `feat: add secure patch endpoint for session results`.

**Situação do Git após o checkpoint:** `main` atualizada com `origin/main`; working tree clean.

#### Etapas restantes do Bloco 5

- **PENDENTE:** definir as invariantes definitivas QT/QC no banco, criar constraints e migration Alembic e testar no PostgreSQL e SQLite.
- **PENDENTE:** revisar resíduos legados de integração entre Session e Goal, sem reintroduzir `goal_id` no domínio de sessões.
- **PENDENTE / A DEFINIR:** consolidar comportamento e contrato de listagem, filtros e ordenação com base no código real.
- **PENDENTE / A DEFINIR:** decidir se paginação é necessária ao MVP.
- **PENDENTE:** revisar serialização, erros e mensagens da API; consolidar o contrato final.
- **PENDENTE:** revisão final de segurança, incluindo Goal, JWT, cookies e CSRF.
- **PENDENTE:** atualizar documentação final e congelar o backend MVP.

## 6. Contrato conhecido da API de sessões

Endpoints implementados e conhecidos:

- `POST /api/sessions/start` — inicia sessão; sucesso HTTP 201.
- `POST /api/sessions/pause` — pausa sessão `running`; sucesso HTTP 200.
- `POST /api/sessions/resume` — retoma sessão `paused`; sucesso HTTP 200.
- `POST /api/sessions/finish` — finaliza sessão ativa, validando QT/QC conforme o tipo; sucesso HTTP 200.
- `POST /api/sessions/cancel` — remove fisicamente sessão ativa; sucesso HTTP 200.
- `GET /api/sessions/list` — lista sessões do usuário autenticado; contrato definitivo de filtros e ordenação ainda sujeito a revisão.
- `PATCH /api/sessions/<session_id>` — edita parcialmente QT/QC de sessão finalizada de questões ou simulado; sucesso HTTP 200.

Todos os endpoints de sessão exigem JWT. Para operações sobre sessões existentes, o service verifica ownership.

Serialização conhecida de sessões: `id`, `user_id`, `status`, `session_type`, `description`, `started_at`, `finished_at`, `duration_hours`, `paused_seconds`, `questions_total` e `questions_correct`.

Datas são serializadas com `isoformat()`; a resposta atual converte `duration_hours` para `float`.

O padrão conhecido de erro é JSON com campo `error`. O catálogo definitivo de mensagens e códigos permanece sujeito à revisão do Bloco 5.

**Nota de consistência documental:** as fontes `API_CONTRACT.md`, `DOMAIN_RULES.md`, `ARCHITECTURE.md` e `SECURITY.md` contêm alguns checkpoints e trechos prospectivos anteriores à conclusão dos Blocos 3, 4 e das etapas QT/QC do Bloco 5. Atualizá-las em checkpoint próprio, preservando decisões já fechadas. Em caso de divergência, conferir o Git e o código real.

## 7. Pendências e decisões fechadas

### Pendências prioritárias

1. **Integridade QT/QC no banco:** analisar invariantes, migration e testes, sem misturar com outras mudanças.
2. **Resíduos de Goal:** examinar o código real antes de decidir alterações.
3. **Listagem e contrato da API:** revisar comportamento existente, filtros, ordenação, paginação e erros.
4. **Segurança pré-MVP:** revisar JWT/cookies/CSRF e endpoints de Goal.
5. **Congelamento do MVP:** atualizar documentação final e validar a suíte completa antes de iniciar o frontend.

### Decisões já fechadas

- Continuar na V2, sem criar V3.
- Backend como fonte de verdade do frontend.
- SQLAlchemy ORM com sessões explícitas; services sem dependência de Flask.
- Identidade exclusivamente pelo JWT; ownership obrigatório.
- Sessão inexistente ou alheia retorna 404.
- Uma única sessão ativa por usuário, com garantia no banco.
- UTC como padrão temporal.
- `duration_hours` como duração líquida persistida; `paused_seconds` como acumulador de pausas.
- Sessões canceladas são excluídas fisicamente.
- Session V2 não possui relacionamento com Goal.
- Regras QT/QC de `/finish` e PATCH conforme documentadas no Bloco 5.
- Frontend somente após estabilização e congelamento do backend MVP.

Não inventar requisitos, filtros, mensagens ou regras não decididos. Registrar o que não estiver fechado como **PENDENTE / A DEFINIR**.

## 8. Fonte de verdade e continuidade

- **Git:** fonte de verdade do código.
- **Documentação persistente do Projeto:** fonte de verdade das decisões, arquitetura e estado registrado.
- **Backend:** fonte de verdade para o frontend.

Em caso de divergência entre memória de conversa, documentação e código, verificar o repositório Git antes de concluir.

O `PROJECT_OVERVIEW.md` é o registro resumido e evolutivo do projeto. Deve ser versionado no repositório e atualizado nas fontes do Projeto no ChatGPT após checkpoints relevantes.

### Processo padrão de desenvolvimento

1. Entender o estado real e identificar os arquivos afetados.
2. Definir uma alteração pequena e verificável.
3. Implementar.
4. Executar os testes específicos.
5. Executar a suíte completa ao integrar o bloco.
6. Revisar `git diff`, `git diff --check` e `git status`.
7. Realizar commit com mensagem clara.
8. Atualizar a documentação no checkpoint e sincronizar o remoto quando apropriado.

> **LEMBRETE — COMMIT:** após concluir e testar um processo, revisar o Git e registrar um commit claro.

> **LEMBRETE — DOCUMENTAÇÃO:** atualizar `PROJECT_OVERVIEW.md` após blocos concluídos, decisões relevantes e checkpoints importantes. Não é necessário reescrevê-lo a cada pequena alteração.

### Próxima ação de desenvolvimento

Iniciar a análise da integridade QT/QC no banco, verificando o estado real das migrations Alembic e das constraints existentes antes de modificar código.
