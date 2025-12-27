"""
Fix remaining schema dict issues in model files.
"""
import re
from pathlib import Path

def fix_file(filepath):
    """Fix a single model file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Fix malformed Column definitions with schema dict
    # Pattern: Column(..., {"schema": "xxx"},    )
    pattern = r'Column\(([^\)]+), default=datetime\.utcnow, nullable=False,\s*\{"schema": "[^"]+"\},\s*\)'
    new_pattern = r'Column(\1, default=datetime.utcnow, nullable=False\n    )'
    content = re.sub(pattern, new_pattern, content)

    # Alternative pattern without default
    pattern2 = r'Column\(([^\)]+),\s*\{"schema": "[^"]+"\},\s*\)'
    new_pattern2 = r'Column(\1\n    )'
    content = re.sub(pattern2, new_pattern2, content)

    with open(filepath, 'w') as f:
        f.write(content)

# Files that need fixing based on grep output
files_to_fix = [
    'calendar.py',
    'document.py',
    'email.py',
    'integration.py',
    'notification.py',
    'relationship.py',
    'task.py',
]

models_dir = Path('/Users/robertvill/voice2task/backend/app/models')
for filename in files_to_fix:
    filepath = models_dir / filename
    if filepath.exists():
        fix_file(filepath)
        print(f"Fixed: {filename}")

print("Done!")
