import os
import re
import sys
import base64
import shutil
import subprocess
import urllib.request
from xml.sax.saxutils import escape

def slugify(text):
    """Convert heading text into a valid DITA ID and filename."""
    clean = re.sub(r'`([^`]+)`', r'\1', text)
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', clean.lower()).strip('_')
    return clean if clean else "topic"

def format_inline(text):
    """Convert inline Markdown formatting into DITA XML tags."""
    text = escape(text)
    text = re.sub(r'`([^`]+)`', r'<codeph>\1</codeph>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

def render_mermaid_to_svg(mermaid_code, output_svg_path, mmd_source_path):
    """
    Save the Mermaid source file (.mmd) and render it to an SVG file.
    Tries local Mermaid CLI (mmdc) first, then falls back to mermaid.ink API.
    """
    os.makedirs(os.path.dirname(output_svg_path), exist_ok=True)
    with open(mmd_source_path, 'w', encoding='utf-8') as f:
        f.write(mermaid_code.strip() + "\n")

    # 1. Try local Mermaid CLI (mmdc) if installed in PATH
    mmdc_path = shutil.which("mmdc")
    if mmdc_path:
        try:
            subprocess.run(
                [mmdc_path, "-i", mmd_source_path, "-o", output_svg_path, "-b", "transparent"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Warning: Local mmdc failed ({e}), trying fallback renderer...")

    # 2. Fallback to mermaid.ink SVG endpoint
    try:
        encoded = base64.urlsafe_b64encode(mermaid_code.strip().encode('utf-8')).decode('ascii')
        url = f"[https://mermaid.ink/svg/](https://mermaid.ink/svg/){encoded}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            svg_data = response.read()
            with open(output_svg_path, 'wb') as out_f:
                out_f.write(svg_data)
        return True
    except Exception as e:
        print(f"Notice: Could not auto-render SVG ({e}). Saved source at '{mmd_source_path}'.")
        return False

def build_32bit_visual_table(bit_rows):
    """
    Generate a 32-column visual DITA CALS table representing the 32-bit register bar
    based on bitfield rows such as [31:2] and [1:0].
    """
    parsed_fields = []
    for row in bit_rows:
        if len(row) < 2:
            continue
        bit_str = row[0].strip(' `')
        name_str = row[1].strip(' `')
        if name_str == '-' or name_str.lower() in ['reserved', 'undefined']:
            display_name = "Undefined"
        else:
            display_name = escape(name_str)

        match_range = re.match(r'\[(\d+):(\d+)\]', bit_str)
        match_single = re.match(r'\[(\d+)\]', bit_str)
        if match_range:
            msb, lsb = int(match_range.group(1)), int(match_range.group(2))
            parsed_fields.append((msb, lsb, display_name))
        elif match_single:
            b = int(match_single.group(1))
            parsed_fields.append((b, b, display_name))

    if not parsed_fields:
        return ""

    parsed_fields.sort(key=lambda x: x[0], reverse=True)

    xml = ['      <table frame="all" rowsep="1" colsep="1" outputclass="bitfield-visual">']
    xml.append('        <tgroup cols="32">')
    for i in range(1, 33):
        xml.append(f'          <colspec colname="c{i}" colnum="{i}" colwidth="1*"/>')
    xml.append('          <thead>')
    xml.append('            <row>')
    for bit_num in range(31, -1, -1):
        xml.append(f'              <entry align="center">{bit_num}</entry>')
    xml.append('            </row>')
    xml.append('          </thead>')
    xml.append('          <tbody>')
    xml.append('            <row>')
    for msb, lsb, label in parsed_fields:
        col_start = 32 - msb
        col_end = 32 - lsb
        if col_start == col_end:
            xml.append(f'              <entry align="center">{label}</entry>')
        else:
            xml.append(f'              <entry namest="c{col_start}" nameend="c{col_end}" align="center">{label}</entry>')
    xml.append('            </row>')
    xml.append('          </tbody>')
    xml.append('        </tgroup>')
    xml.append('      </table>')
    return "\n".join(xml)

def build_cals_table(headers, rows):
    """Convert a standard Markdown pipe table into a DITA CALS table."""
    cols = len(headers)
    xml = ['      <table frame="all" rowsep="1" colsep="1">']
    xml.append(f'        <tgroup cols="{cols}">')
    for i in range(1, cols + 1):
        xml.append(f'          <colspec colname="c{i}" colnum="{i}" colwidth="1*"/>')
    xml.append('          <thead>\n            <row>')
    for h in headers:
        xml.append(f'              <entry>{format_inline(h)}</entry>')
    xml.append('            </row>\n          </thead>')
    xml.append('          <tbody>')
    for r in rows:
        xml.append('            <row>')
        for idx in range(cols):
            cell_val = r[idx] if idx < len(r) else ""
            xml.append(f'              <entry>{format_inline(cell_val)}</entry>')
        xml.append('            </row>')
    xml.append('          </tbody>\n        </tgroup>\n      </table>')
    return "\n".join(xml)

def convert_md_to_dita(md_filepath, out_dir="dita_output"):
    with open(md_filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Strip HTML comments from the Markdown content
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    lines = content.splitlines()

    # Validate that there is exactly one level-1 heading (#)
    h1_lines = [line for line in lines if re.match(r'^#\s+[^#]', line)]
    if len(h1_lines) == 0:
        raise ValueError("Error: The Markdown file does not contain a level-1 heading (#).")
    elif len(h1_lines) > 1:
        raise ValueError(f"Error: The file must contain exactly one level-1 heading (#), found {len(h1_lines)}.")

    doc_title = re.sub(r'^#\s+', '', h1_lines[0]).strip()
    images_dir = os.path.join(out_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    # Split content by level-2 headings (##) into separate chapters
    chapters = []
    current_chapter = None

    for line in lines:
        if re.match(r'^#\s+[^#]', line):
            continue
        h2_match = re.match(r'^##\s+(.+)', line)
        if h2_match:
            if current_chapter:
                chapters.append(current_chapter)
            current_chapter = {'title': h2_match.group(1).strip(), 'lines': []}
        else:
            if current_chapter is not None:
                current_chapter['lines'].append(line)

    if current_chapter:
        chapters.append(current_chapter)

    topic_files = []
    mermaid_counter = 1

    # Generate a DITA topic file for each level-2 heading (##)
    for chap in chapters:
        c_title = chap['title']
        c_id = slugify(c_title)
        filename = f"{c_id}.dita"
        topic_files.append((filename, c_title))

        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE topic PUBLIC "-//OASIS//DTD DITA Topic//EN" "topic.dtd">',
            f'<topic id="{c_id}">',
            f'  <title>{format_inline(c_title)}</title>',
            '  <body>'
        ]

        in_section = False
        i = 0
        c_lines = chap['lines']
        expect_visual_bitfield = False
        current_context_title = c_title

        while i < len(c_lines):
            raw_line = c_lines[i]
            line = raw_line.strip()
            if not line:
                i += 1
                continue

            # Map sub-headings (### or ####) to <section> elements
            h_sub = re.match(r'^(#{3,4})\s+(.+)', line)
            if h_sub:
                if in_section:
                    xml_lines.append('    </section>')
                sec_title = h_sub.group(2).strip()
                current_context_title = sec_title
                sec_id = slugify(sec_title)
                xml_lines.append(f'    <section id="{sec_id}">')
                xml_lines.append(f'      <title>{format_inline(sec_title)}</title>')
                in_section = True
                i += 1
                continue

            # Handle ```mermaid code blocks
            if line.startswith('```mermaid'):
                i += 1
                mermaid_lines = []
                while i < len(c_lines) and not c_lines[i].strip().startswith('```'):
                    mermaid_lines.append(c_lines[i])
                    i += 1
                if i < len(c_lines):
                    i += 1  # Skip closing ```

                mermaid_code = "\n".join(mermaid_lines)
                diagram_slug = f"{slugify(current_context_title)}_diagram_{mermaid_counter}"
                mermaid_counter += 1

                rel_svg_path = f"images/{diagram_slug}.svg"
                full_svg_path = os.path.join(out_dir, "images", f"{diagram_slug}.svg")
                full_mmd_path = os.path.join(out_dir, "images", f"{diagram_slug}.mmd")

                render_mermaid_to_svg(mermaid_code, full_svg_path, full_mmd_path)

                xml_lines.append('      <fig>')
                xml_lines.append(f'        <title>{format_inline(current_context_title)} Diagram</title>')
                xml_lines.append(f'        <image href="{rel_svg_path}" placement="break"/>')
                xml_lines.append('      </fig>')
                continue

            # Map standard images ![Alt](path) to <fig> elements
            img_match = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)', line)
            if img_match:
                fig_title, img_href = img_match.group(1), img_match.group(2)
                xml_lines.append('      <fig>')
                if fig_title:
                    xml_lines.append(f'        <title>{format_inline(fig_title)}</title>')
                xml_lines.append(f'        <image href="{escape(img_href)}" placement="break"/>')
                xml_lines.append('      </fig>')
                i += 1
                continue

            # Map standard pipe tables | Col1 | Col2 |
            if line.startswith('|'):
                table_lines = []
                while i < len(c_lines) and c_lines[i].strip().startswith('|'):
                    table_lines.append(c_lines[i].strip())
                    i += 1
                if len(table_lines) >= 2:
                    headers = [c.strip() for c in table_lines[0].strip('|').split('|')]
                    rows = []
                    for tl in table_lines[2:]:
                        rows.append([c.strip() for c in tl.strip('|').split('|')])

                    # If this is a bit assignment table, generate the 32-bit visual bar first
                    if expect_visual_bitfield or (headers and headers[0].lower() == 'bit'):
                        visual_bar = build_32bit_visual_table(rows)
                        if visual_bar:
                            xml_lines.append(visual_bar)
                        expect_visual_bitfield = False

                    xml_lines.append(build_cals_table(headers, rows))
                continue

            # Check for "Register bit assignments" marker to trigger visual bitfield generation
            if "register bit assignments" in line.lower():
                expect_visual_bitfield = True

            # Standard paragraph
            xml_lines.append(f'      <p>{format_inline(line)}</p>')
            i += 1

        if in_section:
            xml_lines.append('    </section>')

        xml_lines.append('  </body>\n</topic>')

        with open(os.path.join(out_dir, filename), 'w', encoding='utf-8') as out_f:
            out_f.write("\n".join(xml_lines))

    # Generate main DITA Map
    map_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">',
        f'<map id="{slugify(doc_title)}_map">',
        f'  <title>{escape(doc_title)}</title>',
        '  <!-- Standard boilerplate Preface topic is injected automatically here -->',
        '  <!-- <topicref href="common/preface_signal_conventions.dita"/> -->'
    ]
    for fname, ftitle in topic_files:
        map_lines.append(f'  <topicref href="{fname}" navtitle="{escape(ftitle)}"/>')
    map_lines.append('</map>')

    map_path = os.path.join(out_dir, "trm.ditamap")
    with open(map_path, 'w', encoding='utf-8') as mf:
        mf.write("\n".join(map_lines))

    print(f"Conversion complete! Generated {len(topic_files)} DITA topics, diagrams, and map in '{out_dir}'.")

if __name__ == "__main__":
    input_md = sys.argv[1] if len(sys.argv) > 1 else "TRM-Template.md"
    convert_md_to_dita(input_md)