I would recommend deleting the migrations files and doing this:
1. Run migrations
1.1. py manage.py makemigrations users
1.2. py manage.py migrate
1.3. Create a superuser (necessary, because it will be the default user, look at the code)
1.4. py manage.py init_groups
1.5. py manage.py makemigrations
1.5. Change the migrations file of the treasury app to: upload_to=treasury.utils.custom_upload_to,
Somehow django generates upload_to=treasury.utils.custom_upload_to.custom_upload_to, what throws and error
1.6. python manage.py migrate

The second step will create permissions groups and set the permissions
You can change the standard permissions in run time or in the users app /management/init_groups.py