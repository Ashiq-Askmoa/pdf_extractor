import fitz

def debug_keys(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]
    shapes = page.get_drawings()
    
    if len(shapes) > 0:
        print("First Shape Keys:", shapes[0].keys())
        print("First Shape Type:", shapes[0].get('type'))
        if 'items' in shapes[0]:
            print("First Shape 'items' (first 2):", shapes[0]['items'][:2])
        if 'path' in shapes[0]:
            print("First Shape 'path':", shapes[0]['path'])
            
    # Find a shape with type 's' if first one isn't
    for s in shapes:
        if s['type'] == 's':
            print("Found 's' shape keys:", s.keys())
            if 'items' in s:
                print("'items' sample:", s['items'][:1])
            if 'path' in s:
                print("'path' sample:", s['path'][:1])
            break

if __name__ == "__main__":
    debug_keys("sample.pdf")
