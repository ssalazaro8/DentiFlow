# DentiFlow

*Cada caso, de principio a fin.*

DentiFlow is a web platform for managing dental laboratory cases. It follows
a case from the moment a clinic registers it until the laboratory delivers
it, keeping a record of every production stage along the way.

Academic project for the Software Engineering course at Universidad EAFIT.

## Why

A dental laboratory works with several clinics at the same time. Every case
(a crown, a bridge, an implant) arrives with its information, its files and
a due date, and goes through several production stages before it returns to
the clinic.

That coordination usually happens over chat, email and spreadsheets, so
nobody knows for certain where a case stands: the clinic calls to ask, the
laboratory checks its folders, and delays are found late.

DentiFlow brings that flow into one place. Clinics register their cases with
the attached files, the laboratory accepts them and assigns a technician, and
each case moves through stages that are recorded with the person responsible
and the date.

## Project structure

```
DentiFlow
│
├── apps/
│   ├── accounts/        Authentication
│   ├── clinics/         Dental clinics
│   ├── common/          Shared utilities
│   ├── dental_cases/    Cases, search, filters, delivery and dashboard
│   ├── documents/       Files attached to a case
│   ├── inventory/       Materials, consumption and stock alerts
│   ├── laboratories/    Laboratories, authorized users and technicians
│   ├── reports/         Operational reports
│   ├── users/           Laboratory staff
│   └── workflow/        Production stages, history and timeline
│
├── config/              Settings and root URL routing
├── templates/           Shared templates and layout
├── static/              Static files (brand stylesheet)
│
├── requirements.txt
└── manage.py
```

Built with Python, Django 5.2, Bootstrap 5 and SQLite. Each application is
split in layers: `views.py` for presentation, `services.py` for business
rules, `selectors.py` for queries and `models.py` for data.

## How to run it

Requires Python 3.11 or later.

### 1. Clone the repository

```bash
git clone https://github.com/ssalazaro8/DentiFlow.git
cd DentiFlow
```

### 2. Create and activate a virtual environment

On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply the migrations

```bash
python manage.py migrate
```

Run this step again after every update of the repository.

### 5. Create an administrator

```bash
python manage.py createsuperuser
```

The command asks for a username, an email (optional) and a password.

### 6. Run the server

```bash
python manage.py runserver
```

The application is available at `http://127.0.0.1:8000`. To use another
port, pass it as a parameter, for example `python manage.py runserver 8080`.

On Windows, if `python` is not recognised, use `py` in its place.

### 7. First steps

1. Sign in at `/accounts/login/` with the administrator.
2. Open `/admin/` and register a laboratory, a clinic and the inventory
   materials. Add your user to the laboratory's authorized users and
   technicians.
3. Create a case from **Cases > Create Case** and follow it through
   acceptance, technician assignment, production and delivery.

## Team

| Member |
|---|
| Samuel Salazar Ospina |
| Santiago Meneses |
| Juan Fernando Duque |

Diagrams, requirements and sprint deliverables are in the
[project wiki](https://github.com/ssalazaro8/DentiFlow/wiki).
