# PDF Vector Data Extractor & Reconstructor

This project provides tools to extract vector data (lines, rectangles, text) from PDF files into CSV format, and conversely, reconstruct PDF files from that CSV data. This is particularly useful for analyzing or modifying 2D design layouts like floor plans.

## Features

- **Extraction**: Extracts lines, rectangles, and text with their properties (coordinates, color, font, size) from a PDF.
- **Reconstruction**: Generates a PDF file from the extracted CSV data, preserving the layout and vector elements.
- **Coordinate Standardization**: Handles coordinate system differences between PDF libraries to ensure correct placement (Bottom-Left origin).

## Installation

1.  **Prerequisites**: Python 3.11 or higher.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### 1. Extract Vector Data (PDF to CSV)

Use the `extract_vector_pdf_data.py` script to parse a PDF file.

```bash
python3 extract_vector_pdf_data.py <path_to_pdf> [-o output.csv]
```

**Example:**
```bash
python3 extract_vector_pdf_data.py sample_floor_plan.pdf
```
This will generate `output_data.csv` containing the vector elements.

### 2. Reconstruct PDF (CSV to PDF)

Use the `csv_to_pdf.py` script to generate a PDF from the CSV data.

```bash
python3 csv_to_pdf.py <path_to_csv> [-o output.pdf]
```

**Example:**
```bash
python3 csv_to_pdf.py output_data.csv
```
This will create `reconstructed_pdf.pdf`.

## CSV Structure

The output CSV contains the following columns:
- `page_number`: Page number (1-based).
- `element_type`: Type of element (`line`, `rect`, `text`, `curve`).
- `x0`, `y0`, `x1`, `y1`: Bounding box or start/end coordinates (PDF Bottom-Left origin).
- `properties`: JSON string containing additional attributes like color, stroke width, font name, and text content.

## Notes

- The extraction script standardizes text coordinates to the PDF standard (Bottom-Left origin) to ensure compatibility with the reconstruction script and other PDF tools.
- If you encounter `ModuleNotFoundError`, ensure you are running the script with the python version where dependencies were installed (e.g., `python3.11`).
