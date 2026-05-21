import fitz  # PyMuPDF

def pdf_to_high_res_png(pdf_path, output_path, zoom_factor=4):
    # Open the PDF document
    doc = fitz.open(pdf_path)
    
    # Load the specific page (0 is the first page)
    page = doc.load_page(0) 
    
    # Create a transformation matrix. 
    # A zoom factor of 4 roughly equals 300 DPI. 
    # Increase to 8 or 12 for extreme resolutions.
    mat = fitz.Matrix(zoom_factor, zoom_factor)
    
    # Render the page to an image (pixmap)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    # Save as PNG
    pix.save(output_path)
    print(f"Saved highly-resolved image to {output_path}")

# Run the function
pdf_to_high_res_png(r"Python\growthregime.pdf", "growthregime.png", zoom_factor=14)

