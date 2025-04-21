#!/usr/bin/env python3

import os
import sys
import fnmatch
from pathlib import Path

def read_repoignore(directory):
    """Read .repoignore file if it exists and return list of patterns to ignore"""
    default_ignores = [
        'node_modules',
        'vendor',
        '.vscode',
        'bootstrap/cache',
        'storage',
        'public/vendor',
        'public/.htaccess',
        'public/favicon.ico',
        'public/hot',
        'public/robots.txt',
        'database/data',
        'tests',
        '.env',
        '.git',
        'repo_contents.py',
        'repository_contents.txt',
        'artisan',
        'package-lock.json',
        'composer.lock',
        'phpunit.xml',
        'strategy_results',
        'trailing_stop_analysis',
        '50k.csv'
    ]
    
    ignore_file = os.path.join(directory, '.repoignore')
    ignore_patterns = default_ignores.copy()
    
    if os.path.exists(ignore_file):
        with open(ignore_file, 'r') as f:
            # Add custom patterns from .repoignore, strip whitespace
            custom_patterns = [line.strip() for line in f.readlines() if line.strip()]
            ignore_patterns.extend(custom_patterns)
    
    return ignore_patterns

def should_ignore(path, base_dir, ignore_patterns):
    """Check if path should be ignored based on ignore patterns"""
    # Convert path to relative path from base directory
    rel_path = os.path.relpath(path, base_dir)
    
    for pattern in ignore_patterns:
        # Use glob-style pattern matching
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True
            
        # Also check if any parent directory matches the pattern
        parts = Path(rel_path).parts
        for i in range(len(parts)):
            partial_path = os.path.join(*parts[:i+1])
            if fnmatch.fnmatch(partial_path, pattern):
                return True
    
    return False

def is_likely_binary(file_path, sample_size=8192):
    """
    Check if a file is likely binary by reading a sample of bytes
    and checking for null bytes or high percentage of non-text characters
    """
    try:
        with open(file_path, 'rb') as f:
            sample = f.read(sample_size)
            
        # If there are null bytes, it's likely binary
        if b'\x00' in sample:
            return True
            
        # Count control characters (except common ones like newline, tab)
        control_chars = sum(1 for c in sample if c < 32 and c not in (9, 10, 13))
        
        # If more than 10% are control characters, likely binary
        if control_chars / len(sample) > 0.1:
            return True
            
        return False
    except Exception:
        # If we can't read the file, consider it binary
        return True

def process_directory(directory, output_file, ignore_patterns):
    """Recursively process directory and write contents to output file"""
    try:
        directory_path = Path(directory)
        output_path = Path(output_file.name)
        
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not should_ignore(root_path / d, directory, ignore_patterns)]
            
            for file in files:
                file_path = root_path / file
                
                # Skip the output file itself
                if file_path.resolve() == output_path.resolve():
                    continue
                    
                # Skip ignored files
                if should_ignore(file_path, directory, ignore_patterns):
                    continue
                
                # Skip binary files
                if is_likely_binary(file_path):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Write the file path and contents to output
                        rel_path = os.path.relpath(file_path, directory)
                        output_file.write(f"File: {rel_path}\n")
                        output_file.write(f"{'=' * (len(rel_path) + 6)}\n")  # Add separator
                        output_file.write(content)
                        
                        # Ensure there's a proper separator between files
                        if not content.endswith('\n'):
                            output_file.write('\n')
                        output_file.write('\n')
                except (UnicodeDecodeError, IOError) as e:
                    # Log skipped files
                    output_file.write(f"File: {os.path.relpath(file_path, directory)} (Skipped: {str(e)[:100]})\n\n")
                    continue

    except Exception as e:
        print(f"Error processing directory: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python repo_contents.py <directory_path>", file=sys.stderr)
        sys.exit(1)
    
    directory = os.path.abspath(sys.argv[1])
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory", file=sys.stderr)
        sys.exit(1)
    
    output_filename = "repository_contents.txt"
    output_path = os.path.join(directory, output_filename)
    
    # Get ignore patterns
    ignore_patterns = read_repoignore(directory)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as output_file:
            # Write header information
            output_file.write(f"Repository Contents\n")
            output_file.write(f"==================\n")
            output_file.write(f"Directory: {directory}\n")
            output_file.write(f"Generated on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            process_directory(directory, output_file, ignore_patterns)
        print(f"Successfully created {output_path}")
    except Exception as e:
        print(f"Error creating output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()