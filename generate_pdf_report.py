"""
Direct PDF generator for Glance ML Assignment Submission.
Bypasses markdown parsing entirely - content is written section by section
for perfect, precise layout control.
"""
from fpdf import FPDF


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def s(text: str) -> str:
    """Sanitize text for latin-1 encoding used by FPDF core fonts."""
    replacements = {
        '\u2014': '--', '\u2013': '-',
        '\u201c': '"', '\u201d': '"',
        '\u2018': "'", '\u2019': "'",
        '\u2022': '*', '\u2192': '->',
        '\u00d7': 'x', '\u03b1': 'a',
        '\u2264': '<=', '\u2265': '>=',
        '\u2260': '!=',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')


# ---------------------------------------------------------------------------
# PDF subclass with header / footer
# ---------------------------------------------------------------------------

ACCENT   = (41, 65, 148)    # deep indigo
ACCENT2  = (231, 76,  60)   # coral red
MID      = (80, 95, 120)    # mid-slate
LIGHT_BG = (245, 247, 252)  # very light blue-white
CODE_BG  = (248, 248, 250)  # near-white
RULE_CLR = (190, 200, 220)  # divider colour


class PDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(*MID)
        self.cell(0, 8,
                  'Multimodal Fashion & Context Retrieval  |  Glance ML Internship Assignment',
                  border=0, align='R')
        self.ln(10)

    def footer(self):
        self.set_y(-14)
        self.set_font('Helvetica', 'I', 7.5)
        self.set_text_color(*MID)
        self.cell(0, 8, f'Page {self.page_no()}/{{nb}}', border=0, align='C')

    # ------------------------------------------------------------------ #
    # Convenience drawing methods                                          #
    # ------------------------------------------------------------------ #

    def rule(self):
        """Draw a horizontal divider line."""
        self.ln(3)
        self.set_draw_color(*RULE_CLR)
        self.set_line_width(0.3)
        self.line(self.l_margin, self.get_y(),
                  self.w - self.r_margin, self.get_y())
        self.ln(5)

    def h1(self, text: str):
        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(*ACCENT)
        self.multi_cell(0, 9, s(text), border=0, align='L')
        self.ln(1)

    def h2(self, text: str):
        self.ln(2)
        # coloured left bar
        self.set_fill_color(*ACCENT)
        self.rect(self.l_margin, self.get_y(), 3, 7, 'F')
        self.set_x(self.l_margin + 5)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*ACCENT)
        self.cell(0, 7, s(text), border=0, align='L')
        self.ln(9)

    def h3(self, text: str):
        self.ln(1)
        self.set_font('Helvetica', 'B', 10.5)
        self.set_text_color(*MID)
        self.multi_cell(0, 6, s(text), border=0, align='L')
        self.ln(2)

    def body(self, text: str, size: float = 10):
        self.set_font('Helvetica', '', size)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, s(text), border=0, align='L')
        self.ln(2)

    def bullet(self, text: str, level: int = 0, bold_prefix: str = ''):
        """Bullet item with optional bold prefix."""
        indent = 4 + level * 6
        self.set_x(self.l_margin + indent)
        self.set_font('Helvetica', 'B', 9.5)
        self.set_text_color(*MID)
        self.cell(4, 5.5, '-', border=0)

        line_w = self.w - self.l_margin - self.r_margin - indent - 4
        if bold_prefix:
            self.set_font('Helvetica', 'B', 9.5)
            self.set_text_color(30, 30, 30)
            self.cell(self.get_string_width(bold_prefix) + 1, 5.5,
                      s(bold_prefix), border=0)
            self.set_font('Helvetica', '', 9.5)
            self.multi_cell(line_w - self.get_string_width(bold_prefix) - 1,
                            5.5, s(text), border=0, align='L')
        else:
            self.set_font('Helvetica', '', 9.5)
            self.set_text_color(40, 40, 40)
            self.multi_cell(line_w, 5.5, s(text), border=0, align='L')
        self.set_x(self.l_margin)
        self.ln(1)

    def code_block(self, lines_: list[str]):
        """Render a mono-spaced code block with background."""
        self.ln(1)
        # measure height
        line_h = 4.5
        pad = 3
        total_h = len(lines_) * line_h + pad * 2
        x0 = self.l_margin + 4
        w0 = self.w - self.l_margin - self.r_margin - 8
        y0 = self.get_y()

        # Background rect
        self.set_fill_color(*CODE_BG)
        self.set_draw_color(*RULE_CLR)
        self.set_line_width(0.2)
        self.rect(x0, y0, w0, total_h, 'FD')

        # Text
        self.set_font('Courier', '', 8.5)
        self.set_text_color(35, 35, 45)
        self.set_y(y0 + pad)
        for ln in lines_:
            self.set_x(x0 + 3)
            self.cell(w0 - 6, line_h, s(ln), border=0, align='L')
            self.ln(line_h)
        self.set_y(y0 + total_h + 2)
        self.ln(1)

    def info_box(self, text: str, colour=(240, 248, 255)):
        """A light coloured info / note box."""
        self.ln(2)
        x0 = self.l_margin + 4
        w0 = self.w - self.l_margin - self.r_margin - 8
        self.set_font('Helvetica', 'I', 9)
        line_h = 5
        # Estimate height
        chars_per_line = int(w0 / 2.7)
        approx_lines = max(1, len(text) // chars_per_line + 1)
        total_h = approx_lines * line_h + 6
        y0 = self.get_y()
        self.set_fill_color(*colour)
        self.set_draw_color(170, 195, 230)
        self.set_line_width(0.3)
        self.rect(x0, y0, w0, total_h, 'FD')
        self.set_text_color(40, 60, 100)
        self.set_xy(x0 + 4, y0 + 3)
        self.multi_cell(w0 - 8, line_h, s(text), border=0, align='L')
        self.set_y(y0 + total_h + 3)

    def kv(self, key: str, val: str):
        """Key-value pair inline."""
        self.set_font('Helvetica', 'B', 9.5)
        self.set_text_color(35, 35, 35)
        self.cell(self.get_string_width(key) + 1, 5.5, s(key), border=0)
        self.set_font('Helvetica', '', 9.5)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 5.5, s(val), border=0, align='L')
        self.ln(0.5)


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------

