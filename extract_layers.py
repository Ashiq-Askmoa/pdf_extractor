#!/Users/alimran/Documents/pdf_extractor/venv/bin/python3
import fitz # PyMuPDF
import pandas as pd
from math import sqrt, inf
import os

# --- Configuration ---
PDF_FILE = "sample.pdf"
SEPARATED_FILE = "separated_quantities.xlsx"

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
    
    start_p = None
    end_p = None
    
    if shape_type == 's' and 'items' in shape: # Stroke path
        items = shape['items']
        
        for i, item in enumerate(items):
            operator = item[0]
            
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
                is_curve = True
                p1, p4 = item[1], item[4] 
                p2, p3 = item[2], item[3]
                seg_len = sqrt((p4.x - p1.x)**2 + (p4.y - p1.y)**2)
                length += seg_len
                if i == 0: start_p = p1
                end_p = p4
                for p in [p1, p2, p3, p4]:
                    update_bbox(p)
        
        if start_p and end_p and abs(start_p.x - end_p.x) < 1 and abs(start_p.y - end_p.y) < 1:
             is_closed = True

    elif shape_type == 'r': # Rectangle
        rect = shape.get('rect')
        min_x, min_y, max_x, max_y = rect[0], rect[1], rect[2], rect[3]
        width_r = max_x - min_x
        height_r = max_y - min_y
        length = 2 * (abs(width_r) + abs(height_r)) 
        
    if min_x == inf:
        min_x, min_y, max_x, max_y = 0, 0, 0, 0
        
    bbox = (min_x, min_y, max_x, max_y)
        
    # --- CLASSIFICATION LOGIC ---
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
                    
                    # 1. Check for Door Labels (D-..., DBD-...)
                    # Expanded patterns based on analysis: HVD, VVD, YDS, BASTUDÖRR
                    if (txt.startswith("D-") or 
                        txt.startswith("DBD-") or 
                        txt.startswith("HVD-") or 
                        txt.startswith("VVD-") or 
                        txt.startswith("YDS-") or 
                        "BASTUDÖRR" in txt):
                        
                        features.append({
                            "Category": "Door (Label)",
                            "Text": txt,
                            "X": round(block['bbox'][0], 2),
                            "Y": round(block['bbox'][1], 2),
                            "Length": 0
                        })
                        continue # Found a label, skip keywords check
                        
                    # 2. Check Keywords
                    for key, cat in keywords.items():
                        if key == txt or f" {key} " in f" {txt} ":
                            features.append({
                                "Category": cat,
                                "Text": txt,
                                "X": round(block['bbox'][0], 2),
                                "Y": round(block['bbox'][1], 2),
                                "Length": 0
                            })
                            break 
    return features

# --- Main Extraction ---
def main():
    if not os.path.exists(PDF_FILE):
        print(f"Error: {PDF_FILE} not found.")
        return

    print(f"Analyzing {PDF_FILE} for Layer Extraction...")
    doc = fitz.open(PDF_FILE)
    page = doc[0]
    
    detailed_features = []
    
    # 1. Shape Extraction
    shapes = page.get_drawings()
    for shape in shapes:
        length, category, bbox = quantify_shape(shape)
        detailed_features.append({
            "Category": category,
            "Type": "Geometry",
            "Length": round(length, 2),
            "X_Min": round(bbox[0], 2),
            "Y_Min": round(bbox[1], 2),
            "X_Max": round(bbox[2], 2),
            "Y_Max": round(bbox[3], 2)
        })
        
    # 2. Text Feature Extraction
    text_feats = extract_text_features(page)
    for feat in text_feats:
        detailed_features.append({
            "Category": feat["Category"],
            "Type": "Text Label",
            "Length": 0,
            "X_Min": feat["X"],
            "Y_Min": feat["Y"],
            "X_Max": feat["X"],
            "Y_Max": feat["Y"]
        })
            
    doc.close()
    
    # --- Sort and Save Separated Sheets ---
    df_detailed = pd.DataFrame(detailed_features)
    df_detailed = df_detailed.sort_values(by=['Category', 'Y_Min'])
    
    print(f"Saving separate sheets to {SEPARATED_FILE}...")
    
    with pd.ExcelWriter(SEPARATED_FILE, engine='openpyxl') as writer:
        categories = df_detailed['Category'].unique()
        
        for cat in categories:
            df_cat = df_detailed[df_detailed['Category'] == cat]
            
            # Sanitize sheet name (Max 31 chars)
            sheet_name = str(cat).replace(":", "").replace("/", "_").strip()[:30]
            
            df_cat.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"  - Sheet: {sheet_name} ({len(df_cat)} rows)")
            
    print(f"\nSaved successfully to {os.path.abspath(SEPARATED_FILE)}")

if __name__ == "__main__":
    main()
