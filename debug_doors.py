import fitz
from math import sqrt, isclose

def analyze_doors():
    doc = fitz.open("sample.pdf")
    page = doc[0]
    
    # 1. Text Analysis
    print("--- Analyzing Text for 'D' patterns ---")
    text_blocks = page.get_text("dict")["blocks"]
    d_labels = []
    for b in text_blocks:
        if b["type"] == 0:
            for l in b["lines"]:
                for s in l["spans"]:
                    txt = s["text"].strip()
                    if "D" in txt:
                        # Print context for any D found
                        print(f"Found 'D': '{txt}'")
                        
    # 2. Geometry Connectivity Analysis
    print("\n--- Analyzing Geometry (Arc + Line Connection) ---")
    shapes = page.get_drawings()
    
    arcs = []
    lines = []
    
    # Pre-classify
    for shape in shapes:
        width = shape.get('width', 0) or 0
        if 'items' not in shape: continue
        
        for item in shape['items']:
            op = item[0]
            if op == 'c': # Curve
                # Check heuristic (width < 0.70)
                if width < 0.70:
                    # item is ('c', p1, p2, p3, p4)
                    arcs.append((item[1], item[4])) # Start, End
            elif op == 'l':
                lines.append((item[1], item[2], width)) # Start, End, Width
                
    print(f"Found {len(arcs)} candidate Door Arcs.")
    print(f"Found {len(lines)} total Lines.")
    
    # Check Connectivity
    connected_count = 0
    tolerance = 1.0 # 1 unit tolerance
    
    for (a_start, a_end) in arcs:
        # A door leaf usually connects to one end of the arc
        found_connection = False
        for (l_start, l_end, l_width) in lines:
            # Check p1
            if (abs(l_start.x - a_start.x) < tolerance and abs(l_start.y - a_start.y) < tolerance) or \
               (abs(l_end.x - a_start.x) < tolerance and abs(l_end.y - a_start.y) < tolerance) or \
               (abs(l_start.x - a_end.x) < tolerance and abs(l_start.y - a_end.y) < tolerance) or \
               (abs(l_end.x - a_end.x) < tolerance and abs(l_end.y - a_end.y) < tolerance):
                
                # Check if this line looks like a door leaf (similar width to arc?)
                if l_width < 0.70:
                    found_connection = True
                    break
        
        if found_connection:
            connected_count += 1
            
    print(f"Arcs connected to at least one thin line: {connected_count}")

if __name__ == "__main__":
    analyze_doors()
