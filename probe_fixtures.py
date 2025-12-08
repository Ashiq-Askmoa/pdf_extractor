import fitz

def probe_features(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    print("--- Text Analysis ---")
    text = page.get_text("dict")
    # Search for keywords
    keywords = ["WC", "Kök", "Bad", "Tvätt", "TM", "TT", "KM", "G", "L", "ST", "DM", "Dusch"]
    found_keywords = []
    
    for block in text["blocks"]:
        # Only process text blocks (type 0)
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    # Check for exact matches or presence in string if short
                    if txt in keywords or any(f" {k} " in f" {txt} " for k in keywords):
                        found_keywords.append(txt)
                    
    print(f"Found Keywords: {set(found_keywords)}")
    print(f"Total Text Blocks: {len(text['blocks'])}")
    
    print("\n--- XObject Analysis (Reusable Blocks) ---")
    xobjects = page.get_xobjects()
    if xobjects:
         print(f"Found {len(xobjects)} XObjects.")
         for obj in xobjects:
             print(f"  {obj}")
    else:
        print("No XObjects found (Features likely drawn as raw paths).")
        
    print("\n--- Circle/Oval Analysis (Potential Basins) ---")
    shapes = page.get_drawings()
    circles = 0
    for shape in shapes:
        # Check for circles/ellipses (often 'c' path closing on itself or specific sequence)
        # Simplified check: just count curves
        for item in shape.get('items', []):
             if item[0] == 'c':
                 circles += 1
    print(f"Total Curve Segments found: {circles}")

if __name__ == "__main__":
    probe_features("sample.pdf")
