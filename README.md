# Getting Started: IBARECISA

## About

[IBARECISA](https://ibarecisa.org.br/)

## Technologies and versions

  Tools               |  Version
----------------------| --------
Python                | 3
Django                | 4.2
Venv                  | 3
Pip                   | 24

## Prepare environment

```bash
cp .env.example .env
python3 -m venv venv
source venv/bin/activate
python -m pip install pip --upgrade
pip install -r requirements.txt
```

## Setup

I would recommend deleting the migrations files and doing this:

#### Run migrations

1. `python manage.py makemigrations users`
2. `python manage.py migrate`
3. Create a superuser (necessary, because it  will be the default user, look at the code)
4. `python manage.py init_groups`
5. `python manage.py makemigrations`
6. Change the migrations file of the treasury app to: **upload_to=treasury.utils.custom_upload_to**, Somehow django generates **upload_to=treasury.utils.custom_upload_to.custom_upload_to**, what throws and error
7. `python manage.py migrate`

The second step will create permissions groups and set the permissions
You can change the standard permissions in run time or in the users app **/management/init_groups.py**

## Run server

```bash
python manage.py runserver
```

## Versioning

When a new task is created, it is customary to follow the workflow of the [Git flow](https://www.atlassian.com/br/git/tutorials/comparing-workflows/gitflow-workflow) for developing new features and/or resolving bugs.

## Deploy
```bash
git stash 
git pull
git stash pop
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```

## SSL certificate
create
```bash
sudo certbot certonly --standalone -d app.ibarecisa.org.br -d diacono.ibarecisa.org.br
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```

renew (_Let's Encrypt certificates are valid for 90 days_)
```bash
sudo certbot renew
sudo systemctl restart ibarecisasystem && sudo systemctl restart nginx
```