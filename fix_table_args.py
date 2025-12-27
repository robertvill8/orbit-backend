"""
Fix __table_args__ ordering: schema dict must be last element in tuple.
"""
import re
from pathlib import Path

def fix_table_args_in_file(filepath):
    """Fix __table_args__ ordering in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Pattern to find __table_args__ = (\n        {"schema": "..."},\n        ... other items ...
    # We need to move the schema dict to the end
    pattern = r'(__table_args__\s*=\s*\(\s*\n\s*)(\{"schema":\s*"[^"]+"\},\s*\n)((?:\s+[^\n]+\n)+)(\s*\))'

    def reorder(match):
        prefix = match.group(1)  # __table_args__ = (\n
        schema_dict = match.group(2).strip().rstrip(',')  # {"schema": "..."}
        other_items = match.group(3).rstrip()  # Other constraints/indexes
        suffix = match.group(4)  # )

        # Reconstruct with schema dict at the end
        return f"{prefix}{other_items},\n        {schema_dict},{suffix}"

    new_content = re.sub(pattern, reorder, content)

    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

# Fix all model files
models_dir = Path(__file__).parent / 'app' / 'models'
for py_file in models_dir.glob('*.py'):
    if py_file.name != '__init__.py':
        if fix_table_args_in_file(py_file):
            print(f"Fixed: {py_file.name}")
        else:
            print(f"No change: {py_file.name}")

print("Done!")
