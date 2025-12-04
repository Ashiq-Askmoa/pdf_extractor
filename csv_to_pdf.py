import pandas as pd
import argparse
import json
import os
import sys
import ast
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def csv_to_pdf(csv_path, output_pdf):
    """
    Reconstructs a PDF from vector data in a CSV file.
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Create Canvas
        c = canvas.Canvas(output_pdf)
        
        # Group by page number
        pages = df.groupby('page_number')
        
        for page_num, group in pages:
            # Determine page size - try to infer from max coordinates, else default to A4
            # Note: PDF coordinates usually start from bottom-left. 
            # pdfplumber uses top-left for y usually, but let's check how we extracted.
            # In extract_pdf_data.py:
            # line: x0, y0, x1, y1 (pdfplumber raw) -> usually bottom-left origin for lines in PDFMiner, but pdfplumber normalizes?
            # Actually pdfplumber .bbox is (x0, top, x1, bottom).
            # But .lines objects have x0, y0, x1, y1.
            # Let's assume standard PDF coordinate system (bottom-left is 0,0) for reportlab.
            # If the extraction preserved original PDF coordinates, we are good.
            # If pdfplumber converted them, we might need to flip Y. 
            # However, pdfplumber's `page.lines` usually returns PDF coordinates (bottom-left origin).
            # `page.extract_words()` returns `top` and `bottom` relative to top of page.
            # We need to be careful with Y coordinates.
            
            # Let's find the max Y to set page height if possible, or just use A4 (595.27, 841.89)
            # If coordinates are large, we might need a custom page size.
            
            max_x = max(group['x1'].max(), group['x0'].max())
            max_y = max(group['y1'].max(), group['y0'].max())
            
            # Set page size to cover the content + some margin
            page_width = max(max_x + 50, A4[0])
            page_height = max(max_y + 50, A4[1])
            
            c.setPageSize((page_width, page_height))
            
            # We might need to flip Y if the input data was top-based.
            # For now, let's assume the data is compatible or we draw as is.
            # If the output is upside down, we know why.
            # pdfplumber documentation says: "The coordinate system is the standard PDF one: (0, 0) is at the bottom-left."
            # EXCEPT for `extract_words` which uses `top` and `bottom`.
            # In my extraction script:
            # Lines/Rects: used raw x0,y0,x1,y1 -> Bottom-Left origin.
            # Text: used `top` and `bottom`. -> Top-Left origin.
            # So Text Y coordinates need to be flipped relative to page height.
            
            for _, row in group.iterrows():
                elem_type = row['element_type']
                try:
                    props = json.loads(row['properties'])
                except:
                    props = {}
                
                x0 = row['x0']
                y0 = row['y0']
                x1 = row['x1']
                y1 = row['y1']
                
                if elem_type == 'line':
                    # Set color/width if available
                    # pdfplumber line props: 'stroking_color', 'linewidth'
                    if 'stroking_color' in props and props['stroking_color']:
                        # color might be list or tuple
                        color = props['stroking_color']
                        if isinstance(color, (list, tuple)) and len(color) >= 3:
                             c.setStrokeColorRGB(color[0], color[1], color[2])
                    
                    if 'linewidth' in props:
                        c.setLineWidth(props['linewidth'])
                    
                    c.line(x0, y0, x1, y1)
                    
                elif elem_type == 'rect':
                    # pdfplumber rect props: 'non_stroking_color', 'stroking_color'
                    fill = 0
                    if 'non_stroking_color' in props and props['non_stroking_color']:
                        color = props['non_stroking_color']
                        if isinstance(color, (list, tuple)) and len(color) >= 3:
                             c.setFillColorRGB(color[0], color[1], color[2])
                             fill = 1
                    
                    stroke = 0
                    if 'stroking_color' in props and props['stroking_color']:
                         color = props['stroking_color']
                         if isinstance(color, (list, tuple)) and len(color) >= 3:
                             c.setStrokeColorRGB(color[0], color[1], color[2])
                             stroke = 1
                    
                    # ReportLab rect takes (x, y, width, height)
                    w = x1 - x0
                    h = y1 - y0
                    c.rect(x0, y0, w, h, fill=fill, stroke=stroke)
                    
                elif elem_type == 'text':
                    # Text is now standardized to Bottom-Left origin in extraction.
                    # y0 is the bottom of the text (approx baseline).
                    
                    text_content = props.get('text', '')
                    if not text_content:
                        continue
                        
                    # Font settings
                    font_name = props.get('fontname', 'Helvetica')
                    font_size = props.get('size', 10)
                    
                    # Basic font mapping or fallback
                    try:
                        c.setFont(font_name, font_size)
                    except:
                        c.setFont("Helvetica", font_size)
                    
                    # Draw text
                    # reportlab drawString takes (x, y) where y is baseline.
                    # We use y0 which is the bottom of the text bounding box.
                    c.drawString(x0, y0, text_content)

            c.showPage()
            
        c.save()
        print(f"PDF reconstruction complete. Saved to {output_pdf}")

    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reconstruct PDF from CSV vector data.")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("--output", "-o", default="reconstructed.pdf", help="Path to the output PDF file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.csv_file):
        print(f"Error: File '{args.csv_file}' not found.")
        sys.exit(1)
        
    csv_to_pdf(args.csv_file, args.output)
