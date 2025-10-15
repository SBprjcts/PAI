#!/usr/bin/env bash
set -euo pipefail

run_frontend() {
  start bash -c "cd /c/Users/alafs/Desktop/PAI/Frontend; ng serve; exec bash"
}

run_backend() {
  start bash -c "cd /c/Users/alafs/Desktop/PAI/Backend; source venv/Scripts/activate; python app.py; exec bash"
}

# No args → run both
if [[ $# -eq 0 ]]; then
  echo "[info] No flags provided; running both frontend and backend."
  run_frontend
  run_backend
  exit 0
fi

# -i f|b → run independently
if [[ "$1" == "-i" ]]; then
  ftr="${2:-}"
  case "$ftr" in
    f)
      echo "[info] Independent run flag provided; frontend argument; running frontend."
      run_frontend
      ;;
    b)
      echo "[info] Independent run flag provided; backend argument; running backend."
      run_backend
      ;;
    *)
      echo "Usage: $0 [-i f|b]"
      echo "  -i f   Run frontend only"
      echo "  -i b   Run backend only"
      exit 2
      ;;
  esac
  exit 0
fi

echo "Unknown option: $1"
echo "Usage: $0 [-i f|b]"
exit 2
