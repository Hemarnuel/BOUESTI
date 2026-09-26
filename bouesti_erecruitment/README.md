# BOUESTI E-Recruitment System

A full-stack web-based E-Recruitment System, built to match the design in
Chapter 3 of the project report: **Python + Django (MVT architecture)**,
**MySQL** as the relational database, and **HTML5, CSS3, Bootstrap 5,
JavaScript** on the frontend.

It supports three roles — **Administrator**, **Recruiter**, and
**Job Applicant** — and implements the full functional requirement list
from section 3.3.1: registration & secure login, job posting/search,
electronic application with CV upload, shortlisting, interview
scheduling, automatic notifications, user management, and recruitment
reports.

---

## 1. Project Structure

```
bouesti_erecruitment/
├── manage.py
├── requirements.txt
├── .env.example              # copy to .env and edit
├── bouesti_erecruitment/      # project settings, root urls
├── accounts/                  # custom User model, register/login/profile
├── recruitment/                # Job, Application, Interview, Notification
├── templates/                  # Bootstrap 5 HTML templates
├── static/                     # custom CSS/JS
└── media/                      # uploaded CVs (created at runtime)
```

---

## 2. Requirements

- Python 3.10+
- MySQL Server 8.x (or MariaDB) — **or** just use SQLite to try it out first
- pip / venv
- (Windows only, for MySQL) Microsoft C++ Build Tools, needed by `mysqlclient`

---

## 3. Setup in VS Code

```bash
# 1. Open the project folder in VS Code, then in the integrated terminal:

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env        # Windows: copy .env.example .env
```

In VS Code, select the `venv` interpreter (bottom-right corner, or
Ctrl+Shift+P → "Python: Select Interpreter") so linting and debugging work
correctly.

### Quick start (no MySQL needed yet)

The project runs on SQLite out of the box — perfect for demoing the system
to your supervisor before wiring up MySQL:

```bash
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@bouesti.edu.ng
# it will prompt for a password; the shell will ask for role too if you
# use createsuperuser directly. If it doesn't, set the role afterwards:
python manage.py shell -c "from accounts.models import User; u=User.objects.get(username='admin'); u.role='admin'; u.save()"

python manage.py runserver
```

Visit **http://127.0.0.1:8000/** — register as a Recruiter to post jobs,
or as a Job Applicant to browse and apply.

### Switching to MySQL (matches Chapter 3, section 3.6.4)

1. Install MySQL Server and create a database:
   ```sql
   CREATE DATABASE bouesti_erecruitment CHARACTER SET utf8mb4;
   ```
2. Edit `.env`:
   ```
   DB_ENGINE=mysql
   DB_NAME=bouesti_erecruitment
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```
3. Re-run migrations against MySQL:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

> `mysqlclient` (in requirements.txt) needs MySQL's development headers to
> build. On Ubuntu/Debian: `sudo apt install default-libmysqlclient-dev
> build-essential pkg-config`. On macOS: `brew install mysql pkg-config`.
> On Windows, install "Microsoft C++ Build Tools" or use the prebuilt
> wheel that pip fetches automatically for most Python versions.

---

## 4. Default User Roles

| Role | How the account is created |
|---|---|
| Administrator | `python manage.py createsuperuser`, or promote a user's `role` field via `/admin/` |
| Recruiter | Self-registers at `/accounts/register/`, selects "Recruiter" |
| Job Applicant | Self-registers at `/accounts/register/`, selects "Job Applicant" |

Administrators are **not** self-registered through the public form — this
is a deliberate security decision (see the comment in
`accounts/forms.py`) so a random visitor can never create an admin
account.

---

## 5. Key URLs

| URL | Purpose |
|---|---|
| `/` | Public homepage with latest vacancies |
| `/jobs/` | Search & browse all open vacancies |
| `/accounts/register/` | Create an account |
| `/accounts/login/` | Login |
| `/dashboard/` | Role-aware dashboard (Admin / Recruiter / Applicant) |
| `/jobs/new/` | Recruiter: post a new vacancy |
| `/jobs/<id>/applications/` | Recruiter: review applicants, shortlist, schedule interviews |
| `/applications/mine/` | Applicant: track my applications |
| `/notifications/` | Notifications inbox |
| `/admin-panel/users/` | Administrator: manage all accounts |
| `/admin-panel/reports/` | Administrator: recruitment reports |
| `/admin/` | Django's built-in admin panel (full data access) |

---

## 6. Deploying / Hosting

The project is a standard Django app, so it can be hosted anywhere Django
runs. A common, affordable path:

1. **Choose a host** — Railway, Render, PythonAnywhere, or a VPS
   (DigitalOcean/Linode) with `gunicorn` + `nginx` all work well. Managed
   MySQL is available on most of these (or use PlanetScale/Aiven for a
   free-tier MySQL instance).
2. **Before going live**, in `.env` set:
   ```
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
   DJANGO_SECRET_KEY=<generate a new long random string>
   ```
3. Collect static files: `python manage.py collectstatic`
4. Run behind a real WSGI server, e.g.:
   ```bash
   pip install gunicorn
   gunicorn bouesti_erecruitment.wsgi:application --bind 0.0.0.0:8000
   ```
5. Put nginx (or your host's equivalent) in front to serve `/static/` and
   `/media/` and proxy everything else to gunicorn.
6. Point your domain's DNS at the host, and set up HTTPS (Let's Encrypt is
   free) — `settings.py` already tightens cookie/HSTS security
   automatically once `DEBUG=False`.

For a first submission/demo to your supervisor, PythonAnywhere is the
simplest option: it gives you a MySQL database, a free subdomain, and a
web-based file editor with almost no configuration.

---

## 7. Testing

A full functional walkthrough (register → post job → apply with CV →
shortlist → schedule interview → notifications → admin reports) was run
against this exact codebase using Django's test client before delivery,
covering every functional requirement listed in Chapter 3, section 3.3.1,
and every row of the Table 3.1 test-case list (user registration, login,
job posting, job search, job application, interview scheduling,
notification delivery).

To write your own formal test cases for your project defense, add them
under a `tests.py` in `accounts/` or `recruitment/` and run:

```bash
python manage.py test
```

---

## 8. Notes for Your Project Report

- **3.6.2 Programming Language**: Python — used throughout, exactly as
  specified.
- **3.6.3 Django Framework**: MVT architecture — `models.py` (Model),
  `templates/` (Template), `views.py` (View) in both `accounts/` and
  `recruitment/`.
- **3.6.4 Database**: MySQL, switchable via `.env` (`DB_ENGINE=mysql`).
- **3.6.5 Frontend**: Bootstrap 5 + custom CSS/JS in `static/`.
- **3.4.8 Class Diagram**: implemented as `User` (parent, `accounts/models.py`)
  and `Job`, `Application`, `Interview`, `Notification`
  (`recruitment/models.py`), with `RecruiterProfile`/`ApplicantProfile`
  holding the role-specific attributes.
- **3.5 Database Design**: all tables use Django's ORM migrations,
  respecting 1NF/2NF/3NF as written in your normalization section — every
  table has an atomic primary key and no repeating groups.
