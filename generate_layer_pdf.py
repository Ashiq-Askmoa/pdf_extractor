#!/Users/alimran/Documents/pdf_extractor/venv/bin/python3
import fitz # PyMuPDF
import os
from math import sqrt

# --- Configuration ---
PDF_FILE = "sample.pdf"
OUTPUT_DIR = "generated_layers"

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- Geometry Binding Logic ---
def classify_geometry_two_pass(shapes):
    """
    Performs advanced classification linking lines to curves.
    Returns: Dict {Category: [List of Shapes]}
    """
    
    categorized_shapes = {
        "Wall": [],
        "Door": [],
        "Window_Detail": [],
        "Sanitary_Basin": [],
        "Standard_Line": [],
        "Other": []
    }
    
    # Pass 1: Initial Heuristics & Identify Door Arcs
    door_arcs = [] # (StartPoint, EndPoint, ShapeObject)
    
    # Temporary container for line candidates that might be doors
    line_candidates = [] 
    
    for shape in shapes:
        shape_type = shape.get('type')
        width = shape.get('width', 0)
        if width is None: width = 0
        
        # Calculate Length & Check Curve
        length = 0.0
        is_curve = False
        is_closed = False
        start_p = None
        end_p = None
        
        if shape_type == 's' and 'items' in shape:
            for i, item in enumerate(shape['items']):
                op = item[0]
                if op == 'l':
                    p1, p2 = item[1], item[2]
                    length += sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
                    if i == 0: start_p = p1
                    end_p = p2
                elif op == 'c':
                    is_curve = True
                    p1, p4 = item[1], item[4]
                    length += sqrt((p4.x - p1.x)**2 + (p4.y - p1.y)**2)
                    if i == 0: start_p = p1
                    end_p = p4
            
            if start_p and end_p and abs(start_p.x - end_p.x) < 1 and abs(start_p.y - end_p.y) < 1:
                is_closed = True

        elif shape_type == 'r':
            rect = shape.get('rect')
            length = 2 * (abs(rect[2]-rect[0]) + abs(rect[3]-rect[1]))

        # --- Initial Classification ---
        if is_curve and is_closed and length < 200 and length > 10:
            categorized_shapes["Sanitary_Basin"].append(shape)
            
        elif width >= 0.70:
            categorized_shapes["Wall"].append(shape)
            
        elif is_curve and width < 0.70:
            # Found a Door Arc!
            categorized_shapes["Door"].append(shape)
            if start_p and end_p:
                door_arcs.append((start_p, end_p))
                
        elif width > 0 and width < 0.25:
            categorized_shapes["Window_Detail"].append(shape)
            
        elif width >= 0.25 and width < 0.70:
            # Candidate for Door Leaf (if connected to arc) OR Standard Line
            line_candidates.append(shape)
        else:
             categorized_shapes["Other"].append(shape)

    # Pass 2: Check Line Candidates against Door Arcs
    print(f"  [Pass 2] Checking {len(line_candidates)} lines against {len(door_arcs)} door arcs...")
    
    tolerance = 1.0
    
    for shape in line_candidates:
        # Get start/end of this line shape
        s_start = None
        s_end = None
        if shape['type'] == 's' and 'items' in shape:
            # Assuming simple lines for door leaves (usually single segment)
            item = shape['items'][0] 
            if item[0] == 'l':
                s_start = item[1]
                s_end = item[2]
        
        is_door_leaf = False
        if s_start and s_end:
            for (a_start, a_end) in door_arcs:
                 if (abs(s_start.x - a_start.x) < tolerance and abs(s_start.y - a_start.y) < tolerance) or \
                    (abs(s_end.x - a_start.x) < tolerance and abs(s_end.y - a_start.y) < tolerance) or \
                    (abs(s_start.x - a_end.x) < tolerance and abs(s_start.y - a_end.y) < tolerance) or \
                    (abs(s_end.x - a_end.x) < tolerance and abs(s_end.y - a_end.y) < tolerance):
                     is_door_leaf = True
                     break
        
        if is_door_leaf:
            categorized_shapes["Door"].append(shape)
        else:
            categorized_shapes["Standard_Line"].append(shape)

    return categorized_shapes

