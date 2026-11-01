#!/usr/bin/env bash
# One command: generate data -> run SQL -> validate -> build Excel report
set -euo pipefail
python3 scripts/generate_data.py
python3 scripts/run_queries.py > /dev/null
python3 scripts/validate.py > /dev/null && echo "validation: ALL CHECKS PASSED (see docs/validation_report.md)"
python3 scripts/build_excel_report.py
echo "done. CSVs for Power BI/Tableau are in exports/"
