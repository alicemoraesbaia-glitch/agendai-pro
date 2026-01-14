Agendai Pro (Smart Agenda)
Projeto de Estágio Supervisionado – Engenharia de Software (UNINTER) Sistema de agendamento inteligente e gestão clínica de alta performance, projetado com foco em escalabilidade e segurança.

O Agendai Pro é uma solução modular que orquestra fluxos entre pacientes, especialistas e administradores. O projeto destaca-se pela transição de um ambiente de desenvolvimento local (SQLite) para uma infraestrutura de produção escalável em nuvem utilizando PostgreSQL e Render PaaS.

Funcionalidades Principais
Administração e Business Intelligence (BI)
Dashboard de Métricas: Visualização de faturamento e volume de demanda em tempo real através de consultas agregadas.

Gestão de Usuários: Controle total de perfis com suporte a Soft Delete (Exclusão Lógica) para preservação de histórico.

Auditoria de Sistema: Registro imutável de ações críticas (Logs de Auditoria) para rastreabilidade administrativa total.

Operacional e Fluxo de Atendimento
Orquestração de Fluxo (Painel TV): Interface dedicada para salas de espera que gerencia dinamicamente a fila de chamadas com feedback visual.

Gestão de Conflitos Inteligente: Algoritmos que impedem a sobreposição de horários para o mesmo recurso, especialista ou paciente.

👤 Área do Cliente (Paciente)
Agendamento Autônomo: Cadastro, login e seleção de serviços/horários com validação de disponibilidade.

Gestão de Agendamentos: Consulta de histórico e possibilidade de cancelamento diretamente via interface do usuário.

Segurança e Arquitetura
RBAC (Role-Based Access Control): Controle de acesso baseado em papéis (Admin, Staff, Paciente).

Política de Lockout: Bloqueio automático de conta após falhas consecutivas de login para proteção contra força bruta.

Proteção de Dados: Autenticação via Flask-Login, proteção contra CSRF e Reset de Senha seguro via Token.

Design Pattern: Implementação de Clean Architecture utilizando Blueprints e Application Factory.

Stack Tecnológica
Backend: Python 3.13, Flask (App Factory), SQLAlchemy (ORM).

Frontend: HTML5, TailwindCSS (Responsivo), Alpine.js e Jinja2.

Banco de Dados: PostgreSQL (Produção no Render) e SQLite (Desenvolvimento/Testes).

DevOps: Migrações via Alembic (Flask-Migrate) e Integração Contínua (CI/CD) via GitHub.
Configuração e Execução Local

1. Instalação do Ambiente
   Bash

# Clone o repositório oficial

git clone https://github.com/alicemoraesbaia-glitch/agendai-pro.git
cd agendai-pro

# Configurar ambiente virtual

python -m venv venv

# Ativação (Windows): venv\Scripts\activate | (Linux/Mac): source venv/bin/activate

# Instalar dependências

pip install -r requirements.txt 2. Inicialização da Base de Dados
Bash

# Executar as migrações para criar as tabelas

flask db upgrade

# Popular o banco com o catálogo de serviços inicial (Seeding)

python seed_db.py 3. Execução
Bash

flask run
Links Oficiais
Repositório GitHub: https://github.com/alicemoraesbaia-glitch/agendai-pro

Aplicação em Produção: https://agendai-pro.onrender.com
