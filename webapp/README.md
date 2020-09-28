DataPlate - Data Access Portal
=================================

Web service and API that provides audited access to Data sets.


## Running locally

### Using docker-compose

This is the recommended option.

```bash
docker-compose -f docker-compose.yml up --build
```

Open your browser at http://localhost:5000 and use demo@dataplate.io / demo combination for logging in.

### Using venv

This option is useful for debugging.

First, you must have PostgreSQL up and running. This can be achieved easily using Docker:

```bash
docker run --rm -ti -e POSTGRES_USER=da -e POSTGRES_PASSWORD=da -e POSTGRES_DB=da -p 5432:5432 postgres:12.4
```

Prepare the virtual environment:

```bash
python3 -mvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create database schema:

```bash
DA_SECRET_KEY=BcmbPqfA6os9-5kdajQPUA \
DA_SQLALCHEMY_DATABASE_URI=postgresql://da:da@localhost/da \
DA_LOGIN_BACKEND=demo \
FLASK_APP=dataaccess.app \
flask db upgrade
```

Run the application:

```bash
DA_SECRET_KEY=BcmbPqfA6os9-5kdajQPUA \
DA_SQLALCHEMY_DATABASE_URI=postgresql://da:da@localhost/da \
DA_LOGIN_BACKEND=demo \
FLASK_APP=dataaccess.app \
flask run
```
