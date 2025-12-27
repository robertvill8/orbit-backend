"""
Remove malformed schema dicts from function calls (not __table_args__).
"""
import re
from pathlib import Path

# Read the grep output to find problematic lines
problematic_files = {
    'document.py': [149],
    'email.py': [171],
    'integration.py': [45],
    'notification.py': [76],
    'relationship.py': [110],
    'task.py': [198],
}

models_dir = Path('/Users/robertvill/voice2task/backend/app/models')

for filename, line_numbers in problematic_files.items():
    filepath = models_dir / filename
    with open(filepath, 'r') as f:
        lines = f.readlines()

    fixed = False
    for line_num in line_numbers:
        idx = line_num - 1  # Convert to 0-indexed
        if idx < len(lines):
            line = lines[idx]
            # Remove schema dict from this line
            if '{"schema"' in line and ')' in line:
                # Replace the entire malformed ending
                new_line = re.sub(r',?\s*\{"schema": "[^"]+"\},?\s*\)', ')', line)
                if new_line != line:
                    lines[idx] = new_line
                    fixed = True
                    print(f"Fixed {filename} line {line_num}: {line.strip()} -> {new_line.strip()}")

    if fixed:
        with open(filepath, 'w') as f:
            f.writelines(lines)

print("Done!")
