#!/usr/bin/env python3
"""
Temporary fix for PsyNet Unicode error during deployment.
This script patches the PsyNet utils.py file to handle Unicode errors gracefully.
"""

import os
import sys

def patch_psynet_utils():
    """Patch the PsyNet utils.py file to handle Unicode errors in TODO checking."""
    
    # Find the PsyNet utils.py file
    psynet_utils_path = None
    
    # Look in the virtual environment
    for root, dirs, files in os.walk('.'):
        if 'psynet' in dirs and 'utils.py' in files:
            psynet_utils_path = os.path.join(root, 'psynet', 'utils.py')
            break
    
    if not psynet_utils_path:
        print("Could not find PsyNet utils.py file")
        return False
    
    print(f"Found PsyNet utils.py at: {psynet_utils_path}")
    
    # Read the current file
    with open(psynet_utils_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic line and replace it
    old_line = "line_has_todo = [line.strip().startswith(pattern) for line in f.readlines()]"
    new_line = """try:
            line_has_todo = [line.strip().startswith(pattern) for line in f.readlines()]
        except UnicodeDecodeError:
            # Skip files that can't be decoded as UTF-8 (binary files, etc.)
            line_has_todo = []"""
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Write the patched file
        with open(psynet_utils_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("Successfully patched PsyNet utils.py to handle Unicode errors")
        return True
    else:
        print("Could not find the target line to patch")
        return False

if __name__ == "__main__":
    if patch_psynet_utils():
        print("Patch applied successfully. You can now try deploying again.")
    else:
        print("Failed to apply patch.")
        sys.exit(1)

