import fitz

def check_ocg_presence(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    shapes = page.get_drawings()
    
    count_with_ocg = 0
    unique_ocgs = set()
    
    for shape in shapes:
        ocg = shape.get('ocg')
        if ocg:
            count_with_ocg += 1
            unique_ocgs.add(ocg)
            
    print(f"Total Shapes: {len(shapes)}")
    print(f"Shapes with OCG: {count_with_ocg}")
    print(f"Unique OCGs found: {unique_ocgs}")

if __name__ == "__main__":
    check_ocg_presence("sample.pdf")
