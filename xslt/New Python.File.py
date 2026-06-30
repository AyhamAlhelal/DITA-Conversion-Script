import os
import re
import xml.etree.ElementTree as ET

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "out")
MAP_FILE = os.path.join(BASE_DIR, "book.ditamap")

# Global dictionary to track moved files for xref updates
# Format: {'old_file_path.dita': 'new_file_path.dita#parent_id/child_id'}
link_redirect_map = {}

def get_root_id(content):
    """Extracts the ID attribute from the root topic/section element."""
    match = re.search(r'<(topic|concept|task|reference|section)[^>]*\bid=["\']([^"\']+)["\']', content)
    return match.group(2) if match else None

def extract_and_transform_element(filepath, to_section=False):
    """
    Extracts the root XML element. If to_section is True, dynamically 
    transforms the root <topic> tags into <section> tags for leaf nodes.
    """
    if not os.path.exists(filepath):
        return "", None

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Isolate the main body, discarding XML headers and RNG models
    match = re.search(r'<(topic|concept|task|reference)\b(.*)</\1>\s*$', content, re.DOTALL)
    if not match:
        return "", None
        
    element_content = match.group(0)
    element_id = get_root_id(element_content)

    if to_section:
        # Transform root topic to section for leaf nodes
        element_content = re.sub(r'^<(topic|concept|task|reference)\b', '<section', element_content, count=1)
        element_content = re.sub(r'</(topic|concept|task|reference)>\s*$', '</section>', element_content, count=1)

    return element_content, element_id

