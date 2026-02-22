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

The application will be available at `http://localhost:5001`.

# Local Network Access

To access the survey from another device (e.g., a tablet or another PC) on the same Wi-Fi/network:

1.  **Find your Local IP Address**:
    -   On Windows: Open Command Prompt and type `ipconfig`. Look for "IPv4 Address" (e.g., `192.168.1.15`).
2.  **Access from Browser**:
    -   On the other device, enter `http://<YOUR_IP_ADDRESS>:5001` in the browser.

## Troubleshooting: iPad/Safari "Information Not Secure"

When you click "Next" on an iPad, you might see a warning saying **"The information you are about to submit is not secure"**.

### Why it happens
This is a standard security feature in Safari. Since the app is running locally on your network without an SSL certificate (HTTP instead of HTTPS), Safari warns you whenever you submit a form.

### How to avoid it
1.  **Quick Bypass**: When the warning appears, simply click **"Send Anyway"** or **"Continue"**. This is perfectly safe for a local network survey.
2.  **Use Chrome**: Chrome on iPad often has a less intrusive warning (or allows you to "Always allow" for that IP).
3.  **Enable HTTPS (Advanced)**:
    If you want to completely remove the warning, you can run the app with a self-signed certificate.
    -   Install `pyopenssl`: `pip install pyopenssl`
    -   In `app.py`, change the last line to:
        `app.run(debug=True, port=5001, host='0.0.0.0', ssl_context='adhoc')`
    -   Access via `https://` instead of `http://`. (Note: You will then see a "Certificate Not Trusted" warning, which you can bypass once in Safari settings for that site).

## Building/Packaging

Since this is a Python/Flask application, it does not require a formal "build" step like compiled languages. Running `pip install` sets up the environment.

However, if you wish to create a standalone executable for the **GUI Application** (`nasa-tlx.py`), you can use `PyInstaller`:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole nasa-tlx.py
```
This will create a `dist/nasa-tlx.exe` (on Windows) that can run without Python installed. Note that the Flask app (`app.py`) is best run as a service/script and is not typically packaged as an EXE.

## Project Structure
-   `app.py`: Main Flask application.
-   `nasa-tlx.py`: Standalone GUI application.
-   `templates/`: HTML templates for the Flask application.
-   `config.json`: Configuration settings.
-   `results.csv`: Results from the Flask application.
-   `nasa-tlx-results.txt`: Results from the GUI application.
