import os
import re
import xml.etree.ElementTree as ET

# --- Configuration Paths ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
BASE_DIR = os.path.join(PROJECT_ROOT, "out")
MAP_FILE = os.path.join(BASE_DIR, "book.ditamap")

# Global dictionary to track moved files for xref updates
# Format: {'old_file_path.dita': 'new_file_path.dita#id_mapping'}
link_redirect_map = {}

def get_root_info(filepath):
    """Extracts both the tag type and the ID attribute from the root element of a file."""
    if not os.path.exists(filepath):
        return None, None
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    tag_match = re.search(r'<(topic|concept|task|reference|section)\b', content)
    id_match = re.search(r'<(?:topic|concept|task|reference|section)[^>]*\bid=["\']([^"\']+)["\']', content)
    
    tag = tag_match.group(1) if tag_match else None
    root_id = id_match.group(1) if id_match else None
    return tag, root_id

def extract_element_content(filepath):
    """Extracts the entire root element block from a DITA file, discarding headers."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'<(topic|concept|task|reference)\b(.*)</\1>\s*$', content, re.DOTALL)
    return match.group(0) if match else ""

def transform_to_section(element_content):
    """Transforms outer generic <topic> tags into <section> and strips inner <body>."""
    # Convert outer topic tags to section
    content = re.sub(r'^<topic\b', '<section', element_content, count=1)
    content = re.sub(r'</topic>\s*$', '</section>', content, count=1)
    
    # Strip inner generic body tags
    content = re.sub(r'<body[^>]*>', '', content, count=1)
    content = re.sub(r'</body>', '', content, count=1)
    return content

def inject_section(parent_filepath, section_content):
    """Injects transformed section content inside the parent's <body> element."""
    if not os.path.exists(parent_filepath):
        return
    with open(parent_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Self-Healing: Expand self-closing body tags or create a body if completely missing
    if re.search(r'<body\s*/>', content):
        content = re.sub(r'<body\s*/>', '<body>\n    </body>', content, count=1)
    elif not re.search(r'</body>', content):
        content = re.sub(r'(</title>)', r'\1\n    <body>\n    </body>', content, count=1)
        
    match = re.search(r'</body>', content)
    if match:
        insert_pos = match.start()
        injection_wrapper = "\n\n    \n    "
        content = content[:insert_pos] + injection_wrapper + section_content + "\n" + content[insert_pos:]
        with open(parent_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def inject_nested_element(parent_filepath, element_content, parent_tag):
    """Nests an element physically before the final closing tag of the matching parent type."""
    if not os.path.exists(parent_filepath):
        return
    with open(parent_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'</' + re.escape(parent_tag) + r'>\s*$'
    match = re.search(pattern, content)
    if match:
        insert_pos = match.start()
        injection_wrapper = f"\n\n\n"
        content = content[:insert_pos] + injection_wrapper + element_content + "\n" + content[insert_pos:]
        with open(parent_filepath, 'w', encoding='utf-8') as f:
            f.write(content)

def process_node(parent_elem, parent_filepath, parent_type, parent_root_id):
    """
    Recursively evaluates map nodes based on Type-Boundary Chunking Rules.
    - Merges same-type elements physically.
    - Downgrades leaf topics to sections ONLY if the parent is also a topic.
    - Keeps different type elements independent on disk and in the map structure.
    """
    for child_elem in list(parent_elem):
        if child_elem.tag == 'topicref':
            href = child_elem.get('href')
            
            if not href or href.startswith('http') or not href.endswith('.dita'):
                continue
                
            child_filepath = os.path.normpath(os.path.join(BASE_DIR, href))
            child_tag, child_id = get_root_info(child_filepath)
            
            if not child_tag:
                continue
                
            has_children = len([e for e in child_elem if e.tag == 'topicref']) > 0
            is_leaf = not has_children

            # Rule 1: Special Case - Leaf <topic> under a <topic> parent -> Turn to <section>
            if is_leaf and child_tag == 'topic' and parent_type == 'topic':
                child_content = extract_element_content(child_filepath)
                if child_content:
                    section_content = transform_to_section(child_content)
                    inject_section(parent_filepath, section_content)
                    
                    # Track redirect for xref healing
                    old_rel = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                    new_rel = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                    link_redirect_map[old_rel] = f"{new_rel}#{parent_root_id}/{child_id}"
                    
                    # Delete the absorbed child file and clear from map
                    if os.path.exists(child_filepath):
                        os.remove(child_filepath)
                    parent_elem.remove(child_elem)

            # Rule 2: Same Type Merging (topic under topic (non-leaf), task under task, concept under concept)
            elif child_tag == parent_type:
                # Bottom-up processing: clear child's sub-tree first into the child file
                process_node(child_elem, child_filepath, child_tag, child_id)
                
                # SUCK the fully updated child content into the parent file
                child_content = extract_element_content(child_filepath)
                if child_content:
                    inject_nested_element(parent_filepath, child_content, parent_type)
                    
                    # Track redirect for xref healing
                    old_rel = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                    new_rel = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                    link_redirect_map[old_rel] = f"{new_rel}#{child_id}"
                    
                    # Delete child file and remove node from map since it's now internal
                    if os.path.exists(child_filepath):
                        os.remove(child_filepath)
                    parent_elem.remove(child_elem)

            # Rule 3: Different Type boundary -> Keep independent, do NOT merge, but process its sub-tree
            else:
                process_node(child_elem, child_filepath, child_tag, child_id)

def update_global_xrefs():
    """Scans all compiled DITA files to patch broken links following file structural absorption."""
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
    print("Starting Type-Boundary DITA Chunking Engine...")
    if not os.path.exists(MAP_FILE):
        print("Error: Map file not found.")
        return

    # Keep map doctype schema intact
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        map_content = f.read()
    header_match = re.search(r'^(.*?)<bookmap', map_content, re.DOTALL)
    original_header = header_match.group(1) if header_match else '<?xml version="1.0" encoding="utf-8"?>\n'

    tree = ET.parse(MAP_FILE)
    root = tree.getroot()

    # Walk through Level 1 (Chapters / Appendices)
    for level1_elem in root:
        if level1_elem.tag in ['chapter', 'appendix', 'part']:
            
            # Walk through Level 2 (Main Topics acting as initial parent anchors)
            for level2_elem in list(level1_elem):
                if level2_elem.tag == 'topicref':
                    href2 = level2_elem.get('href')
                    if href2 and href2.endswith('.dita'):
                        level2_filepath = os.path.normpath(os.path.join(BASE_DIR, href2))
                        
                        if os.path.exists(level2_filepath):
                            parent_tag, parent_id = get_root_info(level2_filepath)
                            if parent_tag:
                                # Trigger recursive analysis starting from level 2
                                process_node(level2_elem, level2_filepath, parent_tag, parent_id)

    # Output optimized clean map file
    xml_data = ET.tostring(root, encoding='utf-8').decode('utf-8')
    final_map_xml = original_header + '<bookmap' + xml_data.split('<bookmap')[1]
    
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(final_map_xml)
        
    # Execute cross-reference auto-healing across remaining files
    update_global_xrefs()
    print("Process finished successfully. Content tree optimized under Type Boundaries.")

if __name__ == "__main__":
    main()