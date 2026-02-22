# Survey App

This project consists of two main parts:
1.  **Flask Web Application** (`app.py`): A web-based survey system.
2.  **GUI Application** (`nasa-tlx.py`): A standalone GUI for NASA-TLX surveys.

## Prerequisites

-   Python 3.x
-   pip (Python package installer)

## Installation

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install flask appJar
```

## Running the Applications

### 1. Flask Web Application
To run the web application:

```bash
python app.py
```

The application will be available at `http://127.0.0.1:5001` by default.

### 2. GUI Application
To run the standalone NASA-TLX GUI:

```bash
python nasa-tlx.py
```

## Project Structure
-   `app.py`: Main Flask application.
-   `nasa-tlx.py`: Standalone GUI application.
-   `templates/`: HTML templates for the Flask application.
-   `config.json`: Configuration settings.
-   `results.csv`: Results from the Flask application.
-   `nasa-tlx-results.txt`: Results from the GUI application.
