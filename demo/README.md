# Django reCAPTCHA Enterprise REST API Demo

This is a complete Django REST API project demonstrating how to use `drf-recaptcha-enterprise` in a real application. The demo provides a pure REST API without any frontend templates.

## Features

- **Contact Form API** with reCAPTCHA Enterprise validation
- **REST API endpoints** for contact form submission and retrieval
- **API Endpoints** for form submission
- **Frontend Integration** with HTML/JavaScript examples
- **Configuration Examples** for different environments

## Setup

### 1. Install Dependencies

```bash
cd demo
pip install -r requirements.txt
```

### 2. Configure reCAPTCHA Enterprise

1. Set up your Google Cloud project and enable reCAPTCHA Enterprise API
2. Create a reCAPTCHA Enterprise key
3. Set up authentication (service account key or default credentials)

### 3. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
RECAPTCHA_ENTERPRISE_PROJECT_ID=your-project-id
RECAPTCHA_ENTERPRISE_SITE_KEY=your-site-key

# Django Configuration
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 5. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to see the demo application.

## Project Structure

```
demo/
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
├── .env                     # Your environment variables (create this)
├── demo_project/            # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL configuration
│   └── wsgi.py              # WSGI configuration
├── apps/                    # Django applications
│   └── contact/             # Contact form app
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
```

## API Endpoints

### API Information
- `GET /api/` - Get API information and available endpoints

### Contact Form
- `POST /api/contact/` - Submit contact form with reCAPTCHA validation
- `GET /api/contact/list/` - List all contact submissions
- `GET /api/contact/{id}/` - Get specific contact submission
- `GET /api/contact/submissions/` - ViewSet endpoint for contact submissions


## API Testing

You can test the API endpoints using:

- **curl** commands (examples below)
- **Postman** or similar API testing tools
- **Django REST Framework browsable API** at `/api/`
- **Any HTTP client** that supports JSON requests

### Curl Examples

#### Get API Information
```bash
curl -X GET http://127.0.0.1:8001/api/ | python -m json.tool
```

#### List All Contact Submissions
```bash
curl -X GET http://127.0.0.1:8001/api/contact/list/ | python -m json.tool
```

#### Get Specific Contact Submission
```bash
curl -X GET http://127.0.0.1:8001/api/contact/1/ | python -m json.tool
```

#### Submit Contact Form with reCAPTCHA
```bash
curl -X POST http://127.0.0.1:8001/api/contact/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "message": "Hello, this is a test message!",
    "recaptcha_token": "your_recaptcha_token_here"
  }' | python -m json.tool
```

#### Access Django Admin
```bash
curl -I http://127.0.0.1:8001/admin/
```

## Testing

Run the tests to verify everything is working:

```bash
python manage.py test
```

## Production Deployment

For production deployment:

1. Set `DEBUG=False` in your environment
2. Configure proper database (PostgreSQL recommended)
3. Set up static file serving
4. Configure proper logging
5. Use HTTPS for reCAPTCHA to work properly

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Make sure your service account key is valid and has the correct permissions
2. **reCAPTCHA Not Loading**: Ensure your site key is correct and the domain is registered
3. **Validation Failures**: Check that your expected action matches what you're sending from the frontend

### Debug Mode

Enable debug logging by setting:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'drf_recaptcha_enterprise': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Support

For issues and questions:

1. Check the [main package documentation](../README.md)
2. Review the [Google reCAPTCHA Enterprise documentation](https://cloud.google.com/recaptcha/docs)
3. Create an issue in the project repository
