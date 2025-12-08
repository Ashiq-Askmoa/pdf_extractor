import fitz

def dump_all_text():
    doc = fitz.open("sample.pdf")
    page = doc[0]
    text_dict = page.get_text("dict")
    
    all_text = []
    for block in text_dict["blocks"]:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    all_text.append(span["text"])
                    
    print(f"Total Text Items: {len(all_text)}")
    print("--- Content Dump ---")
    print(all_text)

if __name__ == "__main__":
    dump_all_text()
