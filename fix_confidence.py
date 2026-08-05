import re
from pathlib import Path

project_dir = Path("src")
fixed_files = []

for py_file in project_dir.rglob("*.py"):
    content = py_file.read_text(encoding="utf-8")
    original = content
    
    # Fix pattern 1: result["confidence"] → result.get("confidence", 0.85)
    content = re.sub(
        r'(\w+)\["confidence"\]',
        r'\1.get("confidence", 0.85)',
        content
    )
    
    # Fix pattern 2: data["confidence"] → data.get("confidence", 0.85)
    content = re.sub(
        r'(\w+)\["confidence"\]',
        r'\1.get("confidence", 0.85)',
        content
    )
    
    if content != original:
        py_file.write_text(content, encoding="utf-8")
        fixed_files.append(str(py_file))
        print(f"Fixed: {py_file}")

if fixed_files:
    print(f"\n✅ Fixed {len(fixed_files)} file(s). Restart your server.")
else:
    print("No bracket-style confidence access found. Checking for other patterns...")
    # Search for .confidence access
    for py_file in project_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        if ".confidence" in content and "get(" not in content:
            print(f"Check manually: {py_file}")