# --- Text Classification ---
def extract_categorized_text(page):
    text = page.get_text("dict")
    categorized_text = {}
    
    keywords = {
        "WC": "Sanitary_Toilet_WC", 
        "TM": "Appliance_Washing_Machine",
        "TT": "Appliance_Tumble_Dryer",
        "DM": "Appliance_Dishwasher", 
        "Dusch": "Sanitary_Shower"
    }

    for block in text["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    cat = None
                    
                    # 1. Expanded Door Labels
                    if (txt.startswith("D-") or 
                        txt.startswith("DBD-") or 
                        txt.startswith("HVD-") or 
                        txt.startswith("VVD-") or 
                        txt.startswith("YDS-") or 
                        "BASTUDÖRR" in txt):
                        cat = "Door"
                    
                    # 2. Check Keywords
                    if not cat:
                        for key, val in keywords.items():
                            if key == txt or f" {key} " in f" {txt} ":
                                cat = val
                                break
                    
                    if cat:
                        if cat not in categorized_text:
                            categorized_text[cat] = []
                        categorized_text[cat].append({
                            "text": txt,
                            "bbox": span["bbox"],
                            "size": span["size"],
                            "font": span["font"]
                        })
    return categorized_text

# --- PDF Generation Logic ---
def generate_layer_pdfs():
    if not os.path.exists(PDF_FILE):
        print(f"Error: {PDF_FILE} not found.")
        return

    print(f"Reading {PDF_FILE}...")
    doc = fitz.open(PDF_FILE)
    src_page = doc[0]
    src_rect = src_page.rect 
    
    # 1. Advanced Geometry Classification
    shapes = src_page.get_drawings()
    print(f"Classifying {len(shapes)} elements (Two-Pass Logic)...")
    categorized_shapes = classify_geometry_two_pass(shapes)
        
    # 2. Extract Categorized Text
    categorized_text = extract_categorized_text(src_page)
    
    doc.close()
    
    # 3. Generate PDF for each category
    print("\nGenerating Layer PDFs...")
    
    all_categories = set(categorized_shapes.keys()).union(set(categorized_text.keys()))
    
    for cat in all_categories:
        shape_list = categorized_shapes.get(cat, [])
        text_list = categorized_text.get(cat, [])
        
        if not shape_list and not text_list: continue

        # Create new PDF
        out_pdf = fitz.open()
        out_page = out_pdf.new_page(width=src_rect.width, height=src_rect.height)
        
        # A. Draw Shapes
        draw_count = 0
        if shape_list:
            shape_drawer = out_page.new_shape()
            for s in shape_list:
                w = s.get('width')
                width_val = float(w) if w is not None else 0.5
                stroke_width = max(width_val, 0.5) 
                stroke_color = (0, 0, 0)
                
                if 'items' in s:
                    for item in s['items']:
                        op = item[0]
                        if op == 'l':
                            shape_drawer.draw_line(item[1], item[2])
                        elif op == 'c':
                            shape_drawer.draw_bezier(item[1], item[2], item[3], item[4])
                    shape_drawer.finish(width=stroke_width, color=stroke_color, stroke_opacity=1)
                elif s['type'] == 'r':
                    rect = fitz.Rect(s['rect'])
                    shape_drawer.draw_rect(rect)
                    shape_drawer.finish(width=stroke_width, color=stroke_color, stroke_opacity=1)
                draw_count += 1
            shape_drawer.commit()

        # B. Draw Text
        text_count = 0
        if text_list:
            for t in text_list:
                p = fitz.Point(t["bbox"][0], t["bbox"][3]) 
                out_page.insert_text(p, t["text"], fontsize=t["size"], color=(0, 0, 1)) 
                text_count += 1
        
        filename = f"layer_{cat}.pdf"
        filepath = os.path.join(OUTPUT_DIR, filename)
        out_pdf.save(filepath)
        out_pdf.close()
        
        print(f"  -> Generated {filename} ({draw_count} shapes, {text_count} labels)")

    print(f"\nAll files saved to folder: {os.path.abspath(OUTPUT_DIR)}")

if __name__ == "__main__":
    generate_layer_pdfs()
