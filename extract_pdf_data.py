#!/Users/alimran/Documents/pdf_extractor/venv/bin/python3
import fitz # PyMuPDF
import pandas as pd
from math import sqrt, inf
import os

# --- Configuration ---
PDF_FILE = "sample.pdf"
EXCEL_FILE = "blueprint_quantities.xlsx"

# --- Utility: Quantify Shape ---
def quantify_shape(shape):
    """
    Analyzes a shape to determine its length, classification, and bounding box.
    Returns: (length, category, bbox) where bbox is (min_x, min_y, max_x, max_y)
    """
    shape_type = shape.get('type')
    width = shape.get('width', 0)
    if width is None: width = 0
    
    category = "Other"
    length = 0.0
    
    # Initialize BBox
    min_x, min_y = inf, inf
    max_x, max_y = -inf, -inf
    
    # Check for Curves (Doors/Basins)
    is_curve = False
    is_closed = False 
    
    # Start/End points for loop detection
    start_p = None
    end_p = None
    
    if shape_type == 's' and 'items' in shape: # Stroke path
        items = shape['items']
        
        for i, item in enumerate(items):
            operator = item[0]
            
            # Helper to update bbox with a point
            def update_bbox(p):
                nonlocal min_x, min_y, max_x, max_y
                if p.x < min_x: min_x = p.x
                if p.y < min_y: min_y = p.y
                if p.x > max_x: max_x = p.x
                if p.y > max_y: max_y = p.y

            if operator == 'l':
                p1, p2 = item[1], item[2]
                seg_len = sqrt((p2.x - p1.x)**2 + (p2.y - p1.y)**2)
                length += seg_len
                if i == 0: start_p = p1
                end_p = p2
                update_bbox(p1)
                update_bbox(p2)
                
            elif operator == 'c':
                # Curve: ("c", p1, p2, p3, p4)
                is_curve = True
                p1, p4 = item[1], item[4] 
                # Control points p2, p3 also define the curve's extent, but p1/p4 are anchors
                # For simplicity in bbox, we include p2/p3 too
                p2, p3 = item[2], item[3]
                
                seg_len = sqrt((p4.x - p1.x)**2 + (p4.y - p1.y)**2)
                length += seg_len
                if i == 0: start_p = p1
                end_p = p4
                for p in [p1, p2, p3, p4]:
                    update_bbox(p)
        
        # Check for simple closure
        if start_p and end_p and abs(start_p.x - end_p.x) < 1 and abs(start_p.y - end_p.y) < 1:
             is_closed = True

    elif shape_type == 'r': # Rectangle
        rect = shape.get('rect')
        # rect is [x0, y0, x1, y1]
        min_x, min_y, max_x, max_y = rect[0], rect[1], rect[2], rect[3]
        
        width_r = max_x - min_x
        height_r = max_y - min_y
        length = 2 * (abs(width_r) + abs(height_r)) 
        
    # Handle case where no points found (shouldn't happen for valid shapes)
    if min_x == inf:
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        
    bbox = (min_x, min_y, max_x, max_y)
        
    # --- CLASSIFICATION LOGIC ---
    
    # BASIN HEURISTIC
    is_basin = False
    if is_curve and is_closed and length < 200 and length > 10: 
        is_basin = True
        category = "Sanitary: Wash Basin (Est.)"

    elif width >= 0.70:
        category = "Wall"
    
    elif is_curve and width < 0.70 and not is_basin:
        category = "Door (Swing)"
        
    elif width > 0 and width < 0.25:
        category = "Window/Detail"
        
    elif width >= 0.25 and width < 0.70:
        category = "Standard Line"

    return length, category, bbox

