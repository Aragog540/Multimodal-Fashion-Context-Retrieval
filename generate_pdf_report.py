import os
import re
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        # Header title
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Glance ML Internship Assignment Submission - Multimodal Fashion & Context Retrieval", border=0, align="R")
        self.ln(12)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", border=0, align="C")

def sanitize_text(text):
    """Replaces unicode characters not supported by standard latin-1 fonts in FPDF."""
    text = text.replace('\u2014', '--')  # em-dash
    text = text.replace('\u2013', '-')   # en-dash
    text = text.replace('\u201c', '"')   # left double quote
    text = text.replace('\u201d', '"')   # right double quote
    text = text.replace('\u2018', "'")   # left single quote
    text = text.replace('\u2019', "'")   # right single quote
    text = text.replace('\u2022', '*')   # bullet point
    text = text.replace('\u22c5', '*')   # dot operator
    text = text.replace('\u2192', '->')  # arrow
    # Fallback encoding to strip any unmappable characters
    return text.encode('latin-1', 'replace').decode('latin-1')

def build_pdf_from_markdown(md_path="REPORT.md", pdf_path="Glance_ML_Assignment_Submission.pdf"):
    print(f"Reading markdown from {md_path}...")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    pdf = PDFReport(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(15, 15, 15)
    pdf.add_page()
    
    # Enable automatic page breaks
    pdf.set_auto_page_break(auto=True, margin=15)
    
    lines = content.split("\n")
    in_code_block = False
    
    for line in lines:
        line_strip = line.strip()
        
        # Handle Horizontal Rules
        if line_strip in ("---", "***"):
            pdf.ln(5)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
            pdf.ln(5)
            continue
            
        # Handle Code Block Toggles
        if line_strip.startswith("```"):
            in_code_block = not in_code_block
            pdf.ln(2)
            continue
            
        # If in a code block, format as Courier mono-spaced
        if in_code_block:
            pdf.set_font("courier", "", 9)
            pdf.set_text_color(40, 40, 50)
            # Indent code blocks
            pdf.cell(10)
            pdf.multi_cell(170, 5, sanitize_text(line), border=0, align="L")
            pdf.set_x(15)
            continue
            
        # Handle Headings
        if line_strip.startswith("# "):
            pdf.ln(6)
            pdf.set_font("helvetica", "B", 18)
            pdf.set_text_color(30, 40, 90)  # Dark Blue Title
            title = line_strip[2:]
            pdf.multi_cell(180, 8, sanitize_text(title), border=0, align="L")
            pdf.ln(4)
            continue
            
        if line_strip.startswith("## "):
            pdf.ln(5)
            pdf.set_font("helvetica", "B", 14)
            pdf.set_text_color(40, 60, 130)  # Muted Blue Heading
            heading = line_strip[3:]
            pdf.multi_cell(180, 7, sanitize_text(heading), border=0, align="L")
            pdf.ln(3)
            continue
            
        if line_strip.startswith("### "):
            pdf.ln(4)
            pdf.set_font("helvetica", "B", 11)
            pdf.set_text_color(50, 50, 80)
            sub = line_strip[4:]
            pdf.multi_cell(180, 6, sanitize_text(sub), border=0, align="L")
            pdf.ln(2)
            continue

        # Handle Alert Blockquotes
        if line_strip.startswith("> "):
            # Strip > [!NOTE] or > [!IMPORTANT] etc.
            alert_text = line_strip[2:]
            alert_text = re.sub(r"^\[!(NOTE|IMPORTANT|WARNING|TIP|CAUTION)\]\s*", "", alert_text)
            
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(100, 30, 30)  # Dark Red Alert Text
            pdf.set_fill_color(255, 240, 240)  # Light pink background
            # Draw a light box for alerts
            pdf.multi_cell(180, 5, sanitize_text(f"Note: {alert_text}"), border=1, align="L", fill=True)
            pdf.ln(2)
            continue
            
        # Handle List Items
        is_bullet = line_strip.startswith("- ") or line_strip.startswith("* ")
        if is_bullet:
            line_content = line_strip[2:]
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            # Indent list bullets
            pdf.cell(5)
            # Draw a bullet symbol
            pdf.cell(5, 5, chr(149), border=0, align="L")
            # Parse bold inline markers in bullets
            cleaned_content = re.sub(r"\*\*([^*]+)\*\*", r"\1", line_content)
            # Remove markdown links
            cleaned_content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned_content)
            
            pdf.multi_cell(170, 5, sanitize_text(cleaned_content), border=0, align="L")
            pdf.set_x(15)
            pdf.ln(1)
            continue
            
        # Handle Table Formatting (Simple skip or parse)
        if line_strip.startswith("|"):
            # If it's the header separator line, skip it
            if "---" in line_strip:
                continue
            # Parse table columns
            columns = [c.strip() for c in line_strip.split("|")[1:-1]]
            pdf.set_font("helvetica", "B" if "Approach" in line_strip or "Vanilla" in line_strip else "", 8)
            pdf.set_text_color(40, 40, 40)
            
            # Simple column rendering with width limits
            # Table width: 40 + 55 + 40 + 45 = 180mm
            col_widths = [40, 55, 45, 40]
            if len(columns) >= 4:
                x_before = pdf.get_x()
                y_before = pdf.get_y()
                max_h = 0
                for col_idx, text in enumerate(columns[:4]):
                    # Parse bold markers
                    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
                    text = text.replace("<br>", "\n")
                    pdf.set_x(x_before + sum(col_widths[:col_idx]))
                    # Print inside cell
                    pdf.multi_cell(col_widths[col_idx], 4, sanitize_text(text), border=1, align="L")
                    # Track max height
                    h_cell = pdf.get_y() - y_before
                    if h_cell > max_h:
                        max_h = h_cell
                        
                pdf.set_y(y_before + max_h)
                pdf.set_x(15)
                continue
            
        # Handle Standard Paragraphs
        if line_strip:
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(40, 40, 40)
            cleaned_line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line_strip)
            # Strip inline code markers
            cleaned_line = re.sub(r"`([^`]+)`", r"\1", cleaned_line)
            # Strip links [Text](URL) -> Text
            cleaned_line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned_line)
            
            pdf.multi_cell(180, 5, sanitize_text(cleaned_line), border=0, align="L")
            pdf.ln(3)
        else:
            pdf.ln(2)

    print(f"Saving PDF to {pdf_path}...")
    pdf.output(pdf_path)
    print("PDF generation completed successfully!")

if __name__ == "__main__":
    build_pdf_from_markdown()
