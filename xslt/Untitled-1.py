import xml.etree.ElementTree as ET
import os
import re

# --- Configuration Paths (Fixed & Static) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
DITA_DIR = os.path.join(OUT_DIR, "dita")
MAP_FILE = os.path.join(OUT_DIR, "book.ditamap")

def inject_keys_to_map():
    """Inject 'keys' attributes for main chapters inside book.ditamap"""
    print(f"Starting to process {MAP_FILE} to inject 'keys' attributes...")
    
    if not os.path.exists(MAP_FILE):
        print(f"Error: Map file not found at {MAP_FILE}")
        return

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        map_content = f.read()

    header_match = re.search(r'(.*?)<(bookmap|map)', map_content, re.DOTALL)
    original_header = header_match.group(1) if header_match else '<?xml version="1.0" encoding="UTF-8"?>\n'
    root_tag = header_match.group(2) if header_match else 'bookmap'

    tree = ET.parse(MAP_FILE)
    root = tree.getroot()
    modified_count = 0

    for elem in root.iter():
        href = elem.get('href')
        if href and href.endswith('.dita'):
            filename_with_ext = os.path.basename(href)
            key_name = os.path.splitext(filename_with_ext)[0]
            elem.set('keys', key_name)
            modified_count += 1

    xml_data = ET.tostring(root, encoding='utf-8').decode('utf-8')
    if f'<{root_tag}' in xml_data:
        final_map_xml = original_header + f'<{root_tag}' + xml_data.split(f'<{root_tag}')[1]
    else:
        final_map_xml = xml_data

    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(final_map_xml)
        
    print(f"Success! Injected 'keys' attribute into {modified_count} references.")


def convert_external_links_to_keyrefs():
    """Convert external DITA hrefs to standard keyrefs, ignoring internal anchors"""
    print("\nConverting external xref hrefs to direct standard DITA keyrefs...")
    modified_files_count = 0
    
    if not os.path.exists(DITA_DIR):
        print(f"Error: DITA directory not found at {DITA_DIR}")
        return

    for root_dir, dirs, files in os.walk(DITA_DIR):
        for file in files:
            if file.endswith('.dita'):
                filepath = os.path.join(root_dir, file)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                
                # Regex to find ALL <xref> tags that use href
                matches = re.finditer(r'<xref[^>]*?href\s*=\s*"([^"]+)"', content)

                for match in matches:
                    full_href = match.group(1)
                    xref_tag = match.group(0)
                    
                    # Skip normal web links
                    if full_href.startswith('http') or full_href.startswith('www'):
                        continue

                    # Skip internal links (pointing to elements within the same file)
                    if full_href.startswith('#'):
                        continue

                    new_keyref = ""

                    # --- External DITA Links (e.g. href="../chapter/file.dita#...") ---
                    if '.dita' in full_href:
                        file_part = full_href.split('#')[0]
                        key_name = os.path.splitext(os.path.basename(file_part))[0]
                        
                        if '#' in full_href:
                            anchor = full_href.split('#')[1]
                            if '/' in anchor:
                                topic_id, element_id = anchor.split('/', 1)
                                
                                # Intelligent cleanup: drop suffix if it points to the root topic
                                clean_key_name = re.sub(r'[^a-zA-Z]', '', key_name).lower()
                                clean_target = re.sub(r'[^a-zA-Z]', '', element_id).lower()
                                
                                if clean_key_name == clean_target or topic_id == element_id:
                                    new_keyref = key_name
                                else:
                                    new_keyref = f"{key_name}/{element_id}"
                            else:
                                # Standard topic link without deep nesting (file.dita#topic)
                                new_keyref = key_name
                        else:
                            # Direct file link (file.dita)
                            new_keyref = key_name

                    # Apply the transformation if a valid external keyref was constructed
                    if new_keyref:
                        new_xref_tag = re.sub(r'href\s*=\s*"[^"]+"', f'keyref="{new_keyref}"', xref_tag)
                        content = content.replace(xref_tag, new_xref_tag)

                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    modified_files_count += 1

    print(f"Processed and updated {modified_files_count} DITA files successfully.")


if __name__ == "__main__":
    print("--- Starting DITA Map & Key Architect ---")
    inject_keys_to_map()
    convert_external_links_to_keyrefs()
    print("--- Process Completed ---")