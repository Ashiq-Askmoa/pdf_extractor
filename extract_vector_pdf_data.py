import pdfplumber
import pandas as pd
import argparse
import json
import os
import sys

def extract_vector_data(pdf_path, output_csv):
    """
    Extracts lines, rectangles, and text from a PDF and saves to CSV.
    """
    data = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Processing {pdf_path} with {len(pdf.pages)} pages...")
            
            for i, page in enumerate(pdf.pages):
                page_num = i + 1
                
                # Extract Lines
                # pdfplumber extracts lines as dictionaries with keys: x0, y0, x1, y1, width, height, etc.
                # It separates 'lines' (stroked paths) and 'rects' (filled/stroked rectangles).
                
                for line in page.lines:
                    # Properties to keep
                    props = {k: v for k, v in line.items() if k not in ['x0', 'y0', 'x1', 'y1', 'page_number']}
                    
                    data.append({
                        'page_number': page_num,
                        'element_type': 'line',
                        'x0': line.get('x0'),
                        'y0': line.get('y0'),
                        'x1': line.get('x1'),
                        'y1': line.get('y1'),
                        'properties': json.dumps(props)
                    })

                # Extract Rectangles
                for rect in page.rects:
                    props = {k: v for k, v in rect.items() if k not in ['x0', 'y0', 'x1', 'y1', 'page_number']}
                    
                    data.append({
                        'page_number': page_num,
                        'element_type': 'rect',
                        'x0': rect.get('x0'),
                        'y0': rect.get('y0'),
                        'x1': rect.get('x1'),
                        'y1': rect.get('y1'),
                        'properties': json.dumps(props)
                    })
                
                # Extract Text
                # page.extract_words() gives detailed info about each word including position
                # pdfplumber uses 'top' and 'bottom' as distance from top of page.
                # We convert to PDF standard (Bottom-Left origin).
                page_height = page.height
                words = page.extract_words(extra_attrs=['fontname', 'size'])
                for word in words:
                    props = {
                        'text': word.get('text'),
                        'fontname': word.get('fontname'),
                        'size': word.get('size')
                    }
                    
                    # Convert to Bottom-Left origin
                    # y0 (bottom of text) = page_height - word['bottom']
                    # y1 (top of text) = page_height - word['top']
                    
                    y0 = page_height - word.get('bottom')
                    y1 = page_height - word.get('top')
                    
                    data.append({
                        'page_number': page_num,
                        'element_type': 'text',
                        'x0': word.get('x0'),
                        'y0': y0,
                        'x1': word.get('x1'),
                        'y1': y1,
                        'properties': json.dumps(props)
                    })
                    
                # Extract Curves/Other paths if needed (pdfplumber puts these in .curves, but often lines cover most CAD)
                # Adding curves just in case
                for curve in page.curves:
                     props = {k: v for k, v in curve.items() if k not in ['x0', 'y0', 'x1', 'y1', 'page_number']}
                     data.append({
                        'page_number': page_num,
                        'element_type': 'curve',
                        'x0': curve.get('x0'),
                        'y0': curve.get('y0'),
                        'x1': curve.get('x1'),
                        'y1': curve.get('y1'),
                        'properties': json.dumps(props)
                    })

        if not data:
            print("No vector data found in the PDF.")
            return

        df = pd.DataFrame(data)
        df.to_csv(output_csv, index=False)
        print(f"Extraction complete. Data saved to {output_csv}")
        print(f"Total elements extracted: {len(df)}")

    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract vector data (lines, rects, text) from PDF to CSV.")
    parser.add_argument("pdf_file", help="Path to the input PDF file")
    parser.add_argument("--output", "-o", default="output_data.csv", help="Path to the output CSV file")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_file):
        print(f"Error: File '{args.pdf_file}' not found.")
        sys.exit(1)
        
    extract_vector_data(args.pdf_file, args.output)
