"""
PDF Processing Service for Brand Guidelines
Extracts text from PDF files and uses AI to analyze brand content
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
from docx import Document
from app.config import get_settings


class PDFProcessor:
    """Process PDF/DOCX files and extract brand guidelines using AI."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.uploads_dir = Path(__file__).parent.parent / "uploads" / "guidelines"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize OpenAI client with error handling
        try:
            from openai import OpenAI
            if self.settings.OPENAI_API_KEY:
                self.client = OpenAI(api_key=self.settings.OPENAI_API_KEY)
            else:
                print("Warning: OPENAI_API_KEY not configured. AI analysis will use defaults.")
        except ImportError as e:
            print(f"Warning: Could not import OpenAI. Please install openai package: pip install openai>=1.0.0")
            print(f"Error details: {e}")
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Error extracting text from DOCX: {e}")
            return ""
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF or DOCX file."""
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def analyze_brand_guidelines(self, text: str) -> Dict:
        """
        Use OpenAI to analyze brand guidelines and extract structured data.
        Returns content pillars, forbidden phrases, brand hashtags, and voice profile.
        """
        
        prompt = f"""You are a brand strategist analyzing a brand guideline document. 
Extract the following information from the text and return it in a structured JSON format:

1. **Content Pillars**: Identify 3-5 main content themes/pillars the brand focuses on. 
   For each pillar, provide:
   - name: Short name (2-4 words)
   - description: Brief description (1 sentence)
   - weight: Suggested percentage weight (should sum to 100)

2. **Forbidden Phrases**: List any phrases, words, or terms the brand explicitly avoids or prohibits.
   Include things like competitor names, negative terms, or off-brand language.

3. **Brand Hashtags**: Extract or suggest 5-10 brand-specific hashtags that align with the brand identity.
   Include both branded hashtags and category hashtags.

4. **Voice Profile**: Analyze the brand voice and rate these attributes (0-100):
   - formality: 0=very casual, 100=very formal
   - humor: 0=serious, 100=playful
   - warmth: 0=direct/professional, 100=warm/friendly
   - emojiPolicy: "none", "light", "medium", or "rich"

5. **Brand Name**: Extract the brand/company name

6. **Industry**: Identify the industry/sector

7. **Target Audience**: Describe the target audience

Return ONLY valid JSON in this exact format:
{{
  "brandName": "string",
  "industry": "string",
  "targetAudience": "string",
  "pillars": [
    {{"name": "string", "description": "string", "weight": number}}
  ],
  "forbiddenPhrases": ["string"],
  "brandHashtags": ["string"],
  "voice": {{
    "formality": number,
    "humor": number,
    "warmth": number,
    "emojiPolicy": "string"
  }}
}}

Brand Guideline Text:
{text[:8000]}

Return only the JSON, no additional text or explanation."""

        # Check if OpenAI client is available
        if not self.client:
            print("OpenAI client not available. Returning default brand structure.")
            return {
                "brandName": "Unknown Brand",
                "industry": "General",
                "targetAudience": "General audience",
                "pillars": [
                    {"name": "Educational Content", "description": "Share knowledge and insights", "weight": 40},
                    {"name": "Product Updates", "description": "Showcase products and features", "weight": 30},
                    {"name": "Community Stories", "description": "Highlight customer success", "weight": 30}
                ],
                "forbiddenPhrases": [],
                "brandHashtags": [],
                "voice": {
                    "formality": 50,
                    "humor": 30,
                    "warmth": 60,
                    "emojiPolicy": "light"
                }
            }
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are a brand strategist expert at analyzing brand guidelines."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error analyzing brand guidelines with AI: {e}")
            # Return default structure
            return {
                "brandName": "Unknown Brand",
                "industry": "General",
                "targetAudience": "General audience",
                "pillars": [
                    {"name": "Educational Content", "description": "Share knowledge and insights", "weight": 40},
                    {"name": "Product Updates", "description": "Showcase products and features", "weight": 30},
                    {"name": "Community Stories", "description": "Highlight customer success", "weight": 30}
                ],
                "forbiddenPhrases": [],
                "brandHashtags": [],
                "voice": {
                    "formality": 50,
                    "humor": 30,
                    "warmth": 60,
                    "emojiPolicy": "light"
                }
            }
    
    def process_guideline_file(self, file_path: str) -> Dict:
        """
        Process a brand guideline file and return extracted brand data.
        """
        # Extract text from file
        text = self.extract_text(file_path)
        
        if not text or len(text) < 100:
            raise ValueError("Could not extract sufficient text from the file. The file may be empty or scanned.")
        
        # Analyze with AI
        brand_data = self.analyze_brand_guidelines(text)
        
        # Add metadata
        brand_data["sourceFile"] = Path(file_path).name
        brand_data["extractedTextLength"] = len(text)
        
        return brand_data
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to uploads directory."""
        # Sanitize filename
        safe_filename = re.sub(r'[^\w\s.-]', '', filename)
        file_path = self.uploads_dir / safe_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return str(file_path)
