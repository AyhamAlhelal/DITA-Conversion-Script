import os
import re

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")

def clean_name(name):
    """Replace spaces and dashes with underscores."""
    return name.replace(' ', '_').replace('-', '_')

def sanitize_file_system():
    """Rename files and directories on disk inside out/ to remove spaces and dashes."""
    print(f"--- Phase 1: Renaming physical files and directories in out/ ---")
    
    if not os.path.exists(OUT_DIR):
        print(f"Error: Directory {OUT_DIR} not found.")
        return

    renamed_files_count = 0
    renamed_dirs_count = 0

    # topdown=False ensures we rename children files before their parent directories
    for root, dirs, files in os.walk(OUT_DIR, topdown=False):
        # 1. Rename files (dita, ditamap, images, etc.)
        for filename in files:
            new_filename = clean_name(filename)
            if new_filename != filename:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                os.rename(old_path, new_path)
                renamed_files_count += 1
                print(f"Renamed File: '{filename}' -> '{new_filename}'")
        
        # 2. Rename directories (e.g., chapter-01 -> chapter_01)
        for dirname in dirs:
            new_dirname = clean_name(dirname)
            if new_dirname != dirname:
                old_path = os.path.join(root, dirname)
                new_path = os.path.join(root, new_dirname)
                os.rename(old_path, new_path)
                renamed_dirs_count += 1
                print(f"Renamed Directory: '{dirname}' -> '{new_dirname}'")
                
    print(f"Phase 1 Complete: Renamed {renamed_files_count} files and {renamed_dirs_count} directories.")

def update_internal_links():
    """Scan all .dita and .ditamap files in out/ to update href attributes to match new filenames."""
    print("\n--- Phase 2: Updating href links inside .dita and .ditamap files ---")
    modified_files = 0
    
    for root, dirs, files in os.walk(OUT_DIR):
        for filename in files:
            if filename.endswith('.dita') or filename.endswith('.ditamap'):
                filepath = os.path.join(root, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                def href_replacer(match):
                    full_href = match.group(1)
                    
                    # Rule: Exclude Web links, emails, RNG schema links, and purely internal anchors
                    if (full_href.startswith('http') or 
                        full_href.startswith('www') or 
                        full_href.startswith('mailto:') or 
                        full_href.startswith('urn:') or 
                        full_href.startswith('com:') or 
                        full_href.startswith('#')):
                        return f'href="{full_href}"'
                    
                    # Split anchor (#) to ONLY clean the file path part (protecting internal IDs)
                    parts = full_href.split('#')
                    file_part = parts[0]
                    
                    if file_part:
                        # Apply the exact same cleaning rule as the file system
                        file_part = clean_name(file_part)
                    
                    # Reassemble href securely
                    if len(parts) > 1:
                        new_href = f"{file_part}#{parts[1]}"
                    else:
                        new_href = file_part
                        
                    return f'href="{new_href}"'
                
                # Regex to find and replace all href="..." attributes
                content = re.sub(r'href\s*=\s*"([^"]+)"', href_replacer, content)
                
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    modified_files += 1

    print(f"Phase 2 Complete: Updated links in {modified_files} files.")

if __name__ == "__main__":
    print("--- Starting Filename & Link Sanitizer ---")
    sanitize_file_system()
    update_internal_links()
    print("--- Process Completed ---")