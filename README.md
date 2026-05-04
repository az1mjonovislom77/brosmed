# Brosmed - Medical Facility Management System

## Project Description

Brosmed is a comprehensive web application designed to streamline the operations of a medical facility or laboratory. It provides modules for managing users, doctors, reception, cashier services, departments, and laboratory processes. The system features a robust REST API, an administrative interface, and potentially integrates with a Telegram bot for notifications or specific interactions.

## Key Features

*   **User Management**: Secure authentication and authorization for different roles (e.g., admin, doctor, cashier, reception).
*   **Doctor Module**: Management of doctor profiles, schedules, and patient interactions.
*   **Reception Module**: Patient registration, appointment scheduling, and general inquiries.
*   **Cashier Module**: Billing, payment processing, and financial reporting.
*   **Department Management**: Organization and oversight of various medical departments.
*   **Laboratory Management**: Tracking of lab tests, results, and equipment.
*   **RESTful API**: A well-documented API for programmatic access and integration with other systems.
*   **Admin Panel**: An intuitive administrative interface (powered by Django Jazzmin) for system configuration and data management.
*   **Multi-language Support**: (Inferred from `django-modeltranslation` and `django-parler`) Support for multiple languages.
*   **Report Generation**: Ability to generate various reports in formats like PDF, Excel, and Word (inferred from `reportlab`, `openpyxl`, `python-docx`).
*   **Image Processing**: (Inferred from `Pillow`, `pillow_heif`) Handling and processing of medical images.
*   **Telegram Bot Integration**: (Inferred from `python-telegram-bot`) Potential for automated notifications, quick queries, or specific bot-driven workflows.
*   **AI Integration**: (Inferred from `openai`) Possible use of AI for tasks like data analysis, intelligent suggestions, or enhanced search.

## Technologies Used

*   **Backend**:
    *   Python 3.x
    *   Django (Web Framework)
    *   Django REST Framework (for API)
    *   PostgreSQL (Database, via `psycopg2`)
    *   Redis (Caching and task queuing, via `django-redis`)
    *   `django-jazzmin` (Admin Interface)
    *   `django-modeltranslation`, `django-parler` (Internationalization)
    *   `drf-spectacular`, `drf-yasg` (API Documentation)
    *   `python-decouple`, `python-dotenv` (Environment variables)
*   **Utilities & Libraries**:
    *   `aiohttp`, `aiogram` (Asynchronous operations, Telegram bot)
    *   `openai` (AI integration)
    *   `Pillow`, `pillow_heif` (Image processing)
    *   `openpyxl` (Excel file handling)
    *   `python-docx` (Word document handling)
    *   `reportlab` (PDF generation)
    *   `PyJWT` (JWT authentication)

## Setup and Installation

Follow these steps to get the Brosmed project up and running on your local machine.

### Prerequisites

*   Python 3.8+
*   PostgreSQL
*   Redis

### 1. Clone the Repository

```bash
git clone https://github.com/az1mjonovislom77/brosmed.git
cd brosmed
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory and add your configuration.
Example `.env`:

```
SECRET_KEY='your_django_secret_key'
DEBUG=True
DATABASE_URL='postgres://user:password@host:port/dbname'
REDIS_URL='redis://localhost:..../0'
OPENAI_API_KEY='your_openai_api_key' # If using OpenAI features
TELEGRAM_BOT_TOKEN='your_telegram_bot_token' # If using Telegram bot
```

### 5. Database Setup

Apply database migrations:

```bash
python manage.py migrate
```

Create a superuser for the admin panel:

```bash
python manage.py createsuperuser
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

The application will be accessible at `http://127.0.0.1:8000/`.
The admin panel will be at `http://127.0.0.1:8000/admin/`.

### 7. Run the Telegram Bot (Optional)

If the Telegram bot functionality is enabled, you might need to run it separately:

```bash
python bot.py
```
*(Note: This assumes `bot.py` is designed to be run directly. Adjust if it's integrated differently, e.g., via Django management command or a separate process manager.)*

## Usage

*   Navigate to `http://127.0.0.1:8000/` to access the main application.
*   Log in to the admin panel at `http://127.0.0.1:8000/admin/` with your superuser credentials to manage data.
*   Interact with the REST API using tools like Postman or curl.

## API Documentation

The API documentation is automatically generated and available at:
*   **Swagger UI**: `http://127.0.0.1:8000/swagger/`
*   **ReDoc**: `http://127.0.0.1:8000/redoc/`

## Contributing

Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create a new branch (`git checkout -b feature/your-feature-name`).
3.  Make your changes.
4.  Commit your changes (`git commit -m 'Add some feature'`).
5.  Push to the branch (`git push origin feature/your-feature-name`).
6.  Open a Pull Request.
