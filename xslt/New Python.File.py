import os
import re
import xml.etree.ElementTree as ET

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "out")
MAP_FILE = os.path.join(BASE_DIR, "book.ditamap")

# Global dictionary to track moved files for xref updates
link_redirect_map = {}

def get_root_info(content):
    """Extracts both the tag type and the ID attribute from the root element."""
    tag_match = re.search(r'<(topic|concept|task|reference|section)\b', content)
    id_match = re.search(r'<(?:topic|concept|task|reference|section)[^>]*\bid=["\']([^"\']+)["\']', content)
    
    tag = tag_match.group(1) if tag_match else None
    root_id = id_match.group(1) if id_match else None
    return tag, root_id

def extract_and_transform_element(filepath, to_section=False):
    """
    Extracts the root XML element. If to_section is True (only for generic topics), 
    transforms it into <section> and safely unwraps the <body>.
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
    _, element_id = get_root_info(element_content)

    if to_section:
        # 1. Transform generic outer topic to section
        element_content = re.sub(r'^<topic\b', '<section', element_content, count=1)
        element_content = re.sub(r'</topic>\s*$', '</section>', element_content, count=1)
        
        # 2. Strip inner generic body tags (DITA <section> cannot contain <body>)
        element_content = re.sub(r'<body[^>]*>', '', element_content, count=1)
        element_content = re.sub(r'</body>', '', element_content, count=1)

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
            
        # Target the closing tag for safe injection inside the body
        target_tag = r'</body>'
        injection_wrapper = "\n\n    \n    "
    else:
        # Target the closing tag for nested topics (topics, tasks, concepts)
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
    Recursively processes map nodes. Applies the DITA architecture strict rule:
    Only generic <topic> leaves are downgraded to <section>.
    Specialized leaves (<task>, <concept>) remain nested intact.
    """
    for child_elem in list(parent_elem):
        if child_elem.tag == 'topicref':
            href = child_elem.get('href')
            
            if not href or href.startswith('http') or not href.endswith('.dita'):
                continue
                
            child_filepath = os.path.normpath(os.path.join(BASE_DIR, href))
            
            has_children = len([e for e in child_elem if e.tag == 'topicref']) > 0
            is_leaf = not has_children

            # 1. Process deeper children first (Bottom-Up approach)
            if has_children:
                if os.path.exists(child_filepath):
                    with open(child_filepath, 'r', encoding='utf-8') as f:
                        _, child_id = get_root_info(f.read())
                    process_node(child_elem, child_filepath, child_id)

            # 2. Inspect the child before acting
            child_tag = None
            if os.path.exists(child_filepath):
                with open(child_filepath, 'r', encoding='utf-8') as f:
                    child_tag, _ = get_root_info(f.read())

            # 3. Apply Strict Architectural Rule
            transform_to_section = is_leaf and (child_tag == 'topic')

            # 4. Extract and transform current child
            child_content, child_id = extract_and_transform_element(child_filepath, to_section=transform_to_section)
            
            if child_content:
                # 5. Inject into parent file
                inject_content(parent_filepath, child_content, is_section=transform_to_section)
                
                # 6. Map the link redirection
                old_relative_path = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                new_relative_path = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                
                if transform_to_section and parent_root_id and child_id:
                    new_link = f"{new_relative_path}#{parent_root_id}/{child_id}"
                else:
                    new_link = f"{new_relative_path}#{child_id}" if child_id else new_relative_path
                    
                link_redirect_map[old_relative_path] = new_link

                # 7. Cleanup
                if os.path.exists(child_filepath):
                    os.remove(child_filepath)
                parent_elem.remove(child_elem)

def update_global_xrefs():
    """Scans all remaining files and updates broken hrefs using the redirect map."""
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
                old_rel_to_file = os.path.relpath(os.path.join(BASE_DIR, old_href), root_dir).replace('\\', '/')
                new_rel_to_file = os.path.relpath(os.path.join(BASE_DIR, new_href.split('#')[0]), root_dir).replace('\\', '/')
                
                if '#' in new_href:
                    new_rel_to_file += '#' + new_href.split('#')[1]

                pattern = f'href=["\']{re.escape(old_rel_to_file)}(#[^"\']*)?["\']'
                if re.search(pattern, content):
                    content = re.sub(pattern, f'href="{new_rel_to_file}"', content)
                    updated = True

            if updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

def main():
    print("Starting Smart DITA Chunking (Strict Schema Assembly)...")
    if not os.path.exists(MAP_FILE):
        print("Error: Map file not found.")
        return

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        map_content = f.read()
    header_match = re.search(r'^(.*?)<bookmap', map_content, re.DOTALL)
    original_header = header_match.group(1) if header_match else '<?xml version="1.0" encoding="utf-8"?>\n'

    tree = ET.parse(MAP_FILE)
    root = tree.getroot()

    for level1_elem in root:
        if level1_elem.tag in ['chapter', 'appendix', 'part']:
            for level2_elem in list(level1_elem):
                if level2_elem.tag == 'topicref':
                    href2 = level2_elem.get('href')
                    if href2 and href2.endswith('.dita'):
                        level2_filepath = os.path.normpath(os.path.join(BASE_DIR, href2))
                        if os.path.exists(level2_filepath):
                            with open(level2_filepath, 'r', encoding='utf-8') as f:
                                _, level2_root_id = get_root_info(f.read())
                            process_node(level2_elem, level2_filepath, level2_root_id)

    xml_data = ET.tostring(root, encoding='utf-8').decode('utf-8')
    final_map_xml = original_header + '<bookmap' + xml_data.split('<bookmap')[1]
    
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(final_map_xml)
        
    update_global_xrefs()
    print("Architecture assembly complete. All files and links optimized.")

if __name__ == "__main__":
    main()