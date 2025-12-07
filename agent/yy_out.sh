#!/bin/bash

# Script to concatenate 'agent' folder files for code review/sharing

OUTPUT_FILE="zz_agent.txt"

# Clear the output file if it exists
> "$OUTPUT_FILE"

# Custom Ignore patterns based on your 'agent' folder content
IGNORE_PATTERNS=(
    '!celerybeat-schedule'      # Exclude celery binary schedule file
    '!__pycache__/**'           # Exclude python cache
    '!*.pyc'                    # Exclude compiled python
    '!*.sqlite3'
    '!*.db'
    '!data/**'                  # Exclude data folder mentioned in .gitignore
    '!venv/**'
    '!env/**'
    '!.git/**'
    '!*.log'
    '!*.png'
    '!*.jpg'
    '!*.DS_Store'
    "!$OUTPUT_FILE"             # Don't output the output file itself
    '!*out.sh'                  # Don't output this script
)

GLOB_ARGS=""
for pattern in "${IGNORE_PATTERNS[@]}"; do
    GLOB_ARGS="$GLOB_ARGS --glob '$pattern'"
done

echo "Genereting context from 'agent' directory..."

# 1. Run the main search (ripgrep)
# We use eval to handle the dynamic GLOB_ARGS correctly
eval "rg . --line-number --heading $GLOB_ARGS > \"$OUTPUT_FILE\"" &
search_pid=$!

# Wait for ripgrep to finish
wait $search_pid

# 2. Create a sorted file list summary
# This helps you see which files are largest
eval "rg . --files $GLOB_ARGS" > /tmp/agent_files_list.txt

if [ -s /tmp/agent_files_list.txt ]; then
    tmp_output=$(mktemp)
    while read -r file; do
        if [ -f "$file" ]; then
            lines=$(wc -l < "$file")
            printf "%4d %s\n" "$lines" "$file"
        fi
    done < /tmp/agent_files_list.txt > "$tmp_output"

    echo ""
    echo "Files sorted by line count (ascending):"
    echo "--------------------------------------"
    sort -n "$tmp_output"
    echo "--------------------------------------"

    rm -f "$tmp_output"
fi

rm -f /tmp/agent_files_list.txt

# 3. Append .env explicitly if it exists (handling secrets carefully)
if [ -f ".env" ]; then
    echo "" >> "$OUTPUT_FILE"
    echo "///// END OF OTHER FILES, \".env\" file is next" >> "$OUTPUT_FILE"
    echo ".env" >> "$OUTPUT_FILE"
    cat ".env" >> "$OUTPUT_FILE"
fi

# 4. Final Summary
LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
# Recalculate file count excluding ignores
FILE_COUNT=$(eval "rg --files $GLOB_ARGS | wc -l")

echo ""
echo "Done."
echo "Files processed: $FILE_COUNT"
echo "Total lines in $OUTPUT_FILE: $LINE_COUNT"
