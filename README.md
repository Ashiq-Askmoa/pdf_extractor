# PDF Floor Plan Feature Extractor

This project provides a suite of Python tools to extract, quantify, and visualize architectural features (Walls, Doors, Windows, Sanitary Fixtures) from vector-based Floor Plan PDFs.

It differs from standard OCR tools by using **Geometric Heuristics** and **Vector Analysis** to identify features even when standard PDF layers (OCGs) are missing or unstructured.

## Key Features

*   **Geometric Classification**: Identifies features based on line width, shape (curves vs. lines), and connectivity.
    *   **Walls**: Thick lines ($\ge$ 0.70 units).
    *   **Windows**: Thin detailed lines (< 0.25 units).
    *   **Doors**: Intelligent detection connecting Swing Arcs + Door Leaf Lines + Text Labels.
    *   **Sanitary**: Detects Basins (small geometric loops) and WCs (text labels).
*   **Text Extraction**: captures all text and specific labels (Room Names, Appliance Codes).
*   **Layer Regeneration**: Can re-draw specific features onto clean new PDFs.

## Prerequisites

*   Python 3.8+
*   Virtual Environment (Recommended)

### Dependencies
Install the required packages:
```bash
pip install pymupdf pandas openpyxl
```

## Scripts & Usage

### 1. Main Feature Extraction
**Script:** `extract_pdf_data.py`

Analyzes the PDF and generates a comprehensive Excel report.

*   **Output:** `blueprint_quantities.xlsx`
    *   **Summary**: Aggregated counts and lengths.
    *   **Detailed Features**: A list of >80,000 extracted items with Bounding Box coordinates.
    *   **All Text**: Complete text dump.

```bash
python3 extract_pdf_data.py
```

### 2. Layer Separation (Excel)
**Script:** `extract_layers.py`

Organizes the extracted data into separate Excel sheets for easier manual review.

*   **Output:** `separated_quantities.xlsx`
    *   Contains individual tabs for `Wall`, `Door`, `Window_Detail`, `Sanitary`, etc.

```bash
python3 extract_layers.py
```

### 3. Layer Visualization (PDF Generator)
**Script:** `generate_layer_pdf.py`

Re-draws the extracted geometry onto new, clean PDF files. This is useful for visually verifying what the script has detected.

*   **Features:**
    *   **Intelligent Door Binding**: Automatically links independent arc and line segments to reconstruct full doors.
    *   **Visibility Enhancement**: Enforces minimum line widths so thin features remain visible.
*   **Output Directory:** `generated_layers/`
    *   `layer_Wall.pdf`
    *   `layer_Door.pdf`
    *   `layer_Sanitary_Basin.pdf`
    *   ...and more.

```bash
python3 generate_layer_pdf.py
```

## Heuristics Configuration

The classification logic is consistent across all scripts. Key thresholds (in PDF units):

*   **Wall Threshold**: Width $\ge$ 0.70
*   **Window Threshold**: Width < 0.25 (and > 0)
*   **Door Detection**:
    *   **Geometry**: Curve/Arc segments. straight lines touching arcs are promoted to "Door".
    *   **Text**: Labels starting with `D-`, `HVD-`, `VVD-`, `YDS-` or containing `BASTUDÖRR`.
*   **Basin Detection**: Closed geometric loops with perimeter between 10-200 units.

## Troubleshooting

*   **"No module named fitz"**: Ensure you installed `pymupdf` (not `fitz`).
*   **Invisible Output in PDF**: The `generate_layer_pdf.py` script automatically boosts line width to 0.5. If features are still missing, check the `analyze_widths.py` tool (if available) to see the distribution of line weights in your specific PDF.
