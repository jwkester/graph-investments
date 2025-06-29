#!/usr/bin/env bash

# Check for exactly 3 arguments
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <csv_file> <sqlite_db> <table_name>"
  exit 1
fi

CSV_FILE="$1"
DB_FILE="$2"
TABLE_NAME="$3"

# Check if CSV file exists
if [ ! -f "$CSV_FILE" ]; then
  echo "Error: CSV file '$CSV_FILE' does not exist."
  exit 1
fi

# Check if SQLite DB file exists and prompt for deletion
if [ -f "$DB_FILE" ]; then
  read -p "The database file '$DB_FILE' already exists. Delete and recreate it? (y/n) " choice
  case "$choice" in
    y|Y )
      echo "Deleting '$DB_FILE'..."
      rm "$DB_FILE"
      ;;
    n|N )
      echo "Keeping '$DB_FILE'. Aborting to avoid overwriting."
      exit 1
      ;;
    * )
      echo "Invalid response. Aborting."
      exit 1
      ;;
  esac
fi

# Change to the directory containing the CSV
CSV_DIR=$(dirname "$CSV_FILE")
CSV_NAME=$(basename "$CSV_FILE")

cd "$CSV_DIR" || exit 1

# Run the SQLite import
sqlite3 "$DB_FILE" <<EOF
.mode csv
.import "$CSV_NAME" "$TABLE_NAME"
EOF

echo "Imported '$CSV_NAME' into table '$TABLE_NAME' in database '$DB_FILE'"
