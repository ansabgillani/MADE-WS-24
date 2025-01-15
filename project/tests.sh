#!/bin/bash

set -e  # Exit immediately on error

echo "Running pipeline.sh..."
ls
bash ./project/pipeline.sh

DB_FILE="./data/charging_station.db"
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file '$DB_FILE' not found!"
    exit 1
fi
echo "Found database file: $DB_FILE"

TABLE_EXISTS=$(sqlite3 "$DB_FILE" \
    "SELECT name FROM sqlite_master WHERE type='table' AND name='charging_stations';")

if [ "$TABLE_EXISTS" != "charging_stations" ]; then
    echo "Error: Table 'charging_stations' does not exist in '$DB_FILE'."
    exit 1
fi
echo "Table 'charging_stations' exists."

ROW_COUNT=$(sqlite3 "$DB_FILE" "SELECT COUNT(*) FROM charging_stations;")
if [ "$ROW_COUNT" -ne 50 ]; then
    echo "Error: Expected 50 rows in 'charging_stations', found $ROW_COUNT."
    exit 1
fi
echo "Table 'charging_stations' has 50 rows."

TABLE_INFO=$(sqlite3 "$DB_FILE" "PRAGMA table_info(charging_stations);")
# This returns rows like:
# 0|state_name|TEXT|0||0
# 1|count_of_ev_charging_stations|INTEGER|0||0

NUM_COLS=$(echo "$TABLE_INFO" | wc -l)
if [ "$NUM_COLS" -ne 2 ]; then
    echo "Error: Expected 2 columns in 'charging_stations', found $NUM_COLS."
    exit 1
fi

COL1_NAME=$(echo "$TABLE_INFO" | sed -n '1p' | cut -d'|' -f2)
COL2_NAME=$(echo "$TABLE_INFO" | sed -n '2p' | cut -d'|' -f2)

if [ "$COL1_NAME" != "state_name" ] || [ "$COL2_NAME" != "count_of_ev_charging_stations" ]; then
    echo "Error: Columns do not match expected names."
    echo "Found columns: $COL1_NAME, $COL2_NAME"
    exit 1
fi

echo "Columns match expected names: state_name, count_of_ev_charging_stations."

echo "All checks passed successfully!"
