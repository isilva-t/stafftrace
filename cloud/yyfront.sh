#!/bin/bash

# Script to concatenate 'frontend' folder files for code review/sharing

OUTPUT_FILE="zz_frontend.txt"

# Clear the output file if it exists
> "$OUTPUT_FILE"

# Ignore patterns for Angular project
IGNORE_PATTERNS=(
    '!node_modules/**'          # Exclude npm packages
    '!dist/**'                  # Exclude build output
    '!.angular/**'              # Exclude Angular cache
    '!coverage/**'              # Exclude test coverage
    '!__pycache__/**'
	'!backend/'
    '!*.log'
    '!*.png'
    '!*.jpg'
    '!*.ico'                    # Exclude favicon
    '!*.svg'                    # Exclude SVG files
    '!.DS_Store'
	'!zz*'
    "!$OUTPUT_FILE"             # Don't output the output file itself
	'!y*'
	'!docker-compose.yml'
    '!package-lock.json'        # Skip lock file (too large)
    '!*.spec.ts'                # Skip test files
)

GLOB_ARGS=""
for pattern in "${IGNORE_PATTERNS[@]}"; do
    GLOB_ARGS="$GLOB_ARGS --glob '$pattern'"
done

echo "Generating context from 'frontend' directory..."

# 1. Run the main search (ripgrep)
eval "rg . --line-number --heading $GLOB_ARGS > \"$OUTPUT_FILE\"" &
search_pid=$!

# Wait for ripgrep to finish
wait $search_pid

# 2. Create a sorted file list summary
eval "rg . --files $GLOB_ARGS" > /tmp/frontend_files_list.txt

if [ -s /tmp/frontend_files_list.txt ]; then
    tmp_output=$(mktemp)
    while read -r file; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file")
            printf "%4d %s\n" "$lines" "$file"
        fi
    done < /tmp/frontend_files_list.txt > "$tmp_output"

    echo ""
    echo "Files sorted by line count (ascending):"
    echo "--------------------------------------"
    sort -n "$tmp_output"
    echo "--------------------------------------"

    rm -f "$tmp_output"
fi

rm -f /tmp/frontend_files_list.txt

# 3. Final Summary
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
FILE_COUNT=$(eval "rg --files $GLOB_ARGS | wc -l")

echo ""
echo "Done."
echo "Files processed: $FILE_COUNT"
echo "Total lines in $OUTPUT_FILE: $LINE_COUNT"