# --- Utility: Extract Specific Text Features ---
def extract_text_features(page):
    """
    Scans text blocks for specific keywords.
    """
    text = page.get_text("dict")
    features = []
    
    keywords = {
        "WC": "Sanitary: Toilet/WC",
        "TM": "Appliance: Washing Machine",
        "TT": "Appliance: Tumble Dryer",
        "DM": "Appliance: Dishwasher",
        "KM": "Appliance: Combo Washer/Dryer",
        "Kök": "Room: Kitchen",
        "Bad": "Room: Bathroom", 
        "Dusch": "Sanitary: Shower"
    }
    
    for block in text["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    for key, cat in keywords.items():
                        if key == txt or f" {key} " in f" {txt} ":
                            features.append({
                                "Category": cat,
                                "Text": txt,
                                "X": round(block['bbox'][0], 2),
                                "Y": round(block['bbox'][1], 2),
                                "Length": 0
                            })
                            # Break inner loop to avoid double counting same text for different keys
                            break 
                            
    return features

# --- Utility: Extract ALL Text ---
def extract_all_text(page):
    text_data = []
    text_dict = page.get_text("dict")
    
    for block in text_dict["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    if txt:
                        text_data.append({
                            "Text": txt,
                            "Font": span.get("font", ""),
                            "Size": span.get("size", 0),
                            "X": round(span["bbox"][0], 2),
                            "Y": round(span["bbox"][1], 2)
                        })
    return text_data

# --- Main Extraction ---
def main():
    if not os.path.exists(PDF_FILE):
        print(f"Error: {PDF_FILE} not found.")
        return

    print(f"Analyzing {PDF_FILE}...")
    doc = fitz.open(PDF_FILE)
    page = doc[0]
    
    # Data Containers
    stats = {} 
    detailed_features = []
    
    # 1. Shape Extraction
    shapes = page.get_drawings()
    
    for shape in shapes:
        length, category, bbox = quantify_shape(shape)
        
        # Update Summary Stats
        if category not in stats:
            stats[category] = {"count": 0, "length": 0.0}
        stats[category]["count"] += 1
        stats[category]["length"] += length
        
        # Store Detailed Data
        detailed_features.append({
            "Category": category,
            "Type": "Geometry",
            "Length": round(length, 2),
            "X_Min": round(bbox[0], 2),
            "Y_Min": round(bbox[1], 2),
            "X_Max": round(bbox[2], 2),
            "Y_Max": round(bbox[3], 2)
        })
        
    # 2. Specific Feature Extraction (Text Based)
    text_feats = extract_text_features(page)
    for feat in text_feats:
        cat = feat["Category"]
        # Update Stats
        if cat not in stats:
             stats[cat] = {"count": 0, "length": 0.0}
        stats[cat]["count"] += 1
        
        # Store Detailed Data
        detailed_features.append({
            "Category": cat,
            "Type": "Text Label",
            "Length": 0,
            "X_Min": feat["X"],
            "Y_Min": feat["Y"],
            "X_Max": feat["X"], # Text location is a point for simplicity in this view
            "Y_Max": feat["Y"]
        })
            
    # 3. Extract ALL Text
    all_text = extract_all_text(page)
    print(f"Extracted {len(all_text)} text elements.")
    print(f"Extracted {len(detailed_features)} geometric/feature elements.")

    doc.close()
    
    # --- Output Results ---
    
    # Sheet 1: Summary Counts
    summary_results = []
    print("\nExtraction Summary:")
    print(f"{'Category':<30} | {'Count':<10} | {'Length':<20}")
    print("-" * 65)
    
    for cat in sorted(stats.keys()):
        data = stats[cat]
        print(f"{cat:<30} | {data['count']:<10} | {data['length']:<20.2f}")
        summary_results.append({
            "Category": cat,
            "Count": data['count'],
            "Total Length": data['length']
        })
        
    df_summary = pd.DataFrame(summary_results)
    df_detailed = pd.DataFrame(detailed_features)
    df_text = pd.DataFrame(all_text)
    
    # Sort detailed by Category for better readability
    df_detailed = df_detailed.sort_values(by=['Category', 'Y_Min'])
    
    # Save to Excel
    print("Saving to Excel (this might take a moment)...")
    with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        df_detailed.to_excel(writer, sheet_name='Detailed Features', index=False)
        df_text.to_excel(writer, sheet_name='All Text', index=False)
        
    print(f"\nSaved results to {os.path.abspath(EXCEL_FILE)}")
    print(" - 'Summary': Feature counts")
    print(" - 'Detailed Features': Coordinates for every wall, door, etc.")
    print(" - 'All Text': Complete text extraction")

if __name__ == "__main__":
    main()