"""
Verify and fix all __table_args__ in model files.
"""
import re
from pathlib import Path

def fix_table_args(content):
    """
    Fix __table_args__ to ensure schema dict is LAST in the tuple.
    """
    # Pattern to match __table_args__ = ( ... )
    pattern = r'(__table_args__\s*=\s*\(\s*)(.*?)(\s*\))'

    def reorder_args(match):
        prefix = match.group(1)
        args_content = match.group(2)
        suffix = match.group(3)

        # Split by lines and process
        lines = args_content.strip().split('\n')
        schema_line = None
        other_lines = []

        for line in lines:
            stripped = line.strip()
            if '{"schema"' in stripped:
                schema_line = stripped.rstrip(',')
            elif stripped and stripped != ',':
                other_lines.append(line.rstrip().rstrip(','))

        if not schema_line:
            # No schema dict found, return as-is
            return match.group(0)

        # Rebuild with schema dict at the end
        if other_lines:
            result = prefix + '\n' + ',\n'.join(other_lines) + ',\n        ' + schema_line + ',' + suffix
        else:
            result = prefix + schema_line + ',' + suffix

        return result

    new_content = re.sub(pattern, reorder_args, content, flags=re.DOTALL)
    return new_content

models_dir = Path('/Users/robertvill/voice2task/backend/app/models')

for py_file in models_dir.glob('*.py'):
    if py_file.name == '__init__.py':
        continue

    with open(py_file, 'r') as f:
        content = f.read()

    new_content = fix_table_args(content)

    if new_content != content:
        with open(py_file, 'w') as f:
            f.write(new_content)
        print(f"Fixed: {py_file.name}")
    else:
        print(f"OK: {py_file.name}")

print("\nDone!")
