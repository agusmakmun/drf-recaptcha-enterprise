# Django REST Framework reCAPTCHA Enterprise

A Django REST Framework integration for Google reCAPTCHA Enterprise v1, providing easy-to-use serializers, fields, and validators for protecting your API endpoints from bots and abuse.

## Features

- **Easy Integration**: Simple serializers and fields for Django REST Framework
- **Enterprise Grade**: Uses Google reCAPTCHA Enterprise v1 API
- **Flexible Configuration**: Support for score-based and action-based validation
- **Request Context**: Automatically extracts user IP and user agent from requests
- **Comprehensive Validation**: Detailed error messages and validation results
- **Type Hints**: Full type annotation support for better development experience

## Installation

```bash
pip install drf-recaptcha-enterprise
```

## Requirements

- Python 3.10+
- Django 3.2+
- Django REST Framework 3.12+
- Google Cloud reCAPTCHA Enterprise API access

```mermaid
graph TD
    A[User submits form] --> B[Frontend gets reCAPTCHA token]
    B --> C[Token sent to Django backend]
    C --> D{GOOGLE_APPLICATION_CREDENTIALS set?}
    D -->|No| E[❌ Authentication fails]
    D -->|Yes| F[✅ Authenticate with Google Cloud]
    F --> G[Verify token with reCAPTCHA API]
    G --> H[Return verification result]
    H --> I[Process form if valid]
    
    E --> J[❌ Form rejected - security compromised]
    I --> K[✅ Form processed - security maintained]
```

## Setup

### 1. Install Dependencies

```bash
pip install drf-recaptcha-enterprise
```

### 2. Configure Google Cloud

1. Enable the reCAPTCHA Enterprise API in your Google Cloud project
2. Create a reCAPTCHA Enterprise key
3. Set up authentication (service account key or default credentials)

### 3. Django Settings

Add the following to your Django settings:

```python
# settings.py
import os

# reCAPTCHA Enterprise Configuration
# Project ID is automatically detected from GOOGLE_APPLICATION_CREDENTIALS
# You can override it with RECAPTCHA_ENTERPRISE_PROJECT_ID if needed
RECAPTCHA_ENTERPRISE_PROJECT_ID = os.getenv("RECAPTCHA_ENTERPRISE_PROJECT_ID", None)
RECAPTCHA_ENTERPRISE_SITE_KEY = os.getenv("RECAPTCHA_ENTERPRISE_SITE_KEY", "your-recaptcha-site-key")

# Optional: Set minimum score threshold (default: 0.5)
RECAPTCHA_ENTERPRISE_MIN_SCORE = float(os.getenv("RECAPTCHA_ENTERPRISE_MIN_SCORE", "0.5"))

# Optional: Set expected action for action-based scoring
RECAPTCHA_ENTERPRISE_EXPECTED_ACTION = os.getenv("RECAPTCHA_ENTERPRISE_EXPECTED_ACTION", "submit")
```

**⚠️ Security Note**: Always use environment variables for sensitive configuration. Never hardcode API keys or project IDs in your source code!

### 4. Google Cloud Authentication

The package supports multiple ways to provide Google Cloud credentials:

#### **Option 1: Direct Credentials Parameter (Recommended)**
```python
from drf_recaptcha_enterprise import ReCaptchaEnterpriseClient

# With service account file path
client = ReCaptchaEnterpriseClient(
    credentials="/path/to/your/service-account-key.json"
)

# With credentials object
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(
    "/path/to/your/service-account-key.json"
)
client = ReCaptchaEnterpriseClient(credentials=credentials)
```

#### **Option 2: Environment Variable**
```bash
# Set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

#### **Option 3: Application Default Credentials**
```bash
# For production environments
gcloud auth application-default login
```

#### **Project ID Detection**
The package automatically detects your Google Cloud project ID from:
1. **Service account credentials** (from credentials parameter or file)
2. **RECAPTCHA_ENTERPRISE_PROJECT_ID** (Django settings override)
3. **gcloud config** (current project from `gcloud config get-value project`)

#### **Verify Authentication:**
```python
from drf_recaptcha_enterprise.client import check_google_cloud_authentication

