#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -q streamlit streamlit-authenticator==0.2.2 pandas
python3 popular_db.py
python3 -m streamlit run app.py