def render_table(pdf: PDF, headers: list, rows: list, col_widths: list):
    """Render a bordered table with alternating row shading."""
    available_w = pdf.w - pdf.l_margin - pdf.r_margin
    line_h = 4.8

    def table_row(pdf, cells, widths, bold=False, bg=(255, 255, 255)):
        y_start = pdf.get_y()
        x_start = pdf.l_margin

        # Compute per-cell heights first
        heights = []
        for text, w in zip(cells, widths):
            pdf.set_font('Helvetica', 'B' if bold else '', 8)
            # estimate lines
            chars_per_line = max(1, int(w / 2.15))
            n_lines = max(1, (len(text) // chars_per_line) + 1)
            # also count explicit newlines
            n_lines = max(n_lines, text.count('\n') + 1)
            heights.append(n_lines * line_h + 2)
        row_h = max(heights)

        # Check page break
        if y_start + row_h > pdf.h - pdf.b_margin - 5:
            pdf.add_page()
            y_start = pdf.get_y()

        # Draw cells
        for idx, (text, w) in enumerate(zip(cells, widths)):
            x = x_start + sum(widths[:idx])
            pdf.set_xy(x, y_start)
            pdf.set_fill_color(*bg)
            pdf.set_draw_color(*RULE_CLR)
            pdf.set_line_width(0.25)
            pdf.rect(x, y_start, w, row_h, 'FD')
            # Text with padding
            pdf.set_xy(x + 1.5, y_start + 1.5)
            pdf.set_font('Helvetica', 'B' if bold else '', 8)
            pdf.set_text_color(*(30, 40, 80) if bold else (45, 45, 45))
            pdf.multi_cell(w - 3, line_h, s(text), border=0, align='L')
        pdf.set_y(y_start + row_h)

    table_row(pdf, headers, col_widths, bold=True, bg=(220, 230, 248))
    for i, row in enumerate(rows):
        bg = (250, 252, 255) if i % 2 == 0 else (240, 244, 252)
        table_row(pdf, row, col_widths, bold=False, bg=bg)
    pdf.ln(3)


# ---------------------------------------------------------------------------
# COVER PAGE
# ---------------------------------------------------------------------------

def cover_page(pdf: PDF):
    pdf.add_page()

    # Top accent bar
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 0, pdf.w, 38, 'F')

    # Title
    pdf.set_y(10)
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, 'Multimodal Fashion &', border=0, align='C')
    pdf.ln(10)
    pdf.cell(0, 10, 'Context Retrieval Engine', border=0, align='C')
    pdf.ln(18)

    # Sub-title
    pdf.set_font('Helvetica', '', 12)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 8, 'Glance ML Internship Assignment -- Technical Submission', border=0, align='C')
    pdf.ln(14)

    # Divider
    pdf.set_draw_color(*RULE_CLR)
    pdf.set_line_width(0.4)
    pdf.line(30, pdf.get_y(), pdf.w - 30, pdf.get_y())
    pdf.ln(10)

    # Abstract box
    pdf.set_fill_color(*LIGHT_BG)
    pdf.rect(20, pdf.get_y(), pdf.w - 40, 52, 'F')
    pdf.set_xy(28, pdf.get_y() + 5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 6, 'Abstract', border=0, align='L')
    pdf.ln(8)
    pdf.set_x(28)
    pdf.set_font('Helvetica', '', 9.5)
    pdf.set_text_color(40, 40, 40)
    abstract = (
        'This report presents the design, implementation and evaluation of a zero-shot '
        'fashion image retrieval system built on a novel Multi-Vector Compositional Search '
        '(MVCS) architecture. The system overcomes the compositionality limitation of vanilla '
        'CLIP by detecting upper and lower body garment regions, encoding them as separate '
        'CLIP vectors, and scoring candidates with a dynamic weighted composite similarity. '
        'The result is a modular, CPU-friendly pipeline that indexes 1,000+ images in under '
        '25 minutes and returns ranked results with bounding-box overlays through both a '
        'command-line interface and an interactive Streamlit web dashboard.'
    )
    pdf.multi_cell(pdf.w - 56, 5.5, s(abstract), border=0, align='J')
    pdf.ln(12)

    # Key facts row
    facts = [
        ('Models Used', 'YOLOS-Tiny  +  CLIP ViT-B/32'),
        ('Index Size',  '1,016 images  (3 vectors each)'),
        ('Throughput',  '~0.8 s / image on CPU'),
        ('Interface',   'CLI  +  Streamlit Web Dashboard'),
        ('Repository',  'github.com/Aragog540/Multimodal-Fashion-Context-Retrieval'),
    ]
    for key, val in facts:
        pdf.set_x(20)
        pdf.set_font('Helvetica', 'B', 9.5)
        pdf.set_text_color(*ACCENT)
        pdf.cell(48, 5.5, s(key + ':'), border=0)
        pdf.set_font('Helvetica', '', 9.5)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(0, 5.5, s(val), border=0)
        pdf.ln(6)


