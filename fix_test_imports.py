#!/usr/bin/env python3
"""Fix incorrect sparkjar_crew imports in test files."""

import os
import re

def fix_imports_in_file(filepath):
    """Fix imports in a single file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace sparkjar_crew imports with local imports
    replacements = [
        # Schema imports - these don't exist, tests should define their own or skip
        (r'from sparkjar_crew\.shared\.schemas\.memory_schemas import.*', 
         '# TODO: Fix import - schemas should be defined locally\n# from sparkjar_crew.shared.schemas.memory_schemas import ...'),
        
        (r'from sparkjar_crew\.shared\.schemas\.thinking_schemas import.*', 
         '# TODO: Fix import - schemas should be defined locally\n# from sparkjar_crew.shared.schemas.thinking_schemas import ...'),
        
        # Database imports
        (r'from sparkjar_crew\.shared\.database\.connection import.*', 
         '# TODO: Fix import - use local database connection\n# from database import get_db'),
        
        (r'from sparkjar_crew\.shared\.database\.models import.*', 
         '# TODO: Fix import - use local models\n# from database.models import ...'),
        
        # Service imports
        (r'from sparkjar_crew\.shared\.services\.schema_validator import.*', 
         '# TODO: Fix import - validator should be local\n# from services.schema_validator import ...'),
        
        (r'from sparkjar_crew\.services\.memory_service\.mcp_server import.*', 
         '# TODO: Fix import - MCP server should be local\n# from mcp_server import ...'),
        
        # General sparkjar_crew imports
        (r'import sparkjar_crew.*', 
         '# TODO: Fix import - sparkjar_crew package does not exist in this repo'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed imports in: {filepath}")
        return True
    return False

def main():
    """Fix all test imports."""
    test_dir = "tests"
    fixed_count = 0
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_imports_in_file(filepath):
                    fixed_count += 1
    
    print(f"\nFixed imports in {fixed_count} files")
    print("\nNOTE: The fixed files now have TODO comments where imports need to be updated.")
    print("The memory service should not depend on sparkjar_crew package.")

if __name__ == "__main__":
    main()