#!/bin/bash

# Create a temporary file for unsorted results
temp_file=$(mktemp)

# Find all .py files, excluding those in venv directories
# Count lines in each file and append to the temporary file
find . -name "*.py" -not -path "*/venv/*" -not -path "*/.venv/*" | while read -r file; do
    # Get the line count
    lines=$(wc -l < "$file")
    
    # Remove leading './' from file path if present
    file_path=${file#./}
    
    # Store the line count and file path in a format that's easy to sort
    # Format: line_count file_path
    echo "$lines $file_path" >> "$temp_file"
done

# Sort the results by line count (numerically, descending) and format the output
sort -nr "$temp_file" | awk '{print $2 " (" $1 " lines)"}' > line_count.txt

# Clean up the temporary file
rm "$temp_file"

echo "Line counts have been written to line_count.txt (sorted by line count in descending order)"