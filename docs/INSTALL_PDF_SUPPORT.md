# PDF Processing Support Installation Guide

This guide will help you install the required dependencies for PDF/DOCX processing in the Facebook SMM application.

## Prerequisites

- Python 3.8 or higher
- pip package manager

## Installation Steps

### 1. Install Python Dependencies

```bash
cd "python integration/facebook smm"
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (for scanned PDFs)

Tesseract is required for OCR (Optical Character Recognition) of scanned PDF documents.

#### Windows:
1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer and follow the prompts
3. Add Tesseract to your PATH environment variable (usually `C:\Program Files\Tesseract-OCR`)

#### macOS:
```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

### 3. Install Poppler (for PDF to Image conversion)

Poppler is required for converting PDF pages to images for OCR processing.

#### Windows:
1. Download from: http://blog.alivate.com.au/poppler-windows/
2. Extract to a folder (e.g., `C:\Program Files\poppler`)
3. Add the `bin` folder to your PATH environment variable

#### macOS:
```bash
brew install poppler
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt-get install poppler-utils
```

## Verify Installation

Run this command to verify all dependencies are installed:

```bash
python -c "import PyPDF2, docx, pytesseract, PIL; print('✅ All dependencies installed successfully!')"
```

## Configuration

Make sure your `.env` file has the OpenAI API key configured:

```
OPENAI_API_KEY=your_openai_api_key_here
```

The PDF processor uses OpenAI's GPT-4 to analyze brand guidelines and extract:
- Content pillars
- Forbidden phrases
- Brand hashtags
- Voice profile settings

## Usage

1. Navigate to the brand blueprint page: `/FACEBOOK-BRAND-REGISTRATION.html` or `/brand-blueprint`
2. Click on the "Upload Document" area in the Onboarding tab
3. Select your brand guideline PDF or DOCX file (max 50 MB)
4. The system will:
   - Extract text from the document
   - Use AI to analyze the content
   - Automatically populate content pillars, forbidden phrases, and brand hashtags
   - Set voice profile parameters
5. Review and edit the extracted data in the Blueprint tab
6. Save or approve the blueprint

## Troubleshooting

### "Tesseract not found" error
- Make sure Tesseract is installed and added to your PATH
- On Windows, you may need to set the path explicitly in the code

### "Poppler not found" error
- Make sure Poppler is installed and the `bin` folder is in your PATH
- On Windows, verify the path is correct

### PDF extraction returns empty text
- The PDF might be scanned/image-based - OCR will be attempted automatically
- Try a different PDF file to verify the system is working

### OpenAI API errors
- Verify your API key is correct in the `.env` file
- Check your OpenAI account has sufficient credits
- The system will fall back to default values if AI processing fails

## Support

For issues or questions, please check the main README.md or contact support.
