import fitz
import sys

def probe_layers(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        print(f"File: {pdf_path}")
        
        # Check for OCGs (Optional Content Groups) which map to layers
        ocgs = doc.get_ocgs()
        if not ocgs:
            print("No Optional Content Groups (Layers) found.")
        else:
            print(f"Found {len(ocgs)} Layers:")
            for xref, name in ocgs.items():
                print(f"  ID: {xref}, Name: {name}")
                
    except Exception as e:
        print(f"Error: {e}")
        # Fallback to simple print if items() fails (depends on version)
        print("Raw OCGs:", doc.get_ocgs())

if __name__ == "__main__":
    probe_layers("sample.pdf")
