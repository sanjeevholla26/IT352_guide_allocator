rm -r Allocator/migrations
rm db.sqlite3
mkdir Allocator/migrations
touch Allocator/migrations/__init__.py
rm -r logs
mkdir logs
touch logs/django.log
python3 manage.py makemigrations
python3 manage.py migrate
python3 builder.py