# Quick Start Guide - Brand Blueprint Features

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd "python integration/facebook smm"
pip install -r requirements.txt
```

### Step 2: Install External Tools (Optional - for OCR)

**Windows:**
- Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Download Poppler: http://blog.alivate.com.au/poppler-windows/

**Mac:**
```bash
brew install tesseract poppler
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

### Step 3: Configure Environment

Create/update `.env` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
FACEBOOK_PAGE_ACCESS_TOKEN=your_token
FACEBOOK_PAGE_ID=your_page_id
```

### Step 4: Start Server

```bash
python main.py
```

### Step 5: Access Brand Blueprint

Open browser: `http://localhost:8000/brand-blueprint`

---

## 📤 Upload Brand Guidelines

1. Click **Onboarding** tab
2. Click **Upload Document** area
3. Select your PDF or DOCX file (max 50 MB)
4. Wait for processing (2-10 seconds)
5. Review extracted data in **Blueprint** tab

**What Gets Extracted:**
- ✅ Content pillars (with weights)
- ✅ Forbidden phrases
- ✅ Brand hashtags
- ✅ Voice profile settings
- ✅ Brand name and industry

---

## 💾 Export Blueprint as JSON

1. Go to **Blueprint** tab
2. Review/edit your brand data
3. Click **💾 Save JSON** button
4. JSON file downloads automatically

**File:** `YourBrand_blueprint_2026-02-09.json`

---

## 📦 Export Content Package

1. Go to **Planner** tab → Create a plan
2. Go to **Creator & Review** tab → Generate drafts
3. Approve posts you want to export
4. Go to **Calendar/Export** tab
5. Click **Export Package (CSV/JSON)** button
6. Both files download automatically

**Files:**
- `YourBrand_content_package_2026-02-09.json`
- `YourBrand_content_package_2026-02-09.csv`

---

## 🎯 Quick Tips

### For Best PDF Extraction Results:
- Use text-based PDFs (not scanned images)
- Include clear section headers
- List content pillars explicitly
- Mention forbidden phrases/words
- Include brand hashtags

### Sample PDF Structure:
```
Brand Guidelines for [Your Brand]

Voice & Tone:
- Professional yet approachable
- Moderate use of humor
- Warm and friendly

Content Pillars:
1. Innovation - Latest trends (30%)
2. Education - Tips and tutorials (25%)
3. Community - User stories (25%)
4. Product - Features and updates (20%)

Forbidden Language:
- Avoid "buy now" pressure tactics
- Don't use technical jargon
- Never make unsubstantiated claims

Brand Hashtags:
#YourBrand #Innovation #TechForGood
```

### JSON Export Use Cases:
- **Backup:** Save versions of your blueprint
- **Sharing:** Send to team members
- **Integration:** Import into other tools
- **Version Control:** Track changes over time

### CSV Export Use Cases:
- **Scheduling:** Import into Buffer, Hootsuite
- **Review:** Share with stakeholders
- **Analytics:** Track content performance
- **Reporting:** Generate content reports

---

## ⚠️ Troubleshooting

### PDF Upload Issues

**Problem:** "Could not extract text"
- **Solution:** PDF might be scanned. Install Tesseract for OCR.

**Problem:** "File too large"
- **Solution:** Compress PDF or split into smaller files.

**Problem:** "Invalid file type"
- **Solution:** Only PDF and DOCX files are supported.

### JSON Export Issues

**Problem:** Download doesn't start
- **Solution:** Check browser download settings, allow downloads.

**Problem:** File opens instead of downloads
- **Solution:** Right-click button → "Save Link As"

### API Issues

**Problem:** "OpenAI API error"
- **Solution:** Check API key in .env file, verify credits.

**Problem:** "Failed to process"
- **Solution:** Check server logs, verify OpenAI API is accessible.

---

## 📚 Documentation Files

- `INSTALL_PDF_SUPPORT.md` - Detailed installation guide
- `PDF_PROCESSING_FEATURE.md` - PDF feature documentation
- `JSON_EXPORT_FEATURE.md` - Export feature documentation
- `IMPLEMENTATION_SUMMARY.md` - Complete implementation details

---

## 🎉 You're Ready!

Your brand blueprint system is now fully functional with:
- ✅ Dynamic PDF processing
- ✅ AI-powered brand analysis
- ✅ JSON/CSV export capabilities
- ✅ Complete documentation

Start by uploading your brand guidelines and let AI do the work! 🚀
