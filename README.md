# IBARECISA

Sistema de gestão eclesiástica da [IBARECISA](https://ibarecisa.org.br/).

## Apps

| App | Descrição |
|---|---|
| `secretarial` | Atas, projetos de ata, pautas e registros de membros |
| `treasury` | Tesouraria, transações, relatórios e períodos contábeis |
| `users` | Usuários, perfis, permissões e grupos |
| `events` | Gestão de eventos |
| `worship` | Catálogo de cultos e louvores |
| `blog` | Blog/publicações |
| `core` | Modelos base e utilitários compartilhados |

## Stack

- Python 3 + Django 5.2
- Django REST Framework
- WeasyPrint / xhtml2pdf (geração de PDFs)
- CKEditor (editor de texto rico)
- SQLite (dev) / armazenamento S3 (prod)
- Tailwind CSS

## Setup

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations users
python manage.py migrate
python manage.py createsuperuser
python manage.py init_groups
```

## Rodar

```bash
python manage.py runserver
```

## Deploy

```bash
git stash && git pull && git stash pop
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```

## SSL

Criar certificado:
```bash
sudo certbot certonly --standalone -d app.ibarecisa.org.br -d diacono.ibarecisa.org.br
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```

Renovar (válidos por 90 dias):
```bash
sudo certbot renew
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```
