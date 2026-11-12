import os
import re
import sys
from xml.sax.saxutils import escape

def slugify(text):
    """تحويل العنوان إلى معرف (ID) واسم ملف صالح في DITA"""
    clean = re.sub(r'`([^`]+)`', r'\1', text)
    clean = re.sub(r'[^a-zA-Z0-9]+', '_', clean.lower()).strip('_')
    return clean if clean else "topic"

def format_inline(text):
    """تحويل تنسيقات Markdown الداخلية إلى وسوم DITA XML"""
    # هروب محارف XML الأساسية أولاً
    text = escape(text)
    # تحويل `code` إلى <codeph>
    text = re.sub(r'`([^`]+)`', r'<codeph>\1</codeph>', text)
    # تحويل **bold** إلى <b>
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # تحويل *italic* إلى <i>
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text

def build_32bit_visual_table(bit_rows):
    """
    توليد جدول DITA CALS بصري من 32 عموداً يمثل شريط الـ 32-Bit تلقائياً
    بناءً على صفوف جدول البتات مثل [31:2] و [1:0]
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

    # ترتيب الحقول من البت 31 (يسار) إلى البت 0 (يمين)
    parsed_fields.sort(key=lambda x: x[0], reverse=True)

    xml = ['      <table frame="all" rowsep="1" colsep="1" outputclass="bitfield-visual">']
    xml.append('        <tgroup cols="32">')
    for i in range(1, 33):
        xml.append(f'          <colspec colname="c{i}" colnum="{i}" colwidth="1*"/>')
    xml.append('          <thead>')
    xml.append('            <row>')
    # ترقيم البتات من 31 إلى 0
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
    """تحويل جدول Markdown قياسي إلى جدول DITA CALS"""
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

    # إزالة تعليقات HTML من ملف الـ Markdown
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
    lines = content.splitlines()

    # 1. التحقق من وجود عنوان مستوى أول (#) واحد فقط
    h1_lines = [line for line in lines if re.match(r'^#\s+[^#]', line)]
    if len(h1_lines) == 0:
        raise ValueError("خطأ: الملف لا يحتوي على عنوان رئيسي من المستوى الأول (#).")
    elif len(h1_lines) > 1:
        raise ValueError(f"خطأ: يجب أن يحتوي الملف على عنوان (#) واحد فقط، تم العثور على {len(h1_lines)}.")

    doc_title = re.sub(r'^#\s+', '', h1_lines[0]).strip()
    os.makedirs(out_dir, exist_ok=True)

    # تقسيم الملف حسب العناوين الرئيسية (##)
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

    # توليد ملف DITA لكل فصل (##)
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

        while i < len(c_lines):
            line = c_lines[i].strip()
            if not line:
                i += 1
                continue

            # التعامل مع العناوين الفرعية (### أو ####) كأقسام <section>
            h_sub = re.match(r'^(#{3,4})\s+(.+)', line)
            if h_sub:
                if in_section:
                    xml_lines.append('    </section>')
                sec_title = h_sub.group(2).strip()
                sec_id = slugify(sec_title)
                xml_lines.append(f'    <section id="{sec_id}">')
                xml_lines.append(f'      <title>{format_inline(sec_title)}</title>')
                in_section = True
                i += 1
                continue

            # التعامل مع الصور ![Alt](path)
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

            # التعامل مع الجداول القياسية | Col1 | Col2 |
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
                    
                    # إذا كان الجدول يخص توزيع البتات، نولد شريط الـ 32-بت البصري أولاً
                    if expect_visual_bitfield or (headers and headers[0].lower() == 'bit'):
                        visual_bar = build_32bit_visual_table(rows)
                        if visual_bar:
                            xml_lines.append(visual_bar)
                        expect_visual_bitfield = False

                    xml_lines.append(build_cals_table(headers, rows))
                continue

            # التحقق من سطر Register bit assignments لتفعيل الرسم البصري
            if "register bit assignments" in line.lower():
                expect_visual_bitfield = True

            # فقرة نصية عادية
            xml_lines.append(f'      <p>{format_inline(line)}</p>')
            i += 1

        if in_section:
            xml_lines.append('    </section>')

        xml_lines.append('  </body>\n</topic>')

        with open(os.path.join(out_dir, filename), 'w', encoding='utf-8') as out_f:
            out_f.write("\n".join(xml_lines))

    # توليد خريطة DITA Map الرئيسية
    map_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE map PUBLIC "-//OASIS//DTD DITA Map//EN" "map.dtd">',
        f'<map id="{slugify(doc_title)}_map">',
        f'  <title>{escape(doc_title)}</title>',
        '  <!-- يتم حقن ملف المقدمة الثابت تلقائياً هنا -->',
        '  <!-- <topicref href="common/preface_signal_conventions.dita"/> -->'
    ]
    for fname, ftitle in topic_files:
        map_lines.append(f'  <topicref href="{fname}" navtitle="{escape(ftitle)}"/>')
    map_lines.append('</map>')

    map_path = os.path.join(out_dir, "trm.ditamap")
    with open(map_path, 'w', encoding='utf-8') as mf:
        mf.write("\n".join(map_lines))

    print(f"تم التحويل بنجاح! تم إنشاء {len(topic_files)} ملفات DITA مع الخريطة في المجلد: {out_dir}")

if __name__ == "__main__":
    input_md = sys.argv[1] if len(sys.argv) > 1 else "trm-template.md"
    convert_md_to_dita(input_md)