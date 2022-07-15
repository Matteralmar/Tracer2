# Tracer

Django build bug-tracking system

---

## Getting Started

To run this project locally you will need to set your environment variables

1. Create a virtual environment inside the project by running `virtualenv venv` or other commands in your terminal
2. Activate venv using `source venv/bin/activate`
3. Install all the needed packages from "requirements.txt"
4. Install PostgreSQL to your computer, create new database and connect it to the project
5. Create a new file named `.env` inside the `bugTrack` folder
6. Copy all the variables inside `bugTrack/.template.env` and assign your own values to them
7. Make migrations by running `python manage.py migrate` in your terminal
8. Run `export READ_DOT_ENV_FILE=True` inside your terminal so that your environment variables file will be read
9. Run server using `python manage.py runserver` command