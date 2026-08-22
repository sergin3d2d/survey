# Survey Application

An **experiment questionnaire form** system designed for conducting experimental task load and usability feedback (e.g., NASA-TLX, PCUE-Q) across randomized trial conditions. Includes a web server and a standalone desktop backup GUI.

---

## 📖 Complete Documentation

All detailed guides for setting up, configuring, and analyzing data are consolidated in a single file:

### 📄 [DOCUMENTATION.md](DOCUMENTATION.md)

*   **Setup & Installation**: Prerequisites, install dependencies, running servers.
*   **Configuration Guide**: Editing `config.json` rules, setting up multipliers sliders.
*   **Architecture & Workflow**: Pipeline flowchart step redirects state tables.
*   **Data Structure & Analysis**: Column headers matrices grids with sample analysis formula script codes.

---

## 🚀 Quick Run

If everything is already installed:

```bash
# Start Web Survey
python app.py

# OR Start Standalone GUI
python nasa-tlx.py
```
*Access Web server locally via: `http://localhost:5001`*
