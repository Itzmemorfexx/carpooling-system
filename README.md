# PoolMate - Carpooling System

A Django-based web application for carpooling that connects drivers with passengers.

## Features

- User Authentication (Registration and Login)
- Profile Management
- Ride Creation and Management
- Ride Search and Booking
- Admin Panel for System Management
- Responsive UI using Bootstrap

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

4. Create a superuser:
```bash
python manage.py createsuperuser
```

5. Run the development server:
```bash
python manage.py runserver
```

6. Visit http://127.0.0.1:8000/ in your browser

## Project Structure

- `poolmate/` - Main project directory
- `users/` - User authentication and profile management
- `rides/` - Ride management and booking system
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images) 