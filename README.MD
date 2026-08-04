# 🦷 DentiFlow

> A web platform that connects dental laboratories, dental clinics, and independent dentists through a centralized ecosystem for work order management, communication, and service discovery.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.2-success?logo=django)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)
![SQLite](https://img.shields.io/badge/Database-SQLite-blue)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

---

# 📖 Overview

DentiFlow is a web application designed to improve communication and workflow between dental laboratories, dental clinics, and independent dentists.

The platform centralizes the complete lifecycle of a dental work order, from its creation to its final delivery, while also providing a marketplace where clinics and dentists can discover laboratories and specialists based on ratings, specialties, experience, and service quality.

---

# ✨ Main Features

- 🔐 User authentication and authorization
- 👨‍⚕️ Dental clinics management
- 🦷 Independent dentists management
- 🏭 Dental laboratories management
- 📦 Work order lifecycle tracking
- 📄 File upload (Images, PDFs, STL files)
- 💬 Internal chat between participants
- ⭐ Ratings and reviews
- 🔎 Marketplace for laboratories and specialists
- 📊 Personalized dashboards
- 🔔 Notifications

---

# 🏗️ Architecture

The project follows a **Modular Monolith Architecture** using Django's **Model-View-Template (MVT)** pattern.

```
Dentiflow
│
├── apps/
├── config/
├── templates/
├── static/
├── media/
├── docs/
└── manage.py
```

The application is organized by business domains to promote scalability and maintainability.

---

# 🛠️ Technology Stack

| Layer | Technology |
|--------|------------|
| Language | Python 3.11 |
| Backend | Django 5 |
| Frontend | HTML5 + Bootstrap 5 |
| Templates | Django Templates |
| Database | SQLite (Development) |
| Version Control | Git & GitHub |
| Methodology | Scrum |
| Architecture | Modular Monolith (MVT) |

---

# 📂 Project Structure

```
Dentiflow
│
├── apps/
│
├── config/
│
├── docs/
│
├── media/
│
├── static/
│   ├── css/
│   ├── img/
│   ├── js/
│   └── uploads/
│
├── templates/
│
├── requirements.txt
├── manage.py
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/your-organization/dentiflow.git

cd Dentiflow
```

---

## 2. Create a virtual environment

```bash
python -m venv .venv
```

---

## 3. Activate the virtual environment

### Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 5. Apply migrations

```bash
python manage.py migrate
```

---

## 6. Create an administrator

```bash
python manage.py createsuperuser
```

---

## 7. Run the project

```bash
python manage.py runserver
```

Open:

```
http://127.0.0.1:8000
```

---

# 👥 Team

| Name | 
|------|
| Samuel Salazar Ospina | 
| Daniel Villegas | 
| Santiago Meneses | 
| Juan Fernando Duque | 

---

# 🚀 Development Workflow

The team follows Git Flow using feature branches.

```
main

↓

develop

↓

feature/accounts

feature/orders

feature/chat

feature/marketplace
```

Every new feature must be developed in an independent branch and merged through Pull Requests.

---


# 📚 Documentation

Project documentation can be found in the **docs/** directory.

- Software Requirements Specification (SRS)
- Architecture
- UML Diagrams
- Entity Relationship Diagram (ERD)
- Sprint Documentation

---

# 📄 License

This project was developed for academic purposes as part of the Software Engineering course at Universidad EAFIT.

Future commercial use may require additional licensing and legal considerations.