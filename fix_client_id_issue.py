#!/usr/bin/env python3
"""
Fix client_id redundancy in memory service.

IMPORTANT ARCHITECTURAL CHANGE:
- The client_id field is redundant and should be removed
- When actor_type = "client", the actor_id contains the client ID
- This simplifies the API and removes confusion

Example:
    actor_type = "client"
    actor_id = "1d1c2154-242b-4f49-9ca8-e57129ddc823"  # This IS the client ID
"""

import os
import re

def fix_file(filepath):
    """Fix client_id references in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Skip if it's a database model or migration file
    if 'database/models.py' in filepath or 'alembic' in filepath:
        print(f"Skipping database file: {filepath}")
        return False
    
    # Replace client_id parameters with proper documentation
    replacements = [
        # In function parameters
        (r'(\s+)client_id:\s*(?:str|UUID),?\s*\n', 
         r'\1# client_id removed - use actor_id when actor_type="client"\n'),
        
        # In JSON/dict creation
        (r'"client_id":\s*[^,\n]+,?\s*\n', 
         '# "client_id" removed - use actor_id when actor_type="client"\n'),
        
        # In request data
        (r'request\.client_id', 
         'request.actor_id  # When actor_type="client", this is the client_id'),
        
        # In token data extraction
        (r'token_data\["client_id"\]', 
         'token_data["actor_id"]  # When actor_type="client", this is the client_id'),
        
        # In payload checks
        (r'"actor_type", "actor_id"  # client_id removed - redundant', 
         '"actor_type", "actor_id"  # client_id removed - redundant'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Add documentation at the top of files that use actor_type/actor_id
    if 'actor_type' in content and 'actor_id' in content and '# MEMORY SERVICE ARCHITECTURE' not in content:
        doc_header = '''# MEMORY SERVICE ARCHITECTURE NOTE:
# client_id field has been removed as it was redundant.
# When actor_type = "client", the actor_id IS the client ID.
# Example: actor_type="client", actor_id="1d1c2154-242b-4f49-9ca8-e57129ddc823"

'''
        content = doc_header + content
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    """Fix client_id issue in all Python files."""
    fixed_count = 0
    
    # Fix main service files
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and virtual environments
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and 'venv' not in d]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    print("\nIMPORTANT: The client_id field has been removed.")
    print("When actor_type='client', the actor_id contains the client ID.")
    print("\nTest case example:")
    print("  actor_type = 'client'")
    print("  actor_id = '1d1c2154-242b-4f49-9ca8-e57129ddc823'")

if __name__ == "__main__":
    main()