# ---------------------------------------------------------------------------
# SECTION 1 - Architectural Exploration & Tradeoffs
# ---------------------------------------------------------------------------

def section_architecture(pdf: PDF):
    pdf.add_page()
    pdf.h2('1.  Architectural Exploration & Tradeoffs')
    pdf.body(
        'To solve zero-shot natural language image retrieval for fashion, three primary '
        'architectures were evaluated. The table below summarises each approach:'
    )
    pdf.ln(2)

    headers = ['Approach', 'Description', 'Pros', 'Cons', 'Best For']
    rows = [
        [
            '1. Vanilla CLIP\n(Baseline)',
            'Encode full image & full query with CLIP (ViT-B/32). Rank by cosine similarity.',
            'Extremely fast. Excellent zero-shot general context.',
            'Fails compositionality (red shirt / blue pants). Misses fine-grained details.',
            'General search, high-throughput systems.',
        ],
        [
            '2. VLM Captioning\n(Llava / Moondream)',
            'Run a Vision-Language Model on all images to generate captions, then index with BM25.',
            'Rich detail and relationships captured in text.',
            'Very slow on CPU (3-5 s / image). Sensitive to prompt quality.',
            'Small datasets, high-compute GPU environments.',
        ],
        [
            '3. MVCS\n(Chosen)',
            'YOLOS-Tiny detects person. Three CLIP vectors per image: Global, Upper crop, Lower crop.',
            'Solves compositionality mathematically. Fast CPU inference (~0.8 s). Captures fine-grained colour/style.',
            'Slightly larger DB (3x vectors). Needs anatomical crop heuristics.',
            'Fashion retrieval, compositional queries, high precision.',
        ],
    ]
    # col_widths must sum to page width minus margins
    # 210 - 15 - 15 = 180mm
    render_table(pdf, headers, rows, [32, 42, 38, 38, 30])


