import xml.etree.ElementTree as ET
import os
import re

# --- Configuration Paths (Fixed & Static) ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
OUT_DIR = os.path.join(PROJECT_ROOT, "out")
DITA_DIR = os.path.join(OUT_DIR, "dita")

MAP_FILE = os.path.join(OUT_DIR, "book.ditamap")
RELEASE_VARS_FILE = os.path.join(DITA_DIR, "release_vars.ditamap")

def generate_and_replace_variables():
    """Extract metadata, generate release_vars.ditamap, and update bookmap restoring image tags with keyref"""
    print(f"Processing {MAP_FILE} for centralized variables extraction...")
    
    if not os.path.exists(MAP_FILE):
        print(f"Error: book.ditamap not found at {MAP_FILE}")
        return

    if not os.path.exists(DITA_DIR):
        os.makedirs(DITA_DIR, exist_ok=True)

    with open(MAP_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    variables = {}
    image_keys = {}

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
    data_tags = re.findall(r'(<data\s+name="([^"]+)"[^>]*(?:/>|.*?</data>))', content, re.DOTALL)
    for full_tag, data_name in data_tags:
        image_match = re.search(r'<image\s+href="([^"]+)"([^>]*)>', full_tag)
        if image_match:
            img_href = image_match.group(1)
            img_attrs = image_match.group(2)
            image_keys[data_name] = {"href": img_href, "attrs": img_attrs}
        else:
            val_match = re.search(r'value="([^"]+)"', full_tag)
            if val_match:
                variables[data_name] = val_match.group(1)
            else:
                inner_match = re.search(r'>(.*?)</data>', full_tag, re.DOTALL)
                if inner_match and inner_match.group(1).strip():
                    variables[data_name] = inner_match.group(1).strip()

    # Generate release_vars.ditamap content
    vars_content = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<?xml-model href="urn:oasis:names:tc:dita:rng:map.rng" schematypens="http://relaxng.org/ns/structure/1.0"?>',
        '<map>'
    ]

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

    # Put image hrefs inside release_vars.ditamap
    for key, info in image_keys.items():
        vars_content.append(f'    <keydef keys="{key}" href="{info["href"]}"/>')

    vars_content.append('</map>')

    with open(RELEASE_VARS_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(vars_content))
    print(f"Success: Created release_vars.ditamap with {len(variables) + len(image_keys)} keys.")

    # --- Update book.ditamap ---
    
    if "ManualTitle" in variables:
        content = re.sub(
            r'<booktitle>\s*<mainbooktitle>.*?</mainbooktitle>\s*</booktitle>',
            '<title><ph keyref="ManualTitle"/> Reference Manual</title>',
            content,
            flags=re.DOTALL
        )

    new_bookmeta = ['<bookmeta>']
    if "Release" in variables:
        new_bookmeta.append('    <data keyref="Release"/>')
    if "Date" in variables:
        new_bookmeta.append('    <data keyref="Date"/>')
    
    # Restore <image> tags inside data elements using keyref instead of href
    for key, info in image_keys.items():
        new_bookmeta.append(f'    <data name="{key}">')
        new_bookmeta.append(f'        <image keyref="{key}"{info["attrs"]}/>')
        new_bookmeta.append('    </data>')
        
    for key in variables.keys():
        if key not in ["ManualTitle", "Product", "Version", "Release", "BookPartNo"]:
            new_bookmeta.append(f'    <data keyref="{key}"/>')
            
    new_bookmeta.append('</bookmeta>')

    content = re.sub(r'<bookmeta>.*?</bookmeta>', '\n'.join(new_bookmeta), content, flags=re.DOTALL)

    # Reference release_vars.ditamap with the correct relative path
    if 'dita/release_vars.ditamap' not in content and 'release_vars.ditamap' not in content:
        mapref_tag = '\n    <mapref href="dita/release_vars.ditamap" format="ditamap"/>'
        if '<frontmatter>' in content:
            content = content.replace('<frontmatter>', '<frontmatter>' + mapref_tag, 1)
        elif '</bookmap>' in content:
            content = content.replace('</bookmap>', f'    <frontmatter>{mapref_tag}\n    </frontmatter>\n</bookmap>', 1)
    elif 'href="release_vars.ditamap"' in content:
        content = content.replace('href="release_vars.ditamap"', 'href="dita/release_vars.ditamap"')

    with open(MAP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Success: Updated book.ditamap restoring image tags with keyref.")


if __name__ == "__main__":
    print("--- Starting Release Variables Architect ---")
    generate_and_replace_variables()
    print("--- Process Completed ---")