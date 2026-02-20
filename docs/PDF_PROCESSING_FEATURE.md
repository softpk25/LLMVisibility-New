# PDF Processing Feature - Implementation Summary

## Overview

The brand blueprint page now supports dynamic extraction of content pillars, forbidden phrases, and brand hashtags from uploaded PDF/DOCX brand guideline documents using AI-powered analysis.

## What Was Implemented

### 1. PDF Processing Service (`services/pdf_processor.py`)

A new service that handles:
- **PDF text extraction** using PyPDF2
- **DOCX text extraction** using python-docx
- **OCR support** for scanned documents (via pytesseract)
- **AI analysis** using OpenAI GPT-4 to extract:
  - Brand name and industry
  - Content pillars with descriptions and weights
  - Forbidden phrases
  - Brand hashtags
  - Voice profile settings (formality, humor, warmth, emoji policy)
  - Target audience

### 2. API Endpoint (`/api/brand/upload-guideline`)

New POST endpoint that:
- Accepts PDF/DOCX files up to 50 MB
- Validates file type and size
- Processes the document and extracts brand data
- Saves the data to the database
- Returns structured brand information

**Request:**
```
POST /api/brand/upload-guideline?brand_id=brand-001
Content-Type: multipart/form-data
Body: file (PDF/DOCX)
```

**Response:**
```json
{
  "status": "success",
  "message": "Brand guideline processed successfully",
  "brandData": {
    "brandName": "TechCorp",
    "industry": "Technology",
    "targetAudience": "Tech professionals and enthusiasts",
    "pillars": [
      {
        "name": "Innovation",
        "description": "Latest tech trends",
        "weight": 30
      }
    ],
    "forbiddenPhrases": ["buy now", "limited time"],
    "brandHashtags": ["#TechCorp", "#Innovation"],
    "voice": {
      "formality": 50,
      "humor": 30,
      "warmth": 60,
      "emojiPolicy": "light"
    }
  }
}
```

### 3. Frontend Integration

Updated `brand-blueprint.html` to:
- Handle file upload via drag-and-drop or click
- Show upload progress and status
- Call the API endpoint with the uploaded file
- Dynamically update the UI with extracted data:
  - Content pillars list
  - Forbidden phrases chips
  - Brand hashtags chips
  - Voice profile sliders
- Display success/error messages
- Auto-switch to blueprint tab for review

### 4. Database Schema

The `BrandBlueprint` model already supports storing:
- `pillars` (JSON array)
- `forbidden_phrases` (JSON array)
- `brand_hashtags` (JSON array)
- `voice_formality`, `voice_humor`, `voice_warmth` (integers)
- `emoji_policy` (string)
- `guideline_doc_name` (string)
- `guideline_doc_status` (string)

### 5. Dependencies Added

New packages in `requirements.txt`:
- `PyPDF2==3.0.1` - PDF text extraction
- `python-docx==1.1.0` - DOCX text extraction
- `pytesseract==0.3.10` - OCR for scanned documents
- `Pillow==10.2.0` - Image processing
- `pdf2image==1.17.0` - PDF to image conversion

## How It Works

### User Flow

1. **Upload**: User navigates to `/brand-blueprint` and uploads a PDF/DOCX file
2. **Processing**: Backend extracts text and sends it to OpenAI for analysis
3. **Extraction**: AI identifies brand elements and returns structured data
4. **Display**: Frontend updates all fields with extracted information
5. **Review**: User reviews and edits the auto-populated data
6. **Save**: User saves or approves the blueprint

### AI Prompt Strategy

The system uses a carefully crafted prompt that:
- Instructs GPT-4 to analyze brand guidelines
- Requests specific structured output (JSON format)
- Defines exact schema for consistency
- Handles missing or incomplete information gracefully
- Falls back to sensible defaults if AI fails

### Error Handling

- **Invalid file type**: Returns 400 error with allowed formats
- **File too large**: Returns 400 error (50 MB limit)
- **Text extraction fails**: Returns 400 error with helpful message
- **AI processing fails**: Falls back to default brand data
- **Network errors**: Shows user-friendly error message

## Configuration

### Required Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Optional Configuration

The PDF processor can be configured by modifying `services/pdf_processor.py`:
- Upload directory location
- AI model selection (currently GPT-4 Turbo)
- Prompt customization
- Default fallback values

## Testing

### Test the Feature

1. Start the FastAPI server:
```bash
cd "python integration/facebook smm"
python main.py
```

2. Navigate to: `http://localhost:8000/brand-blueprint`

3. Upload a test PDF with brand guidelines

4. Verify the extracted data appears in the blueprint tab

### Sample Test Document

Create a simple PDF with content like:

```
Brand Guidelines for TechCorp

Our brand voice is professional yet approachable. We use moderate humor
and maintain a warm tone with our audience.

Content Pillars:
1. Innovation - Showcasing cutting-edge technology
2. Education - Teaching our users
3. Community - Building connections
4. Product Updates - New features and improvements

Forbidden Language:
- Avoid "buy now" and "limited time" pressure tactics
- Don't use overly technical jargon
- Never make unsubstantiated claims

Brand Hashtags:
#TechCorp #Innovation #TechForGood #FutureOfWork

Target Audience: Tech professionals, developers, and early adopters
```

## Future Enhancements

Potential improvements:
- Support for more file formats (Google Docs, Notion exports)
- Multi-language support for non-English guidelines
- Image extraction from PDFs (logos, color palettes)
- Version history for blueprint changes
- Collaborative editing features
- Export blueprint as PDF report

## Troubleshooting

See `INSTALL_PDF_SUPPORT.md` for installation and troubleshooting guide.

## API Documentation

The endpoint is automatically documented in FastAPI's Swagger UI:
- Navigate to: `http://localhost:8000/docs`
- Find: `POST /api/brand/upload-guideline`
- Test directly from the browser

## Security Considerations

- File size limited to 50 MB to prevent abuse
- Only PDF and DOCX formats accepted
- Files are saved to a dedicated uploads directory
- Filenames are sanitized to prevent path traversal
- API key is never exposed to the frontend
- Uploaded files are processed server-side only
