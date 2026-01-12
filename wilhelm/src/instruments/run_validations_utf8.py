"""
UTF-8 wrapper for validation runner
"""
import sys
import os
import io

# Force UTF-8 encoding for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Now run the main validation script
exec(open('run_disease_validations.py', encoding='utf-8').read())
