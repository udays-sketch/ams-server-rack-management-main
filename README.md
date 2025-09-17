# Server Rack Change Detection Web Application

A web application for detecting hardware changes in server racks using visual AI and reconciling these findings with asset management records.

## Prerequisites

- **Python 3.10** (required - the application has dependencies that are not compatible with other versions)
- Tesseract OCR (required for text extraction from images)
- System libraries:
  - OpenGL libraries (required by OpenCV)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd deploy_package
```

### 2. Install system dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update && sudo apt-get install -y libgl1-mesa-glx
```

#### Alpine Linux:
```bash
apk add --no-cache libgl mesa-gl
```

#### NixOS/Nix:
```bash
nix-env -i mesa
# or use in a nix-shell
# nix-shell -p mesa
```

#### macOS:
OpenGL libraries are included with the system.

#### Windows:
OpenGL libraries are typically included with graphics drivers.

### 3. Set up a Python 3.10 virtual environment

Make sure you have Python 3.10 installed:

```bash
# Check installed Python versions
python3 --version

# If Python 3.10 is not your default version, you may need to specify it:
python3.10 --version
```

Create a virtual environment using Python 3.10:

```bash
python3.10 -m venv venv
```

Activate the virtual environment:

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

### 4. Install dependencies

With the virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Install Tesseract OCR

#### macOS:
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr
```

#### Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

## Directory Structure

The application requires several directories for storing uploads, results, and the mock asset management system database:

```bash
# Create necessary directories if they don't exist
mkdir -p uploads results mock_ams
```

## Running the Application

With the virtual environment activated, run:

```bash
python -m src.main
```

The application will be available at:
- http://localhost:5001

## Usage Guide

Please refer to the [User Guide](user_guide.md) for detailed instructions on using the application.

## Troubleshooting

### Port 5000 already in use

The application runs on port 5001 by default. If this port is in use:

1. Edit `src/main.py` and change the port number:
   ```python
   app.run(host='0.0.0.0', port=5001, debug=True)
   ```

### Matplotlib errors on macOS

If you encounter errors related to matplotlib GUI on macOS, verify that the file `src/models/image_comparison.py` has the following lines near the top:

```python
# Set matplotlib to use non-GUI backend
import matplotlib
matplotlib.use('Agg')  # Use Agg backend (non-GUI) to avoid threading issues
import matplotlib.pyplot as plt
```

### Missing templates

If you encounter template errors, ensure that the `src/templates` directory contains:
- 404.html
- 500.html
- compare.html
- assets.html
- reports.html

## License

[Specify license information] 