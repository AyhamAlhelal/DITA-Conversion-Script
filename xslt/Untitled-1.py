import xml.etree.ElementTree as ET
import os
import re

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
# Based on your file tree, the map is located inside out/dita
BASE_DIR = os.path.join(PROJECT_ROOT, "out", "dita") 
MAP_FILE = os.path.join(BASE_DIR, "book.ditamap")
KEYS_MAP_FILE = os.path.join(BASE_DIR, "keys.ditamap")

def inject_keys_to_map():
    """Original function: Add keys for chapters inside book.ditamap"""
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


def harvest_nested_keys_and_update_dita():
    """New function: Harvest nested links, generate keys.ditamap, and update DITA files"""
    print("\nScanning DITA files for complex nested links...")
    nested_keys = {}
    modified_files_count = 0

    # Scan all DITA files in the project
    for root_dir, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.dita'):
                filepath = os.path.join(root_dir, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content
                
                # Search for nested links (containing # followed by a path with /)
                matches = re.finditer(r'<xref[^>]*?href\s*=\s*"([^"]+#[^"/]+/[^"]+)"', content)

                for match in matches:
                    full_href = match.group(1)
                    xref_tag = match.group(0)
                    
                    # Extract the last ID to use as the key
                    nested_id = full_href.split('/')[-1]
                    # Add a prefix to prevent name collisions
                    key_name = f"nested_{nested_id}"

                    # Calculate the correct relative path from keys.ditamap to the target file
                    current_file_dir = os.path.dirname(filepath)
                    target_file_part = full_href.split('#')[0]
                    anchor_part = full_href.split('#')[1]
                    
                    abs_target_path = os.path.normpath(os.path.join(current_file_dir, target_file_part))
                    rel_path_to_base = os.path.relpath(abs_target_path, BASE_DIR).replace('\\', '/')
                    
                    final_href_for_keymap = f"{rel_path_to_base}#{anchor_part}"
                    nested_keys[key_name] = final_href_for_keymap

                    # Replace the complex href with keyref inside the DITA file
                    new_xref_tag = re.sub(r'href\s*=\s*"[^"]+"', f'keyref="{key_name}"', xref_tag)
                    content = content.replace(xref_tag, new_xref_tag)

                # Save changes if links were found
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    modified_files_count += 1

    print(f"Updated {modified_files_count} DITA files with clean nested keyrefs.")

    # Create keys.ditamap file matching company standards
    if nested_keys:
        print("Generating keys.ditamap...")
        keys_content = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<?xml-model href="urn:oasis:names:tc:dita:rng:map.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>',
            '<map>',
            '    <title>Centralized Nested Keys</title>',
            '    <topicgroup processing-role="resource-only">'
        ]
        
        for key, href in nested_keys.items():
            keys_content.append(f'        <keydef keys="{key}" href="{href}"/>')
            
        keys_content.extend(['    </topicgroup>', '</map>'])

        with open(KEYS_MAP_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(keys_content))
        print(f"Success: Created keys.ditamap with {len(nested_keys)} targeted keys.")
    else:
        print("No nested links found. keys.ditamap creation skipped.")


def link_keys_map_to_bookmap():
    """Inject the reference line into the main map"""
    if not os.path.exists(KEYS_MAP_FILE):
        return

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if it is already linked
    if 'href="keys.ditamap"' in content:
        print("keys.ditamap is already linked in book.ditamap.")
        return

    # Inject the link directly after the <bookmap> or <map> tag
    match = re.search(r'<bookmap[^>]*>|<map[^>]*>', content)
    if match:
        root_tag = match.group(0)
        mapref_element = '\n    <!-- Centralized Keys -->\n    <mapref href="keys.ditamap" format="ditamap" processing-role="resource-only"/>'
        new_content = content.replace(root_tag, root_tag + mapref_element, 1)
        
        with open(MAP_FILE, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success: Linked keys.ditamap to book.ditamap.")


if __name__ == "__main__":
    print("--- Starting DITA Map & Key Architect ---")
    inject_keys_to_map()
    harvest_nested_keys_and_update_dita()
    link_keys_map_to_bookmap()
    print("--- Process Completed ---")