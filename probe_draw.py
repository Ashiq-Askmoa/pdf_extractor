import fitz

def check_api():
    print(f"PyMuPDF Version: {fitz.VersionBind}")
    shape = fitz.open().new_page().new_shape()
    
    # Check signature via help or try/except
    print("\nChecking draw_bezier signature...")
    try:
        # Try 4 args (p1, p2, p3, p4)
        shape.draw_bezier((0,0), (10,10), (20,20), (30,30))
        print("Success: draw_bezier accepts 4 arguments (start, cp1, cp2, end)?")
    except Exception as e:
        print(f"Failed 4 args: {e}")
        
    try:
        # Try 3 args (cp1, cp2, end) - implying current point
        shape.draw_bezier((10,10), (20,20), (30,30))
        print("Success: draw_bezier accepts 3 arguments (cp1, cp2, end)?")
    except Exception as e:
        print(f"Failed 3 args: {e}")

    # Check move_to
    if hasattr(shape, 'draw_line'): print("Has draw_line")
    if hasattr(shape, 'move_to'): print("Has move_to")
    if hasattr(shape, 'draw_move'): print("Has draw_move")

if __name__ == "__main__":
    check_api()
