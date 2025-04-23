import os
import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
import pdfplumber
from PIL import Image
import fitz  # PyMuPDF
import tempfile
import sys
import io
from fpdf import FPDF
from contextlib import contextmanager

st.set_page_config(page_title="OCR PDF Extractor", layout="centered")
st.title("📄 OCR PDF Extractor (No GPU Needed)")
st.write("Upload scanned or text-based PDFs. This app extracts and displays the text.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    poppler_path = st.text_input("Poppler Path (optional)", 
                               placeholder="e.g., C:\\poppler\\bin",
                               help="Path to Poppler binaries if not in system PATH")
    
    # Check for Tesseract installation
    tesseract_path = st.text_input("Tesseract Path (optional)",
                                 placeholder="e.g., C:\\Program Files\\Tesseract-OCR",
                                 help="Path to Tesseract executable if not in system PATH")
    
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = os.path.join(tesseract_path, 'tesseract.exe') \
            if not os.path.isfile(tesseract_path) else tesseract_path
    
    # Additional options
    st.subheader("OCR Options")
    ocr_dpi = st.slider("DPI for OCR", min_value=72, max_value=600, value=300, 
                      help="Higher DPI may improve OCR accuracy but uses more memory")
    ocr_lang = st.selectbox("OCR Language", 
                          options=["eng", "fra", "deu", "spa", "ita", "por", "chi_sim", "jpn", "kor"],
                          index=0,
                          help="Select language for OCR")
    
    fallback_all_pages = st.checkbox("Force OCR on all pages", 
                                  value=False, 
                                  help="Use OCR for all pages, even when text is extractable")

# Error handling wrapper
@contextmanager
def error_handling(stage_name):
    try:
        yield
    except Exception as e:
        st.error(f"⚠️ Error during {stage_name}: {str(e)}")
        st.info("Try adjusting the settings in the sidebar or try another PDF.")
        return None

# Check for Poppler installation
def is_poppler_installed(custom_path=None):
    try:
        from pdf2image.exceptions import PDFInfoNotInstalledError
        test_file = os.path.join(tempfile.gettempdir(), "test.pdf")
        with open(test_file, "wb") as f:
            f.write(b"%PDF-1.7\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%EOF\n")
        convert_from_bytes(open(test_file, "rb").read(), dpi=200, first_page=1, last_page=1, 
                          poppler_path=custom_path)
        os.remove(test_file)
        return True
    except Exception:
        return False

# Create PDF from extracted text
def create_pdf_from_text(text, title="Extracted Text"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Add title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    pdf.ln(10)
    
    # Add text content
    pdf.set_font("Arial", size=12)
    
    # Split text into lines and add to PDF
    lines = text.split('\n')
    for line in lines:
        # Handle very long lines
        if len(line) > 0:
            # Encode special characters
            try:
                pdf.multi_cell(0, 5, txt=line)
            except Exception:
                # If encoding issues, try to clean the text
                pdf.multi_cell(0, 5, txt="[Content with special characters removed]")
    
    return pdf.output(dest="S").encode('latin-1')

uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

if uploaded_file:
    st.info("Processing PDF... Please wait ⏳")

    extracted_text = ""
    file_bytes = uploaded_file.read()
    page_count = 0
    
    # Save temporarily for processing
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(file_bytes)
        tmp_pdf_path = tmp_file.name
    
    # Try to get page count
    try:
        with fitz.open(tmp_pdf_path) as doc:
            page_count = len(doc)
            st.info(f"PDF has {page_count} pages")
    except Exception as e:
        st.warning(f"Could not determine page count: {str(e)}")
    
    # Process with different methods based on settings
    if not fallback_all_pages:
        # First try pdfplumber (for text-based PDFs)
        with st.spinner("Trying text-based extraction..."):
            try:
                with pdfplumber.open(tmp_pdf_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        page_text = page.extract_text() or ""
                        if page_text.strip():
                            extracted_text += f"\n--- Page {i+1} ---\n{page_text}"
                
                if len(extracted_text.strip()) > 100:
                    st.success("✅ Text-based extraction successful!")
            except Exception as e:
                st.warning(f"Text-based extraction error: {str(e)}")
                extracted_text = ""  # Reset if failed
    
    # If little or no text or forced OCR, use OCR
    if len(extracted_text.strip()) < 100 or fallback_all_pages:
        st.warning("Text-based extraction failed or forced OCR. Switching to OCR mode 📸")
        
        # Check if Poppler is installed before attempting OCR
        poppler_installed = is_poppler_installed(poppler_path if poppler_path else None)
        
        if not poppler_installed:
            st.error("""
            ❌ Poppler is not installed or not in PATH. OCR cannot proceed.
            
            To install Poppler:
            
            1. Download Poppler for Windows from: https://github.com/oschwartz10612/poppler-windows/releases/
            2. Extract the ZIP file to a folder (e.g., C:\\poppler)
            3. Either:
               - Add the bin directory to your PATH (e.g., C:\\poppler\\bin), or
               - Specify the bin directory path in the sidebar
            4. Restart your application
            """)
        else:
            extracted_text = ""  # Reset text if using OCR
            with st.spinner("Performing OCR on document..."):
                try:
                    images = convert_from_bytes(file_bytes, dpi=ocr_dpi, 
                                              poppler_path=poppler_path if poppler_path else None)
                    st.success(f"✅ Successfully converted {len(images)} pages to images for OCR")
                    
                    # Progress bar for OCR
                    progress_bar = st.progress(0)
                    
                    for i, image in enumerate(images):
                        progress_bar.progress((i+1)/len(images))
                        try:
                            text = pytesseract.image_to_string(image, lang=ocr_lang)
                            extracted_text += f"\n--- Page {i+1} ---\n{text}"
                            st.info(f"Processed page {i+1}/{len(images)}")
                        except Exception as e:
                            st.error(f"OCR error on page {i+1}: {str(e)}")
                    
                    progress_bar.empty()
                    
                except Exception as e:
                    st.error(f"❌ OCR processing error: {str(e)}")

    # Clean up the temporary file
    try:
        os.unlink(tmp_pdf_path)
    except:
        pass

    # Show result
    if extracted_text.strip():
        st.success("✅ Text extraction complete!")
        st.text_area("📃 Extracted Text", extracted_text, height=400)

        col1, col2 = st.columns(2)
        with col1:
            # Download as text
            st.download_button("⬇️ Download Text", extracted_text, file_name="extracted_text.txt")
        
        with col2:
            # Create and download as PDF
            try:
                pdf_bytes = create_pdf_from_text(extracted_text, title=f"Extracted from {uploaded_file.name}")
                st.download_button("⬇️ Download as PDF", pdf_bytes, 
                                 file_name="extracted_text.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error creating PDF: {str(e)}")
    else:
        st.error("❌ Failed to extract any text. Check the PDF or try another one.")
        
    # Show tips
    with st.expander("Troubleshooting Tips"):
        st.markdown("""
        ### Tips for better results:
        
        1. **For text-based PDFs**: Ensure the PDF is not password-protected.
        
        2. **For scanned PDFs**:
           - Try adjusting the DPI setting in the sidebar (higher DPI may give better results but uses more memory)
           - Select the correct language for your document
           - Ensure the scan quality is good - clear, high-contrast scans work best
           
        3. **For mixed PDFs**:
           - Try the "Force OCR on all pages" option
           
        4. **If extraction fails**:
           - Verify Poppler and Tesseract are correctly installed
           - Try processing smaller sections of the PDF
           - For secure or DRM-protected PDFs, OCR might be the only option
        """)