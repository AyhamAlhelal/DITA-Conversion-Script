import os
import re
import sys
from xml.sax.saxutils import escape

def slugify(text):
    """Convert heading text into a valid DITA ID and filename."""
    clean = re.sub(r'`([^`]+)`', r'\1', text)
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', clean.lower()).strip('_')
    return clean if clean else "topic"

def format_inline(text):
    """Convert inline Markdown formatting into DITA XML tags."""
    # Escape basic XML characters first
    text = escape(text)
    # Convert `code` to <codeph>
    text = re.sub(r'`([^`]+)`', r'<codeph>\1</codeph>', text)
    # Convert **bold** to <b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # Convert *italic* to <i>
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

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

    # Sort fields from bit 31 (left) down to bit 0 (right)
    parsed_fields.sort(key=lambda x: x[0], reverse=True)

    xml = ['      <table frame="all" rowsep="1" colsep="1" outputclass="bitfield-visual">']
    xml.append('        <tgroup cols="32">')
    for i in range(1, 33):
        xml.append(f'          <colspec colname="c{i}" colnum="{i}" colwidth="1*"/>')
    xml.append('          <thead>')
    xml.append('            <row>')
    # Number bits from 31 down to 0
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
    xml.append('