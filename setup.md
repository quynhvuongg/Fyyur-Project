1. Install postgres

```sh
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql.service
```

2. Access postgres: sudo -i -u postgres/ sudo -u postgres psql
3. Create db:

```sh
createdb fyyur
```

or: sudo -u postgres createdb sammy

4. Init flask db

```sh
sudo apt install python3-dev libpq-dev
pip3 install psycopg2
pip install Flask-Migrate
flask db init
```

