import fitz
from collections import Counter

def analyze_widths(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    shapes = page.get_drawings()
    
    widths = []
    types = []
    
    for shape in shapes:
        # Check stroke width
        w = shape.get('width')
        if w is not None:
            widths.append(round(w, 2))
        types.append(shape.get('type'))
            
    print(f"Total Shapes: {len(shapes)}")
    print("Shape Types:", Counter(types))
    print("Top 20 Line Widths:", Counter(widths).most_common(20))

if __name__ == "__main__":
    analyze_widths("sample.pdf")
