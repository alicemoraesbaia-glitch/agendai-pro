# 📅 Smart Agenda

Sistema de Agendamento Inteligente desenvolvido com **Flask (App Factory)**, **SQLAlchemy**, **TailwindCSS** e **PostgreSQL**.

## 🚀 Funcionalidades

- **Clientes:** Cadastro, Login, Agendamento de serviços, Cancelamento e Histórico.
- **Admin:** Dashboard de métricas, Gestão de Usuários (Soft Delete), Gestão de Serviços e Auditoria.
- **Segurança:** Autenticação via Flask-Login, CSRF Protection, Reset de Senha via Token.
- **Arquitetura:** Clean Architecture com Blueprints e Logs de Auditoria.

## 🛠️ Tecnologias

- **Backend:** Python 3.13, Flask, SQLAlchemy, Alembic.
- **Frontend:** HTML5, TailwindCSS, Alpine.js.
- **Banco:** PostgreSQL (Produção) / SQLite (Dev).

## 🔧 Configuração Local

### 1. Clonar e Instalar

```bash
# Clone o repositório
git clone [https://github.com/seu-usuario/smart-agenda.git](https://github.com/seu-usuario/smart-agenda.git)
cd smart-agenda

# Crie e ative o ambiente virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```
