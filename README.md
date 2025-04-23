# OCR PDF Extractor

A Streamlit application that extracts text from PDFs using both text-based extraction and OCR.

## Features

- Extracts text from text-based PDFs using pdfplumber
- Automatically falls back to OCR for scanned documents
- Supports downloading extracted text as a file
- No GPU required - uses CPU-based OCR

## Requirements

- Python 3.7+
- Poppler (for PDF to image conversion)
- Tesseract OCR (for image to text conversion)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/KunjShah95/ocr-pdf-extractor.git
   cd ocr-pdf-extractor
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Poppler:
   - **Windows**: 
     1. Download from: https://github.com/oschwartz10612/poppler-windows/releases/
     2. Extract to a folder (e.g., `C:\poppler`)
     3. Either add the `bin` directory to your PATH or specify it in the app
   
   - **macOS**:
     ```
     brew install poppler
     ```
   
   - **Linux**:
     ```
     sudo apt-get install poppler-utils
     ```

4. Install Tesseract OCR:
   - **Windows**:
     1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
     2. Install and note the installation path
   
   - **macOS**:
     ```
     brew install tesseract
     ```
   
   - **Linux**:
     ```
     sudo apt-get install tesseract-ocr
     ```

## Usage

1. Run the Streamlit app:
   ```
   streamlit run main.py
   ```

2. Access the app in your browser at `http://localhost:8501`

3. Upload a PDF file using the file uploader

4. If your Poppler or Tesseract installations are not in the system PATH:
   - Enter the paths in the sidebar configuration section

5. Wait for the text extraction to complete

6. View the extracted text and download it if needed

## Troubleshooting

- **"Unable to get page count. Is poppler installed and in PATH?"** - You need to install Poppler or specify its path in the sidebar
- **OCR errors** - Ensure Tesseract is properly installed and its path is correctly specified if not in system PATH

## License

[MIT License](LICENSE)