# ---------------------------------------------------------------------------
# SECTION 2 - Chosen Approach
# ---------------------------------------------------------------------------

def section_approach(pdf: PDF):
    pdf.add_page()
    pdf.h2('2.  Chosen Approach: Multi-Vector Compositional Search (MVCS)')
    pdf.body(
        'The MVCS architecture breaks retrieval into a multi-channel alignment problem. '
        'A natural language query is decomposed into three sub-queries '
        '(Global, Upper, Lower). Each is encoded by CLIP into a 512-d vector and matched '
        'independently against the three per-image vectors stored in the database. '
        'The final ranking score is a dynamic weighted sum of all three cosine similarities.'
    )

    pdf.h3('System Architecture (ASCII Diagram)')
    pdf.code_block([
        '  Natural Language Query',
        '         |',
        '  [ Syntactic Parser ]',
        '  /          |          \\',
        ' Global   Upper       Lower',
        ' Query    Query       Query',
        '  |          |          |',
        ' CLIP      CLIP        CLIP',
        ' Text      Text        Text',
        '  |          |          |',
        '  \\          |          /',
        '   [ Composite Cosine Similarity Score ]',
        '  /          |          \\',
        ' Global   Upper       Lower',
        ' Vector   Vector      Vector',
        '  |          |          |',
        ' CLIP      CLIP        CLIP',
        ' Image     Crop        Crop',
        '  |          \\          /',
        '  |         [ YOLOS-Tiny Detector ]',
        '  |                  |',
        '  +------  Raw Image  --------+',
    ])

    pdf.h3('Key Technical Elements')

    pdf.bullet('Person Detection & Crop Heuristics  (Part A - Indexer)',
               bold_prefix='Step 1 -- ')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    details = (
        'YOLOS-Tiny detects persons in each image. The primary detection is used to crop '
        'the Upper Body (ymin + 10% to ymin + 65% of bounding-box height) and the '
        'Lower Body (ymin + 50% to ymax). If no person is detected (flat-lay images), '
        'the top and bottom halves of the full image are used as fallback crops.'
    )
    pdf.multi_cell(0, 5, s(details), border=0, align='L')
    pdf.ln(2)

    pdf.bullet('Normalised Vector Database  (Part A - Indexer)',
               bold_prefix='Step 2 -- ')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('CLIP ViT-B/32 extracts 512-dimensional L2-normalised embeddings for '
                     'the full image, upper crop and lower crop. All three vectors are stored '
                     'per image in a SQLite database (BLOB columns) for fast retrieval.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('Query Parser  (Part B - Retriever)',
               bold_prefix='Step 3 -- ')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Rule-based segmentation of the natural language query around prepositions '
                     '("with", "and", "in a", "sitting on") produces three sub-query strings '
                     'that are independently encoded with CLIP.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('Dynamic Composite Scoring  (Part B - Retriever)',
               bold_prefix='Step 4 -- ')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Score = w_global * Sim(text_global, img_global)\n'
                     '       + w_upper  * Sim(text_upper,  img_upper)\n'
                     '       + w_lower  * Sim(text_lower,  img_lower)'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.h3('Dynamic Weight Scheme')
    headers = ['Query contains', 'w_global', 'w_upper', 'w_lower']
    rows = [
        ['Both upper & lower specified', '0.40', '0.30', '0.30'],
        ['Only upper garment specified', '0.50', '0.50', '0.00'],
        ['Only context / environment',   '1.00', '0.00', '0.00'],
    ]
    render_table(pdf, headers, rows, [80, 30, 30, 40])


# ---------------------------------------------------------------------------
# SECTION 3 - Evaluation
# ---------------------------------------------------------------------------

