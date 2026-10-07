# OT Local Agent portable workspace

This folder is a local-first workspace.

## Important

- Contains code, SQLite database, templates, synthetic test data and setup scripts.
- On a new PC you need a Python interpreter.
- Ollama and LLM models are optional for non-LLM workflow.
- For LLM features install Ollama on target PC and make models available locally.
- Do not copy .venv between PCs. Create it again with setup_portable.ps1.

## First run on a new PC

1. Open PowerShell in this folder.
2. Run: powershell -ExecutionPolicy Bypass -File ./setup_portable.ps1
3. Run: powershell -ExecutionPolicy Bypass -File ./run_portable.ps1
4. Open http://127.0.0.1:8501

## Backup database

powershell -ExecutionPolicy Bypass -File ./backup_portable.ps1

## Security

Keep Streamlit telemetry disabled: browser.gatherUsageStats=false in config.toml.
According to the provided Streamlit privacy policy page, last updated April 2026, Streamlit is owned by Snowflake and governed by the Snowflake Privacy Notice.
If the folder contains real personal data, encrypt the USB drive and control access.
Do not sync this folder to cloud services unless encryption and legal basis are confirmed.