def inject_content(parent_filepath, child_content, is_section):
    """
    Injects content into the parent file based on structural rules.
    Includes Self-Healing logic for missing, empty, or self-closing <body> tags.
    """
    if not child_content or not os.path.exists(parent_filepath):
        return

    with open(parent_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if is_section:
        # Edge Case 1: Expand self-closing XML tags like <body/> to <body></body>
        if re.search(r'<body\s*/>', content):
            content = re.sub(r'<body\s*/>', '<body>\n    </body>', content, count=1)
            
        # Edge Case 2: If parent lacks a body entirely, create one after </title>
        elif not re.search(r'</body>', content):
            content = re.sub(r'(</title>)', r'\1\n    <body>\n    </body>', content, count=1)
            
        # Target the closing tag for safe injection (handles whitespaces/comments inside naturally)
        target_tag = r'</body>'
        injection_wrapper = "\n\n    \n    "
    else:
        # Inject nested topics before the final closing </topic> tag
        target_tag = r'</(topic|concept|task|reference)>\s*$'
        injection_wrapper = "\n\n\n"

    match = re.search(target_tag, content)
    if match:
        insert_pos = match.start()
        new_content = content[:insert_pos] + injection_wrapper + child_content + "\n" + content[insert_pos:]
        with open(parent_filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def process_node(parent_elem, parent_filepath, parent_root_id):
    """
    Recursively processes map nodes. Decides between Section vs Topic 
    transformation based on whether the node has children (Leaf vs Parent).
    """
    for child_elem in list(parent_elem):
        if child_elem.tag == 'topicref':
            href = child_elem.get('href')
            
            # Ignore absolute URLs and non-DITA files
            if not href or href.startswith('http') or not href.endswith('.dita'):
                continue
                
            child_filepath = os.path.normpath(os.path.join(BASE_DIR, href))
            
            # Check if this node is a leaf (no nested topicrefs)
            has_children = len([e for e in child_elem if e.tag == 'topicref']) > 0
            is_leaf = not has_children

            # 1. Process deeper children first (Bottom-Up approach)
            if has_children:
                if os.path.exists(child_filepath):
                    with open(child_filepath, 'r', encoding='utf-8') as f:
                        child_id = get_root_id(f.read())
                    process_node(child_elem, child_filepath, child_id)

            # 2. Extract and transform current child
            child_content, child_id = extract_and_transform_element(child_filepath, to_section=is_leaf)
            
            if child_content:
                # 3. Inject into parent file
                inject_content(parent_filepath, child_content, is_section=is_leaf)
                
                # 4. Map the link redirection for xref updates later
                old_relative_path = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                new_relative_path = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                
                # DITA linking syntax: filename.dita#parent_id/child_id (for sections)
                if is_leaf and parent_root_id and child_id:
                    new_link = f"{new_relative_path}#{parent_root_id}/{child_id}"
                else:
                    new_link = f"{new_relative_path}#{child_id}" if child_id else new_relative_path
                    
                link_redirect_map[old_relative_path] = new_link

                # 5. Cleanup: Delete the absorbed file and remove from map
                if os.path.exists(child_filepath):
                    os.remove(child_filepath)
                parent_elem.remove(child_elem)

def update_global_xrefs():
    """
    Scans all remaining DITA files in the output directory and updates 
    any broken hrefs pointing to the deleted files using the redirect map.
    """
    print(f"Updating cross-references for {len(link_redirect_map)} merged files...")
    
    for root_dir, _, files in os.walk(os.path.join(BASE_DIR, "dita")):
        for file in files:
            if not file.endswith('.dita'):
                continue
                
            filepath = os.path.join(root_dir, file)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            updated = False
            for old_href, new_href in link_redirect_map.items():
                # Handle relative link calculation from the current file's directory
                old_rel_to_file = os.path.relpath(os.path.join(BASE_DIR, old_href), root_dir).replace('\\', '/')
                new_rel_to_file = os.path.relpath(os.path.join(BASE_DIR, new_href.split('#')[0]), root_dir).replace('\\', '/')
                
                if '#' in new_href:
                    new_rel_to_file += '#' + new_href.split('#')[1]

                # Update the href attribute via regex
                pattern = f'href=["\']{re.escape(old_rel_to_file)}(#[^"\']*)?["\']'
                if re.search(pattern, content):
                    content = re.sub(pattern, f'href="{new_rel_to_file}"', content)
                    updated = True

            if updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

def main():
    print("Starting Smart DITA Chunking (Level 3+ Assembly)...")
    if not os.path.exists(MAP_FILE):
        print("Error: Map file not found.")
        return

    # Preserve the original doctype/xml-model header of the map
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        map_content = f.read()
    header_match = re.search(r'^(.*?)<bookmap', map_content, re.DOTALL)
    original_header = header_match.group(1) if header_match else '<?xml version="1.0" encoding="utf-8"?>\n'

    tree = ET.parse(MAP_FILE)
    root = tree.getroot()

    # Iterate through Level 1 (Chapters/Appendices)
    for level1_elem in root:
        if level1_elem.tag in ['chapter', 'appendix', 'part']:
            
            # Iterate through Level 2 (Main Topics)
            for level2_elem in list(level1_elem):
                if level2_elem.tag == 'topicref':
                    href2 = level2_elem.get('href')
                    
                    if href2 and href2.endswith('.dita'):
                        level2_filepath = os.path.normpath(os.path.join(BASE_DIR, href2))
                        
                        # Get root ID of Level 2 for section linking logic
                        if os.path.exists(level2_filepath):
                            with open(level2_filepath, 'r', encoding='utf-8') as f:
                                level2_root_id = get_root_id(f.read())
                            
                            # Execute the recursive merger
                            process_node(level2_elem, level2_filepath, level2_root_id)

    # Reconstruct the map file with the preserved header
    xml_data = ET.tostring(root, encoding='utf-8').decode('utf-8')
    final_map_xml = original_header + '<bookmap' + xml_data.split('<bookmap')[1]
    
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(final_map_xml)
        
    # Execute global cross-reference healing
    update_global_xrefs()
    
    print("Architecture assembly complete. All files and links optimized.")

if __name__ == "__main__":
    main()