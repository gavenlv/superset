# Apache Superset Local Development Setup Guide

This guide will help you set up Apache Superset for local development on Windows.

Postgresql DB:
```
CREATE DATABASE superset_db WITH 
  ENCODING = 'UTF8' 
  LC_COLLATE = 'en_US.utf8' 
  LC_CTYPE = 'en_US.utf8' 
  TEMPLATE = template0;  

```

## Prerequisites

- Git
- Python 3.9+ (recommended: Python 3.9.x)
- Node.js 16+ (recommended: Node.js 16.x)
- npm 7+
- Microsoft Visual C++ Build Tools

## Initial Setup

### 1. Clone the Repository

```bash
git clone git@gitee.com:gavenlv/superset.git
cd superset
```

### 2. Python Environment Setup

#### 2.1 change dependency
#python-ldap==3.4.4 in requirements/development.txt

```command
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate.bat
python -m pip install --upgrade pip

# Install Python dependencies
pip install -r requirements/development.txt
```
### 3. Prepare .evn in root folder of the project
.env
```command
FLASK_APP = superset
FLASK_ENV = development
PYTHONPATH = D:\workspace\superset
SUPERSET_CONFIG_PATH = D:\workspace\superset\superset_config.py
SUPERSET_SECRET_KEY=fiVM2JDST7oP0SkXtge8RhCE+mtWk2GmoI7xHwMc5BsspcWfbMmWoqf8
SECRET_KEY=SUPERSET_SECRET_KEY
SUPERSET_DATABASE_URI=postgresql+psycopg2://postgres:root@localhost:25011/superset_db
SUPERSET_EXAMPLES_BASE_URL=http://localhost:8089/
```

### 4. Initialize the Database

```command
# Initialize the database
# run ddl in db
superset db upgrade
#create default roles and permisison
superset init
superset fab create-admin
```

### 5. Load example
* Download https://github.com/apache-superset/examples-data/archive/refs/heads/master.zip
* unzip and start with python
```
python -m http.server 8089
```
Load examples data
```
superset load_examples
```

### 5. Frontend Dependencies
* Install node modules
```command
cd superset-frontend
npm install
npm run dev

```

### 6. Start backend 
```
superset run -p 8088 --with-threads --reload --debugger
```

- Backend API server will be available at: http://localhost:8088
- Frontend development server will be available at: http://localhost:9000
