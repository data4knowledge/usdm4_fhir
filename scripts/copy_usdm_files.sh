#!/bin/bash

SOURCE_DIR="/Users/daveih/Documents/github/usdm4_m11/tests/usdm4_m11/test_files/m11"
DEST_DIR="$(dirname "$0")/../tests/usdm4_fhir/test_files/m11/export/prism3"

FILES=(
  "ASP8062/ASP8062_usdm.json"
  "TCBCPT_01/TCBCPT_01_usdm.json"
  "TCBCPT_02/TCBCPT_02_usdm.json"
  "TCBCPT_03/TCBCPT_03_usdm.json"
  "WA42380/WA42380_usdm.json"
)

for file in "${FILES[@]}"; do
  src="$SOURCE_DIR/$file"
  if [ -f "$src" ]; then
    cp "$src" "$DEST_DIR/"
    echo "Copied: $file"
  else
    echo "Not found: $src"
  fi
done

# Replace "id": "FAKE" with a valid UUID in each copied file
echo ""
echo "Replacing FAKE UUIDs..."
for dest_file in "$DEST_DIR"/*_usdm.json; do
  if [ -f "$dest_file" ]; then
    uuid=$(uuidgen | tr '[:upper:]' '[:lower:]')
    sed -i '' "s/\"id\": \"FAKE\"/\"id\": \"$uuid\"/" "$dest_file"
    echo "Updated $(basename "$dest_file") with UUID: $uuid"
  fi
done
