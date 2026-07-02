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
    """Robust extraction: Captures the root element block safely."""
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'<(topic|concept|task|reference)\b(.*)</\1>', content, re.DOTALL)
    return match.group(0) if match else ""

def transform_to_section(element_content):
    """Transforms outer <topic> into <section>."""
    content = re.sub(r'^<topic\b', '<section', element_content, count=1)
    parts = content.rsplit('</topic>', 1)
    content = '</section>'.join(parts)
    
    content = re.sub(r'<body[^>]*>', '', content, count=1)
    content = re.sub(r'</body>', '', content, count=1)
    return content

def inject_section(parent_filepath, section_content):
    """Injects section content inside the body. Returns True if successful."""
    if not os.path.exists(parent_filepath):
        return False
    with open(parent_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Self-Healing
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
        return True
    return False

def inject_nested_element(parent_filepath, element_content, parent_tag):
    """Robust Injection: Nests element preserving map order. Returns True if success."""
    if not os.path.exists(parent_filepath):
        return False
    with open(parent_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the absolute LAST closing tag of the parent to inject before it
    matches = list(re.finditer(r'</' + re.escape(parent_tag) + r'>', content))
    if matches:
        last_match = matches[-1]
        insert_pos = last_match.start()
        injection_wrapper = f"\n\n\n"
        content = content[:insert_pos] + injection_wrapper + element_content + "\n" + content[insert_pos:]
        with open(parent_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def process_node(parent_elem, parent_filepath, parent_type, parent_root_id):
    """Recursively evaluates nodes, integrating Sibling Protection rules."""
    
    # --- SIBLING SCANNER: Look ahead to protect physical order ---
    has_non_leaf_topic_sibling = False
    if parent_type == 'topic':
        for child_elem in list(parent_elem):
            if child_elem.tag == 'topicref':
                href = child_elem.get('href')
                if href and not href.startswith('http') and href.endswith('.dita'):
                    child_filepath = os.path.normpath(os.path.join(BASE_DIR, href))
                    child_tag, _ = get_root_info(child_filepath)
                    has_children = len([e for e in child_elem if e.tag == 'topicref']) > 0
                    
                    # If any sibling is a topic that WILL NOT become a section
                    if child_tag == 'topic' and has_children:
                        has_non_leaf_topic_sibling = True
                        break

    # --- PROCESS CHILDREN ---
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

            # Sibling Protection: Only allow Section conversion if NO non-leaf topic siblings exist
            can_be_section = is_leaf and child_tag == 'topic' and parent_type == 'topic' and not has_non_leaf_topic_sibling

            # Rule 1: Leaf <topic> under a <topic> parent (Order-Safe) -> Turn to <section>
            if can_be_section:
                child_content = extract_element_content(child_filepath)
                if child_content:
                    section_content = transform_to_section(child_content)
                    
                    # --- NEW FIX: Auto-Heal Internal Cross-References ---
                    # 1. Update internal links to elements: href="#old_id/element" -> href="#new_parent_id/element"
                    section_content = re.sub(f'href=["\']#{re.escape(child_id)}/([^"\']+)["\']', f'href="#{parent_root_id}/\\1"', section_content)
                    # 2. Update internal links to the topic itself: href="#old_id" -> href="#new_parent_id/old_id"
                    section_content = re.sub(f'href=["\']#{re.escape(child_id)}["\']', f'href="#{parent_root_id}/{child_id}"', section_content)
                    # ----------------------------------------------------

                    if inject_section(parent_filepath, section_content):
                        old_rel = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                        new_rel = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                        link_redirect_map[old_rel] = f"{new_rel}#{parent_root_id}/{child_id}"
                        
                        if os.path.exists(child_filepath):
                            os.remove(child_filepath)
                        parent_elem.remove(child_elem)
                    else:
                        print(f"Safety Abort: Could not inject {os.path.basename(child_filepath)} as section.")

            # Rule 2: Same Type Merging (Fallback for protected leaf topics, and non-leaf topics)
            elif child_tag == parent_type:
                process_node(child_elem, child_filepath, child_tag, child_id)
                
                child_content = extract_element_content(child_filepath)
                if child_content:
                    if inject_nested_element(parent_filepath, child_content, parent_type):
                        old_rel = os.path.relpath(child_filepath, BASE_DIR).replace('\\', '/')
                        new_rel = os.path.relpath(parent_filepath, BASE_DIR).replace('\\', '/')
                        link_redirect_map[old_rel] = f"{new_rel}#{child_id}"
                        
                        if os.path.exists(child_filepath):
                            os.remove(child_filepath)
                        parent_elem.remove(child_elem)
                    else:
                        print(f"Safety Abort: Could not inject {os.path.basename(child_filepath)} as nested element.")

            # Rule 3: Different Type boundary -> Keep independent
            else:
                process_node(child_elem, child_filepath, child_tag, child_id)

def update_global_xrefs():
    """Patches broken links globally."""
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
                old_rel = os.path.relpath(os.path.join(BASE_DIR, old_href), root_dir).replace('\\', '/')
                new_rel = os.path.relpath(os.path.join(BASE_DIR, new_href.split('#')[0]), root_dir).replace('\\', '/')
                if '#' in new_href:
                    new_rel += '#' + new_href.split('#')[1]

                pattern = f'href=["\']{re.escape(old_rel)}(#[^"\']*)?["\']'
                if re.search(pattern, content):
                    content = re.sub(pattern, f'href="{new_rel}"', content)
                    updated = True
            if updated:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

def main():
    print("Starting Armored Type-Boundary DITA Chunking Engine with Sibling Protection...")
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
                            parent_tag, parent_id = get_root_info(level2_filepath)
                            if parent_tag:
                                process_node(level2_elem, level2_filepath, parent_tag, parent_id)

    xml_data = ET.tostring(root, encoding='utf-8').decode('utf-8')
    final_map_xml = original_header + '<bookmap' + xml_data.split('<bookmap')[1]
    
    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(final_map_xml)
        
    update_global_xrefs()
    print("Process finished successfully. Content tree optimized.")

if __name__ == "__main__":
    main()