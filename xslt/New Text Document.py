import os
import re

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "out")

def polish_dita_files():
    print("Starting Final DITA Polisher: Sweeping whitespaces and formatting issues...")
    
    files_modified = 0
    
    for root_dir, _, files in os.walk(os.path.join(BASE_DIR, "dita")):
        for file in files:
            if not file.endswith('.dita'):
                continue
                
            filepath = os.path.join(root_dir, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            content = original_content

            # --- Rule 1: Trailing spaces before closing tags ---
            # Example: "the system. </p>" -> "the system.</p>"
            content = re.sub(r'([^\s>])\s+</', r'\1</', content)

            # --- Rule 2: Leading spaces right after opening tags ---
            # Example: "<entry>\n  Moisture" -> "<entry>Moisture"
            content = re.sub(r'>\s+([^\s<])', r'>\1', content)

            # --- Rule 3: Snap opening inline tags to block tags (The <li>\n <b> issue) ---
            # Example: "<li>\n    <b>" -> "<li><b>"
            content = re.sub(r'<(p|li|entry|note|title)([^>]*)>\s+<', r'<\1\2><', content)

            # --- Rule 4: Snap closing inline tags to closing block tags ---
            # Example: "</b>\n  </li>" -> "</b></li>"
            content = re.sub(r'>\s+</(p|li|entry|note|title)>', r'></\1>', content)

            # --- Rule 5: Remove completely empty tags safely (Multiple passes for nested tags) ---
            # Example: "<p> </p>" or "<li><b></b></li>" -> ""
            previous_content = ""
            while previous_content != content:
                previous_content = content
                content = re.sub(r'<(p|li|entry|b|i|u|note|section|div|title)[^>]*>\s*</\1>', '', content)

            # --- Rule 6: Eradicate large structural gaps (Multiple blank lines) ---
            # Converts vertical blank space between tags into a single clean newline
            content = re.sub(r'\n[ \t]*\n', '\n', content)

            # Write back only if changes were made
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                files_modified += 1

    print(f"Polishing complete! Fixed formatting in {files_modified} files.")

if __name__ == "__main__":
    polish_dita_files()