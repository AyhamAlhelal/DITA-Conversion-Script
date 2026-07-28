import xml.etree.ElementTree as ET
import os
import re

# --- Configuration Paths (Fixed & Static) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
MAP_FILE = os.path.join(OUT_DIR, "book.ditamap")
RELEASE_VARS_FILE = os.path.join(OUT_DIR, "release_vars.ditamap")

def generate_release_variables_map():
    """Extract metadata from book.ditamap and generate release_vars.ditamap matching company standards"""
    print(f"Processing {MAP_FILE} to extract variables and build release_vars.ditamap...")
    
    if not os.path.exists(MAP_FILE):
        print(f"Error: book.ditamap not found at {MAP_FILE}")
        return

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Default extracted values (fallback if tags are missing)
    tool_name = "HAPS-200 6F"
    release_version = "April 2026"
    date_value = "June 2025"

    # Extract <mainbooktitle> value if exists
    title_match = re.search(r'<mainbooktitle>(.*?)</mainbooktitle>', content)
    if title_match:
        tool_name = title_match.group(1).replace(" Reference Manual", "").strip()

    # Extract release/version from <vrm> tag if exists
    vrm_match = re.search(r'<vrm[^>]*release="([^"]+)"', content)
    if vrm_match:
        release_version = vrm_match.group(1)

    # Generate release_vars.ditamap content following company standard
    vars_content = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml-model href="urn:oasis:names:tc:dita:rng:map.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>',
        '<map>',
        '    <keydef keys="ToolTM">',
        '        <topicmeta>',
        '            <keywords>',
        f'                <keyword>{tool_name}</keyword>',
        '            </keywords>',
        '        </topicmeta>',
        '    </keydef>',
        '    <keydef keys="Release">',
        '        <topicmeta>',
        '            <keywords>',
        f'                <keyword>{release_version}</keyword>',
        '            </keywords>',
        '        </topicmeta>',
        '    </keydef>',
        '    <keydef keys="Date">',
        '        <topicmeta>',
        '            <keywords>',
        f'                <keyword>{date_value}</keyword>',
        '            </keywords>',
        '        </topicmeta>',
        '    </keydef>',
        '</map>'
    ]

    with open(RELEASE_VARS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vars_content))
    print(f"Success: Created release_vars.ditamap at {RELEASE_VARS_FILE}")


def update_bookmap_with_variable_keys():
    """Transform book.ditamap hardcoded elements to use ph/data keyrefs and include mapref"""
    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace hardcoded mainbooktitle with keyref structure in title
    content = re.sub(
        r'<title>.*?</title>',
        '<title><ph keyref="ToolTM"/> User Guide</title>',
        content,
        flags=re.DOTALL
    )

    # Replace metadata data blocks with keyrefs
    metadata_replacement = '<bookmeta>\n    <data keyref="Release"/>\n    <data keyref="Date"/>'
    content = re.sub(r'<bookmeta>.*?</bookmeta>', metadata_replacement, content, flags=re.DOTALL)

    # Ensure release_vars.ditamap is referenced inside <frontmatter>
    if 'release_vars.ditamap' not in content:
        mapref_tag = '\n    <mapref href="release_vars.ditamap" format="ditamap"/>'
        content = content.replace('<frontmatter>', '<frontmatter>' + mapref_tag)

    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success: Updated book.ditamap to use keyref variables and mapref.")


if __name__ == "__main__":
    print("--- Starting Release Variables Architect ---")
    generate_release_variables_map()
    update_bookmap_with_variable_keys()
    print("--- Process Completed ---")