def section_evaluation(pdf: PDF):
    pdf.add_page()
    pdf.h2('3.  Evaluation & Verification Results')
    pdf.body(
        'The engine was evaluated on the five benchmark prompts specified in the assignment, '
        'indexed against a database of 1,016 images. Each query is decomposed, searched, '
        'and the top-5 ranked results are displayed with annotated bounding boxes and '
        'similarity scores.'
    )

    benchmarks = [
        (
            '1. Attribute Specific',
            '"A person in a bright yellow raincoat."',
            'Upper: "a bright yellow raincoat"\nLower: "yellow raincoat or pants"',
            'Targets the bright yellow raincoat crop and aligns global similarity.',
        ),
        (
            '2. Contextual / Place',
            '"Professional business attire inside a modern office."',
            'Upper: "professional business blazer or shirt"\nLower: "professional business trousers or skirt"',
            'Matches blazer textures in the upper crop plus office-like global context.',
        ),
        (
            '3. Complex Semantic',
            '"Someone wearing a blue shirt sitting on a park bench."',
            'Upper: "a blue shirt"\nLower: "pants or jeans"',
            'Correlates the blue shirt crop with bench/park global background.',
        ),
        (
            '4. Style Inference',
            '"Casual weekend outfit for a city walk."',
            'Upper: "casual t-shirt or hoodie or top"\nLower: "jeans or casual pants or skirt"',
            'Evaluates style using query expansion heuristics.',
        ),
        (
            '5. Compositional',
            '"A red tie and a white shirt in a formal setting."',
            'Upper: "a red tie and a white shirt"\nLower: "formal suit trousers or skirt"',
            'Isolates upper crop to prevent false-positive colour swaps.',
        ),
    ]

    for title, query, decomp, note in benchmarks:
        pdf.h3(title)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*ACCENT2)
        pdf.multi_cell(0, 5.5, s(f'Query:  {query}'), border=0)
        pdf.ln(1)
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        for line in decomp.split('\n'):
            pdf.set_x(pdf.l_margin + 4)
            pdf.multi_cell(0, 5, s(line), border=0, align='L')
        pdf.set_x(pdf.l_margin)
        pdf.ln(1)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(70, 80, 70)
        pdf.multi_cell(0, 5, s('Result: ' + note), border=0, align='L')
        pdf.ln(4)

    pdf.info_box(
        'The automated evaluation script (test_queries.py) generates annotated top-5 '
        'result grids as JPEG files, with score overlays and red bounding boxes drawn '
        'on each matched image, providing clear visual alignment with all five prompts.'
    )


# ---------------------------------------------------------------------------
# SECTION 4 - Future Extensions
# ---------------------------------------------------------------------------