auth_status = check_google_cloud_authentication()
print(f"Authenticated: {auth_status['authenticated']}")
print(f"Project ID: {auth_status['project_id']}")
```

### 5. Usage Examples

#### Option A: Direct Credentials Parameter (Recommended)

```python
from drf_recaptcha_enterprise import ReCaptchaEnterpriseClient

# Initialize client with credentials file path
client = ReCaptchaEnterpriseClient(
    credentials="/path/to/your/service-account-key.json"
)

# Or with credentials object
from google.oauth2 import service_account
credentials = service_account.Credentials.from_service_account_file(
    "/path/to/your/service-account-key.json"
)
client = ReCaptchaEnterpriseClient(credentials=credentials)
```

#### Option B: Environment Variable

```python
# settings.py
import os

# Set up authentication
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/path/to/your/service-account-key.json'
```

#### Option C: Application Default Credentials

```bash
gcloud auth application-default login
```

## Usage

### Basic Usage with Serializer

```python
from rest_framework import serializers
from drf_recaptcha_enterprise import ReCaptchaEnterpriseSerializer

class MyFormSerializer(ReCaptchaEnterpriseSerializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    message = serializers.CharField()
    
    def create(self, validated_data):
        # Remove reCAPTCHA token from data
        validated_data.pop('recaptcha_token', None)
        
        # Your business logic here
        return validated_data
```

### Using the Mixin

```python
from rest_framework import serializers
from drf_recaptcha_enterprise import ReCaptchaEnterpriseMixin

class UserRegistrationSerializer(ReCaptchaEnterpriseMixin, serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
```

### Custom Field Usage

```python
from rest_framework import serializers
from drf_recaptcha_enterprise import ReCaptchaEnterpriseField

class MySerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    recaptcha = ReCaptchaEnterpriseField(
        min_score=0.7,  # Custom minimum score
        expected_action="contact_form"  # Custom action
    )
```

### Using Validators

```python
from rest_framework import serializers
from drf_recaptcha_enterprise import ReCaptchaEnterpriseValidator

class MySerializer(serializers.Serializer):
    recaptcha_token = serializers.CharField(
        validators=[ReCaptchaEnterpriseValidator(min_score=0.6)]
    )
```

### View Integration

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MyFormSerializer

class MyFormView(APIView):
    def post(self, request):
        serializer = MyFormSerializer(data=request.data)
        
        if serializer.is_valid():
            # Get reCAPTCHA verification result
            recaptcha_result = serializer.get_recaptcha_verification_result()
            
            # Your business logic here
            result = serializer.create(serializer.validated_data)
            
            return Response({
                'message': 'Form submitted successfully',
                'recaptcha_score': recaptcha_result['score']
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## Frontend Integration

### HTML Example

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://www.google.com/recaptcha/enterprise.js?render=YOUR_SITE_KEY"></script>
</head>
<body>
    <form id="contact-form">
        <input type="text" name="name" placeholder="Name" required>
        <input type="email" name="email" placeholder="Email" required>
        <textarea name="message" placeholder="Message" required></textarea>
        <button type="submit">Submit</button>
    </form>

    <script>
        grecaptcha.enterprise.ready(function() {
            document.getElementById('contact-form').addEventListener('submit', function(e) {
                e.preventDefault();
                
                grecaptcha.enterprise.execute('YOUR_SITE_KEY', {action: 'contact_form'}).then(function(token) {
                    // Add token to form data
                    const formData = new FormData(e.target);
                    formData.append('recaptcha_token', token);
                    
                    // Submit to your API
                    fetch('/api/contact/', {
                        method: 'POST',
                        body: formData
                    }).then(response => response.json())
                      .then(data => console.log('Success:', data))
                      .catch(error => console.error('Error:', error));
                });
            });
        });
    </script>
</body>
</html>
```

### React Example

```jsx
import React, { useState } from 'react';

function ContactForm() {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        message: ''
    });

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        try {
            // Get reCAPTCHA token
            const token = await window.grecaptcha.enterprise.execute('YOUR_SITE_KEY', {
                action: 'contact_form'
            });
            
            // Submit form with token
            const response = await fetch('/api/contact/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...formData,
                    recaptcha_token: token
                })
            });
            
            const result = await response.json();
            console.log('Success:', result);
        } catch (error) {
            console.error('Error:', error);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="text"
                name="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Name"
                required
            />
            <input
                type="email"
                name="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="Email"
                required
            />
            <textarea
                name="message"
                value={formData.message}
                onChange={(e) => setFormData({...formData, message: e.target.value})}
                placeholder="Message"
                required
            />
            <button type="submit">Submit</button>
        </form>
    );
}
```

## Configuration Options

### Field Options

- `project_id`: Google Cloud project ID (optional, uses settings if not provided)
- `site_key`: reCAPTCHA site key (optional, uses settings if not provided)
- `min_score`: Minimum score threshold (0.0 to 1.0, default: 0.5)
- `expected_action`: Expected action name for action-based scoring
- `write_only`: Field is write-only (default: True)
- `required`: Field is required (default: True)

### Serializer Options

- `recaptcha_field_name`: Name of the reCAPTCHA field (default: 'recaptcha_token')
- `recaptcha_project_id`: Google Cloud project ID
- `recaptcha_site_key`: reCAPTCHA site key
- `recaptcha_min_score`: Minimum score threshold
- `recaptcha_expected_action`: Expected action name

## Error Handling

The package provides detailed error messages for different validation failures:

- **Token Required**: "reCAPTCHA token is required."
- **Verification Failed**: "reCAPTCHA verification failed. Please try again."
- **Score Too Low**: "reCAPTCHA score too low (0.3). Minimum required: 0.5."
- **Invalid Token**: "Invalid reCAPTCHA token."

## Advanced Usage

### Custom Client Configuration

```python
from drf_recaptcha_enterprise.client import ReCaptchaEnterpriseClient

# Custom client with specific configuration
client = ReCaptchaEnterpriseClient(
    project_id="custom-project-id",
    site_key="custom-site-key"
)

result = client.verify_token(
    token="your-token",
    user_ip="192.168.1.1",
    user_agent="Mozilla/5.0...",
    expected_action="custom_action",
    min_score=0.8
)
```

### Getting Verification Results

```python
# In your view or serializer
recaptcha_result = serializer.get_recaptcha_verification_result()

if recaptcha_result:
    print(f"Score: {recaptcha_result['score']}")
    print(f"Action: {recaptcha_result['action']}")
    print(f"Valid: {recaptcha_result['valid']}")
    print(f"Hostname: {recaptcha_result['hostname']}")
```

## Testing

```python
from django.test import TestCase
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock

class ReCaptchaTestCase(APITestCase):
    @patch('drf_recaptcha_enterprise.client.ReCaptchaEnterpriseClient.verify_token')
    def test_recaptcha_validation(self, mock_verify):
        # Mock successful verification
        mock_verify.return_value = {
            'success': True,
            'score': 0.8,
            'action': 'test_action',
            'valid': True,
            'hostname': 'localhost'
        }
        
        data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'message': 'Test message',
            'recaptcha_token': 'mock-token'
        }
        
        response = self.client.post('/api/contact/', data)
        self.assertEqual(response.status_code, 201)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the [documentation](https://drf-recaptcha-enterprise.readthedocs.io/)
2. Search [existing issues](https://github.com/agusmakmun/drf-recaptcha-enterprise/issues)
3. Create a [new issue](https://github.com/agusmakmun/drf-recaptcha-enterprise/issues/new)

## Changelog

### 1.0.0
- Initial release
- Support for reCAPTCHA Enterprise v1
- Django REST Framework integration
- Score-based and action-based validation
- Comprehensive error handling
