## Requirements
- Postgres (10.0 or higher)
- Python 3.5

## Installation
- Install python 3.5
- Install Postgres

### Create Postgres Database (windows)
- `psql -U postgres`
- `CREATE ROLE branchlinks WITH LOGIN PASSWORD 'secure_password';`
- `ALTER ROLE branchlinks CREATEDB;`
- `CREATE DATABASE branchlinks;`
- `GRANT ALL PRIVILEGES ON DATABASE branchlinks TO branchlinks;`


### Create Super User
- `./manage.py migrate`
- `./manage.py createsuperuser`

## Running the Server (and Migrations)
- `./manage.py migrate`
- `./manage.py runserver`
