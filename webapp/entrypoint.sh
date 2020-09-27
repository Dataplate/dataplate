#!/bin/sh

db_upgrade() {
  flask db upgrade
}

run() {
  flask run -h 0.0.0.0
}

for cmd in "$@"; do
  case "$cmd" in
    db_upgrade|run)
      eval $1
      shift
      ;;
    *)
      echo "Unknown command: $cmd"
      exit 1
      ;;
  esac
done