def section_future(pdf: PDF):
    pdf.add_page()
    pdf.h2('4.  Future Extensions')

    pdf.h3('A.  Location & Weather Integration')
    pdf.body(
        'To extend retrieval to environmental context (e.g. "rainy London street", '
        '"sunny Miami beach") and weather dynamics, the following pipeline additions '
        'are proposed:'
    )
    pdf.bullet('Dual-Model Metadata Tagging', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Integrate a scene classifier (Places365) or image tagger to extract semantic '
                     'environment tags (e.g. snowing, raining, beach, urban) and store them as '
                     'indexing attributes in SQLite.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('External Weather & Geotag Databases', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('If images contain EXIF GPS/timestamp metadata, integrate a weather archive '
                     'API (Open-Meteo) to dynamically assign temperature/precipitation context during indexing.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('Query Expansion & Semantic Reranking', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Expand queries like "London street" at run-time using a lightweight dictionary '
                     'or LLM to add correlated terms ("rainy", "wet pavement", "gloomy weather") and '
                     'weight the global context vector accordingly.'),
                   border=0, align='L')
    pdf.ln(4)

    pdf.h3('B.  Strategies to Improve Precision')
    pdf.bullet('Fine-Tuning CLIP (Contrastive Adaptation)', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Fine-tune CLIP with a contrastive loss on fashion datasets (DeepFashion2, Fashionpedia) '
                     'to align fine-grained descriptors like "houndstooth pattern" and "A-line skirt" with crops.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('VQA Stage-2 Reranking', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Use MVCS to retrieve the top-50 candidates, then pass each through a VQA model '
                     '(Moondream / BLIP) with a yes/no question: "Is this person wearing a bright yellow '
                     'raincoat?" Rerank by VQA confidence to dramatically boost precision.'),
                   border=0, align='L')
    pdf.ln(2)

    pdf.bullet('LLM-Powered Query Expansion', bold_prefix='')
    pdf.set_x(pdf.l_margin + 10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(50, 50, 50)
    pdf.multi_cell(0, 5,
                   s('Use an LLM to generate descriptive variations of the query before encoding '
                     '(e.g. "business attire" -> "button-down shirt, suit jacket, tie, trousers") '
                     'to improve recall without retraining.'),
                   border=0, align='L')
    pdf.ln(2)


# ---------------------------------------------------------------------------
# SECTION 5 - Codebase
# ---------------------------------------------------------------------------

def section_codebase(pdf: PDF):
    pdf.add_page()
    pdf.h2('5.  Codebase & Repository')

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 6, s('GitHub Repository:'), border=0)
    pdf.ln(6)
    pdf.set_font('Helvetica', 'U', 9.5)
    pdf.set_text_color(*ACCENT2)
    pdf.cell(0, 6, s('https://github.com/Aragog540/Multimodal-Fashion-Context-Retrieval'), border=0)
    pdf.ln(10)

    pdf.h3('Project Structure')
    pdf.code_block([
        'glance-assgn/',
        '|',
        '+-- indexer/',
        '|   +-- detector.py       # YOLOS-Tiny person detection & crop generation',
        '|   +-- embedder.py       # CLIP ViT-B/32 embedding extraction (L2-normalised)',
        '|   +-- pipeline.py       # Batched indexing pipeline',
        '|',
        '+-- retriever/',
        '|   +-- parser.py         # Rule-based query decomposer',
        '|   +-- search.py         # Composite scoring & search logic',
        '|   +-- cli.py            # Command-line search interface',
        '|',
        '+-- utils/',
        '|   +-- database.py       # SQLite vector database connector',
        '|',
        '+-- app.py                # Streamlit Web UI Dashboard',
        '+-- test_queries.py       # Benchmark evaluator & visual grid generator',
        '+-- run.py                # Main CLI entrypoint',
        '+-- requirements.txt',
    ])

    pdf.h3('Usage Instructions')

    steps = [
        ('Install dependencies',
         'pip install -r requirements.txt',
         'Installs torch, transformers, pillow, streamlit.'),
        ('Index images  (Part A)',
         'python run.py index --dir "path/to/images" --limit 1000 --batch 16',
         'Runs YOLOS-Tiny + CLIP on all images. ~0.8 s/image on CPU.'),
        ('Launch Web Dashboard',
         'python -m streamlit run app.py',
         'Opens browser at localhost:8501. Sidebar has benchmark query presets.'),
        ('CLI Search  (Part B)',
         'python run.py search "A person in a bright yellow raincoat" --show',
         'Prints ranked table and opens top result with bounding-box overlay.'),
        ('Run Evaluation Suite',
         'python test_queries.py',
         'Evaluates all 5 benchmark prompts and writes annotated JPEG grids.'),
    ]

    for i, (title, cmd, desc) in enumerate(steps, 1):
        pdf.set_font('Helvetica', 'B', 9.5)
        pdf.set_text_color(*MID)
        pdf.cell(0, 6, s(f'Step {i}: {title}'), border=0)
        pdf.ln(6)
        pdf.code_block([cmd])
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(70, 70, 70)
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(0, 5, s(desc), border=0, align='L')
        pdf.ln(3)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def build_pdf(out_path='Glance_ML_Assignment_Submission.pdf'):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.set_margins(15, 18, 15)
    pdf.set_auto_page_break(auto=True, margin=18)

    cover_page(pdf)
    section_architecture(pdf)
    section_approach(pdf)
    section_evaluation(pdf)
    section_future(pdf)
    section_codebase(pdf)

    pdf.output(out_path)
    print(f'Saved: {out_path}  ({pdf.page} pages)')


if __name__ == '__main__':
    build_pdf()
