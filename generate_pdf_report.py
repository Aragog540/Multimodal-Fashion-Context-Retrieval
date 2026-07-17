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
            pdf.ln(4)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 180, pdf.get_y())
            pdf.ln(4)
            continue
            
        # Handle Code Block Toggles
        if line_strip.startswith("```"):
            in_code_block = not in_code_block
            pdf.ln(2)
            continue
            
        # If in a code block, format as Courier mono-spaced
        if in_code_block:
            pdf.set_font("courier", "", 9)
            pdf.set_text_color(50, 50, 60)
            
            # Temporarily shift left margin for code block indentation
            pdf.set_left_margin(25)
            pdf.set_x(25)
            pdf.multi_cell(160, 4.5, sanitize_text(line), border=0, align="L")
            pdf.set_left_margin(15)
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
            pdf.set_font("helvetica", "B", 13)
            pdf.set_text_color(40, 60, 130)  # Muted Blue Heading
            heading = line_strip[3:]
            pdf.multi_cell(180, 7, sanitize_text(heading), border=0, align="L")
            pdf.ln(3)
            continue
            
        if line_strip.startswith("### "):
            pdf.ln(3)
            pdf.set_font("helvetica", "B", 10.5)
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
            
            # Formatted box
            pdf.set_font("helvetica", "I", 9.5)
            pdf.set_text_color(90, 20, 20)  # Dark Red Alert Text
            pdf.set_fill_color(255, 245, 245)  # Light pink background
            pdf.set_left_margin(20)
            pdf.set_x(20)
            # Draw a light box for alerts
            pdf.multi_cell(170, 5, sanitize_text(f"Note: {alert_text}"), border=1, align="L", fill=True)
            pdf.set_left_margin(15)
            pdf.set_x(15)
            pdf.ln(2)
            continue
            
        # Handle List Items (Hanging Indents)
        is_bullet = line_strip.startswith("- ") or line_strip.startswith("* ")
        if is_bullet:
            line_content = line_strip[2:]
            
            # Print bullet symbol at X=18
            pdf.set_x(18)
            pdf.set_font("helvetica", "B", 10)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(5, 5, "-", border=0, align="L")
            
            # Clean list item text
            cleaned_content = re.sub(r"\*\*([^*]+)\*\*", r"\1", line_content)
            cleaned_content = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned_content)
            
            # Set left margin to 23 for proper text wrapping
            pdf.set_left_margin(23)
            pdf.set_x(23)
            pdf.set_font("helvetica", "", 9.5)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(167, 5, sanitize_text(cleaned_content), border=0, align="L")
            
            # Reset left margin
            pdf.set_left_margin(15)
            pdf.set_x(15)
            pdf.ln(1)
            continue
            
        # Handle Table Formatting (Clean 5-column grid)
        if line_strip.startswith("|"):
            # If it's the header separator line, skip it
            if "---" in line_strip or "| :---" in line_strip:
                continue
            
            # Parse table columns
            columns = [c.strip() for c in line_strip.split("|")[1:-1]]
            
            # We want a 5-column layout
            # Table width: 30 + 45 + 35 + 35 + 35 = 180mm
            col_widths = [30, 45, 35, 35, 35]
            
            if len(columns) >= 5:
                # Check if it is the header row
                is_header = "Approach" in columns[0]
                
                # Check if we need to trigger page break to prevent split cells
                # Estimate height based on length of longest cell (approx 15 lines max -> ~60mm height)
                approx_height = max([len(col) // 10 * 4 + 8 for col in columns])
                if pdf.get_y() + approx_height > 275:
                    pdf.add_page()
                    
                x_before = pdf.get_x()
                y_before = pdf.get_y()
                max_h = 0
                
                # Draw the row cells
                for col_idx, text in enumerate(columns[:5]):
                    # Parse bold markers and HTML breaks
                    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
                    text = text.replace("<br>", "\n")
                    
                    # Set font & colors
                    if is_header:
                        pdf.set_font("helvetica", "B", 8)
                        pdf.set_fill_color(230, 235, 245)  # Light Blue/Grey background for header
                        pdf.set_text_color(30, 40, 80)
                    else:
                        pdf.set_font("helvetica", "", 7.5)
                        pdf.set_fill_color(255, 255, 255)  # White background for rows
                        pdf.set_text_color(40, 40, 40)
                        
                    # Position cursor and print cell
                    pdf.set_y(y_before)
                    pdf.set_x(x_before + sum(col_widths[:col_idx]))
                    
                    pdf.multi_cell(col_widths[col_idx], 4.5, sanitize_text(text), border=1, align="L", fill=True)
                    
                    # Track height of the cell
                    h_cell = pdf.get_y() - y_before
                    if h_cell > max_h:
                        max_h = h_cell
                
                # Align cursor below the row
                pdf.set_y(y_before + max_h)
                pdf.set_x(15)
                pdf.ln(1)
                continue
            
        # Handle Standard Paragraphs
        if line_strip:
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(45, 45, 45)
            
            cleaned_line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line_strip)
            cleaned_line = re.sub(r"`([^`]+)`", r"\1", cleaned_line)
            cleaned_line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned_line)
            
            pdf.multi_cell(180, 5, sanitize_text(cleaned_line), border=0, align="L")
            pdf.ln(2.5)
        else:
            pdf.ln(1.5)

    print(f"Saving PDF to {pdf_path}...")
    pdf.output(pdf_path)
    print("PDF generation completed successfully!")

if __name__ == "__main__":
    build_pdf_from_markdown()
