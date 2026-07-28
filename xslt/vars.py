import xml.etree.ElementTree as ET
import os
import re

# --- Configuration Paths (Fixed & Static) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
MAP_FILE = os.path.join(OUT_DIR, "book.ditamap")
RELEASE_VARS_FILE = os.path.join(OUT_DIR, "release_vars.ditamap")

def generate_and_replace_variables():
    """Extract metadata and variables from book.ditamap, generate release_vars.ditamap, and update bookmap with keyrefs"""
    print(f"Processing {MAP_FILE} for centralized variables extraction...")
    
    if not os.path.exists(MAP_FILE):
        print(f"Error: book.ditamap not found at {MAP_FILE}")
        return

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    variables = {}

    # 1. Extract mainbooktitle
    title_match = re.search(r'<mainbooktitle>(.*?)</mainbooktitle>', content)
    if title_match:
        variables["ManualTitle"] = title_match.group(1).strip()

    # 2. Extract prodname
    prod_match = re.search(r'<prodname>(.*?)</prodname>', content)
    if prod_match:
        variables["Product"] = prod_match.group(1).strip()

    # 3. Extract vrm version/release
    vrm_match = re.search(r'<vrm\s+version="([^"]+)"\s+release="([^"]+)"', content)
    if vrm_match:
        variables["Version"] = vrm_match.group(1).strip()
        variables["Release"] = vrm_match.group(2).strip()

    # 4. Extract bookpartno (bookid)
    part_match = re.search(r'<bookpartno>(.*?)</bookpartno>', content)
    if part_match:
        variables["BookPartNo"] = part_match.group(1).strip()

    # 5. Extract all <data name="..." ...> elements dynamically
    # Matches both self-closing data tags and tags with inner content (like images)
    data_tags = re.findall(r'(<data\s+name="([^"]+)"[^>]*(?:/>|.*?</data>))', content, re.DOTALL)
    data_items = {}
    for full_tag, data_name in data_tags:
        # Check if it has a value attribute or inner content
        val_match = re.search(r'value="([^"]+)"', full_tag)
        if val_match:
            data_items[data_name] = val_match.group(1)
        else:
            # Keep the inner content/structure if it contains elements like <image>
            inner_match = re.search(r'>(.*?)</data>', full_tag, re.DOTALL)
            if inner_match and inner_match.group(1).strip():
                data_items[data_name] = inner_match.group(1).strip()

    # Generate release_vars.ditamap content following company standard
    vars_content = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml-model href="urn:oasis:names:tc:dita:rng:map.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>',
        '<map>'
    ]

    # Add standard variables
    for key, val in variables.items():
        vars_content.extend([
            f'    <keydef keys="{key}">',
            '        <topicmeta>',
            '            <keywords>',
            f'                <keyword>{val}</keyword>',
            '            </keywords>',
            '        </topicmeta>',
            '    </keydef>'
        ])

    # Add data items as keys
    for key, val in data_items.items():
        if val.startswith('<'):
            # If the value contains XML tags (like images), include them directly inside keyword/topicmeta
            vars_content.extend([
                f'    <keydef keys="{key}">',
                '        <topicmeta>',
                '            <keywords>',
                f'                <keyword>{val}</keyword>',
                '            </keywords>',
                '        </topicmeta>',
                '    </keydef>'
            ])
        else:
            vars_content.extend([
                f'    <keydef keys="{key}">',
                '        <topicmeta>',
                '            <keywords>',
                f'                <keyword>{val}</keyword>',
                '            </keywords>',
                '        </topicmeta>',
                '    </keydef>'
            ])

    vars_content.append('</map>')

    with open(RELEASE_VARS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vars_content))
    print(f"Success: Created release_vars.ditamap with {len(variables) + len(data_items)} keys.")

    # --- Now update book.ditamap ---
    
    # Transform booktitle to title with ph keyref
    if "ManualTitle" in variables:
        content = re.sub(
            r'<booktitle>\s*<mainbooktitle>.*?</mainbooktitle>\s*</booktitle>',
            '<title><ph keyref="ManualTitle"/> Reference Manual</title>',
            content,
            flags=re.DOTALL
        )

    # Replace bookmeta fields with keyrefs
    new_bookmeta = ['<bookmeta>']
    if "Release" in variables:
        new_bookmeta.append('    <data keyref="Release"/>')
    if "Date" in variables:
        new_bookmeta.append('    <data keyref="Date"/>')
    
    # Include other data keys as keyrefs
    for key in data_items.keys():
        new_bookmeta.append(f'    <data keyref="{key}"/>')
    new_bookmeta.append('</bookmeta>')

    content = re.sub(r'<bookmeta>.*?</bookmeta>', '\n'.join(new_bookmeta), content, flags=re.DOTALL)

    # Ensure release_vars.ditamap is referenced via mapref inside frontmatter
    if 'release_vars.ditamap' not in content:
        mapref_tag = '\n    <mapref href="release_vars.ditamap" format="ditamap"/>'
        if '<frontmatter>' in content:
            content = content.replace('<frontmatter>', '<frontmatter>' + mapref_tag, 1)
        elif '</bookmap>' in content:
            content = content.replace('</bookmap>', f'    <frontmatter>{mapref_tag}\n    </frontmatter>\n</bookmap>', 1)

    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success: Updated book.ditamap with keyrefs and mapref.")


if __name__ == "__main__":
    print("--- Starting Release Variables Architect ---")
    generate_and_replace_variables()
    print("--- Process Completed ---")