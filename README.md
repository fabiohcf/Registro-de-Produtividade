Registro de Produtividade (Versão Expandida)

Uma aplicação web para registro de horas de estudo e trabalho, com gestão de usuários, metas e sessões. Evolução da versão resumida disponível aqui
 e hospedada neste link.

Funcionalidades

Gestão de usuários: cadastro e listagem.
Gestão de metas: criar metas vinculadas a usuários, com descrição, tipo e horas alvo.
Registro de sessões: iniciar, pausar e finalizar sessões, calculando duração automaticamente.
Autenticação: login e logout de usuários.
Relatórios: visualização das metas e sessões registradas.
Interface web responsiva: baseada em Flask, HTML, CSS e JS.

Tecnologias

Back-end: Python 3.12, Flask, SQLAlchemy
Banco de dados: PostgreSQL (produção) / SQLite (teste)
Testes: Pytest
Hospedagem: Render
Controle de versão: Git / GitHub

Estrutura do Projeto
´´´
Registro-de-Produtividade/
├── app/
│   ├── models/
│   ├── routes/
│   ├── templates/
│   ├── static/
│   ├── utils/
│   ├── __init__.py
│   └── database.py
├── config/
│   └── database.py
├── tests/
│   └── ...
├── .env
├── .gitignore
├── requirements-dev.txt
└── run.py
´´´
Instalação

Clone o repositório:
git clone https://github.com/fabiohcf/Registro-de-Produtividade.git
cd Registro-de-Produtividade


Crie e ative o ambiente virtual:
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows


Instale as dependências:
pip install -r requirements-dev.txt


Configure as variáveis de ambiente no .env:
DATABASE_URL=postgresql://usuario:senha@endereco:porta/nome_db
SECRET_KEY=sua_chave_secreta

Execução
python run.py


Acesse a aplicação em: http://127.0.0.1:5000

Endpoints Principais

Usuários
GET /api/usuarios – Lista todos os usuários
POST /api/usuarios – Cria um novo usuário

Metas
GET /api/metas – Lista todas as metas
POST /api/metas – Cria uma nova meta

Autenticação
POST /auth/login – Login de usuário
POST /auth/logout – Logout do usuário

Sessões
POST /api/sessoes – Cria nova sessão (com start/end)
GET /api/sessoes – Lista sessões do usuário

Testes
Para rodar todos os testes com Pytest:
pytest -v

Todos os testes da versão expandida foram ajustados e estão passando.

Licença
MIT License – veja o arquivo LICENSE.
