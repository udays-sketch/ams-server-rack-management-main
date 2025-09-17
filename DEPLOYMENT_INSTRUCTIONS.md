# Server Rack Change Detection Web Application - Deployment Instructions

This document provides instructions for deploying the Server Rack Change Detection Web Application on your own server.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Web server (e.g., Nginx, Apache) for production deployment

## Installation Steps

### 1. Set Up Environment

```bash
# Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Application

The application requires several directories for storing uploads, results, and the mock asset management system database:

```bash
# Create necessary directories if they don't exist
mkdir -p uploads results mock_ams
```

### 3. Run the Application

#### Development Mode

For testing and development purposes:

```bash
# Run the Flask application
python -m src.main
```

The application will be available at http://localhost:5000

#### Production Deployment

For production deployment, it's recommended to use a WSGI server like Gunicorn:

1. Install Gunicorn:
```bash
pip install gunicorn
```

2. Create a WSGI entry point (wsgi.py):
```python
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from src.main import app

if __name__ == "__main__":
    app.run()
```

3. Run with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:8000 wsgi:app
```

4. Configure Nginx or Apache as a reverse proxy (recommended for production):

Example Nginx configuration:
```
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Verify Installation

1. Open a web browser and navigate to your server URL
2. Verify that you can access all pages:
   - Home page
   - Compare page
   - Asset Management page
   - Reports page

## Directory Structure

- `src/` - Application source code
  - `models/` - Core logic modules
  - `routes/` - API endpoints
  - `static/` - Static assets (CSS, JS, images)
  - `templates/` - HTML templates
  - `main.py` - Application entry point
- `uploads/` - Directory for uploaded images
- `results/` - Directory for comparison results
- `mock_ams/` - Directory for the mock asset management system database
- `requirements.txt` - Python dependencies
- `user_guide.md` - User guide for the application

## Troubleshooting

### Common Issues

1. **Application fails to start**
   - Check that all dependencies are installed: `pip install -r requirements.txt`
   - Verify that Python version is 3.8 or higher: `python --version`
   - Ensure all required directories exist: `uploads/`, `results/`, `mock_ams/`

2. **Image comparison not working**
   - Verify that OpenCV is installed correctly: `pip install opencv-python`
   - Check that Tesseract OCR is installed: `sudo apt-get install tesseract-ocr`

3. **Database errors**
   - Ensure the `mock_ams/` directory exists and is writable
   - Check for database corruption: delete the database file and restart the application to recreate it

4. **Permission issues**
   - Ensure the application has write permissions to the `uploads/`, `results/`, and `mock_ams/` directories

## Security Considerations

For production deployment, consider the following security measures:

1. Enable HTTPS using SSL/TLS certificates
2. Implement user authentication
3. Set up proper file upload validation and restrictions
4. Configure appropriate server hardening measures
5. Regularly update dependencies to patch security vulnerabilities

## Backup and Maintenance

1. Regularly backup the `mock_ams/` directory containing the database
2. Monitor disk usage in the `uploads/` and `results/` directories
3. Implement a cleanup strategy for old uploads and results
4. Set up logging for troubleshooting and monitoring

## Support

If you encounter any issues during deployment, please contact:
- Email: support@saltmine.com
- Phone: (555) 123-4567
