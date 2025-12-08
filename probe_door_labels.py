import fitz

def probe_d_labels():
    doc = fitz.open("sample.pdf")
    page = doc[0]
    text = page.get_text("dict")
    
    d_count = 0
    print("Searching for 'D' labels...")
    
    for block in text["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    txt = span["text"].strip()
                    # Check for "D" or "D" followed by numbers (e.g. D1, D-1)
                    if txt.startswith("D") and len(txt) < 5: 
                        print(f"Found Label: '{txt}' at {span['bbox']}")
                        d_count += 1
                        
    print(f"\nTotal potential Door labels found: {d_count}")

if __name__ == "__main__":
    probe_d_labels()
