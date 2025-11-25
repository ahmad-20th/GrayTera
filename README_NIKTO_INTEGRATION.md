# Nikto Scanner Integration for GrayTera

This document explains how the **Nikto scanner** was integrated into the GrayTera
framework, including:

- Scanner registration
- Running Nikto from within the framework
- XML parsing
- JSON and SQLite persistence
- How to view results

---

## 📌 1. How the Integration Works

The integration consists of the following files:

| File | Purpose |
|------|----------|
| `scanners/nikto_scanner.py` | Main scanner wrapper for Nikto |
| `scanners/__init__.py` | Registers the scanner inside GrayTera |
| `results_viewer.py` | Reads SQLite results and displays them |
| `.gitlab-ci.yml` | Provides optional GitLab CI integration |

Nikto runs using an external binary (`nikto` CLI), generates an XML report,
and the parser extracts vulnerability entries into the framework.

---

## 📌 2. Running the Scanner

### **Basic Run (no storage):**

```bash
python3 - << 'EOF'
from scanners.nikto_scanner import NiktoScanner
scanner = NiktoScanner()
results = scanner.scan("http://testphp.vulnweb.com")
print(results)
EOF
