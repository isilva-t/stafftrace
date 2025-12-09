#!/bin/bash

# Script to concatenate 'backend' folder files for code review/sharing

OUTPUT_FILE="zz_backend.txt"

# Clear the output file if it exists
> "$OUTPUT_FILE"

# Ignore patterns for Spring Boot project
IGNORE_PATTERNS=(
	'!frontend/'
    '!target/**'                # Exclude Maven build output
    '!.mvn/**'                  # Exclude Maven wrapper internals
    '!__pycache__/**'
    '!*.class'                  # Exclude compiled Java
    '!*.jar'
    '!*.war'
    '!venv/**'
    '!env/**'
    '!.git/**'
    '!*.log'
    '!*.png'
    '!*.jpg'
    '!.DS_Store'
    "!$OUTPUT_FILE"             # Don't output the output file itself
    '!y*'                  # Don't output this script
	'!zz*'
    '!HELP.md'                  # Skip Spring Boot help file
    '!mvnw'                     # Skip Maven wrapper scripts
    '!mvnw.cmd'
)

GLOB_ARGS=""
for pattern in "${IGNORE_PATTERNS[@]}"; do
    GLOB_ARGS="$GLOB_ARGS --glob '$pattern'"
done

echo "Generating context from 'backend' directory..."

# 1. Run the main search (ripgrep)
eval "rg . --line-number --heading $GLOB_ARGS > \"$OUTPUT_FILE\"" &
search_pid=$!

# Wait for ripgrep to finish
wait $search_pid

# 2. Create a sorted file list summary
eval "rg . --files $GLOB_ARGS" > /tmp/backend_files_list.txt

if [ -s /tmp/backend_files_list.txt ]; then
    tmp_output=$(mktemp)
    while read -r file; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file")
            printf "%4d %s\n" "$lines" "$file"
        fi
    done < /tmp/backend_files_list.txt > "$tmp_output"

    echo ""
    echo "Files sorted by line count (ascending):"
    echo "--------------------------------------"
    sort -n "$tmp_output"
    echo "--------------------------------------"

    rm -f "$tmp_output"
fi

rm -f /tmp/backend_files_list.txt

# 3. Append .env explicitly if it exists
if [ -f ".env" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "///// END OF OTHER FILES, \".env\" file is next" >> "$OUTPUT_FILE"
    echo ".env" >> "$OUTPUT_FILE"
    cat ".env" >> "$OUTPUT_FILE"
fi

# 4. Final Summary
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
FILE_COUNT=$(eval "rg --files $GLOB_ARGS | wc -l")

echo ""
echo "Done."
echo "Files processed: $FILE_COUNT"
echo "Total lines in $OUTPUT_FILE: $LINE_COUNT"
