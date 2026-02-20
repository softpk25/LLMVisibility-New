# Brand Blueprint Migration Package

## Overview

This document lists all files needed to migrate the brand blueprint functionality to a standalone application or different directory.

---

## 📦 Files to Copy

### Core Application Files

#### 1. **Backend API Routes** (Extract from `main.py`)
Location: Lines containing brand blueprint endpoints
- `/api/brand/upload-guideline` (POST)
- `/api/brand/blueprint` (GET)
- `/api/brand/blueprint` (POST)
- `/api/brand/blueprint/generate` (POST)
- `/api/brand/blueprint/approve` (POST)
- `/FACEBOOK-BRAND-REGISTRATION.html` (GET)
- `/brand-blueprint` (GET)
- `/agent` (GET)

#### 2. **Services**
- `services/pdf_processor.py` - PDF processing and AI analysis
- `services/openai_service.py` - OpenAI integration (if used)

#### 3. **Models** (Extract from `models.py`)
- `BrandBlueprint` (SQLAlchemy model)
- `VoiceProfile` (Pydantic model)
- `ContentPillar` (Pydantic model)
- `Policies` (Pydantic model)
- `BlueprintData` (Pydantic model)
- `BrandBlueprintRequest` (Pydantic model)
- `BrandBlueprintResponse` (Pydantic model)

#### 4. **Templates**
- `templates/brand-blueprint.html` - Main UI
- `templates/agent.html` - Agent page (if needed)

#### 5. **Static Files**
- `static/css/style.css` - Styles (if custom styles exist)
- `static/js/app.js` - JavaScript (if separate file exists)

#### 6. **Configuration**
- `config.py` - Settings management
- `database.py` - Database setup
- `.env.example` - Environment variables template

#### 7. **Dependencies**
- `requirements.txt` - Python packages

#### 8. **Uploads Directory**
- `uploads/guidelines/` - Directory for uploaded files

---

## 📋 Migration Steps

### Step 1: Create New Directory Structure

```
brand-blueprint-app/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py
│   │   └── openai_service.py
│   ├── templates/
│   │   ├── brand-blueprint.html
│   │   └── agent.html
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── uploads/
│       └── guidelines/
├── .env
├── .env.example
├── requirements.txt
└── README.md
```

### Step 2: Extract and Copy Files

Use the extraction script provided below or manually copy files.

### Step 3: Update Imports

Update import paths in the new location:
```python
# Old
from config import get_settings
from database import get_db
from models import BrandBlueprint

# New (if using app package)
from app.config import get_settings
from app.database import get_db
from app.models import BrandBlueprint
```

### Step 4: Update Configuration

Update `.env` file with necessary credentials:
```env
OPENAI_API_KEY=your_key
DATABASE_URL=sqlite:///./brand_blueprint.db
```

### Step 5: Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

### Step 6: Test

```bash
python app/main.py
# or
uvicorn app.main:app --reload
```

---

## 🔧 Extraction Details

### Files Content Summary

**See the following files for complete standalone code:**
1. `STANDALONE_MAIN.py` - Complete FastAPI app
2. `STANDALONE_MODELS.py` - All data models
3. `STANDALONE_CONFIG.py` - Configuration
4. `STANDALONE_DATABASE.py` - Database setup

These files are created in the next step and contain all the extracted code.

---

## ⚙️ Configuration Requirements

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults provided)
DATABASE_URL=sqlite:///./brand_blueprint.db
UPLOAD_DIR=./uploads/guidelines
MAX_UPLOAD_SIZE=52428800
```

### External Dependencies

**For OCR Support (Optional):**
- Tesseract OCR
- Poppler utilities

**Installation:**
- Windows: See `INSTALL_PDF_SUPPORT.md`
- Mac: `brew install tesseract poppler`
- Linux: `apt-get install tesseract-ocr poppler-utils`

---

## 🚀 Quick Migration Command

```bash
# Create new directory
mkdir -p brand-blueprint-app/app/{services,templates,static/css,static/js,uploads/guidelines}

# Copy files (adjust paths as needed)
cp services/pdf_processor.py brand-blueprint-app/app/services/
cp templates/brand-blueprint.html brand-blueprint-app/app/templates/
cp requirements.txt brand-blueprint-app/
cp .env brand-blueprint-app/

# Copy standalone files
cp STANDALONE_*.py brand-blueprint-app/app/

# Initialize
cd brand-blueprint-app
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## 📝 Notes

### Database Migration

If you need to migrate existing data:

```python
# Export from old database
from old_app.database import SessionLocal
from old_app.models import BrandBlueprint
import json

db = SessionLocal()
blueprints = db.query(BrandBlueprint).all()

data = []
for bp in blueprints:
    data.append({
        'brand_id': bp.brand_id,
        'brand_name': bp.brand_name,
        # ... other fields
    })

with open('blueprints_export.json', 'w') as f:
    json.dump(data, f)

# Import to new database
from new_app.database import SessionLocal
from new_app.models import BrandBlueprint

db = SessionLocal()
with open('blueprints_export.json', 'r') as f:
    data = json.load(f)

for item in data:
    bp = BrandBlueprint(**item)
    db.add(bp)
db.commit()
```

### API Endpoint Changes

If moving to a different domain/port, update:
- Frontend API calls in `brand-blueprint.html`
- CORS settings in FastAPI app
- Redirect URLs if using OAuth

---

## ✅ Verification Checklist

After migration, verify:
- [ ] Server starts without errors
- [ ] Database initializes correctly
- [ ] Brand blueprint page loads
- [ ] PDF upload works
- [ ] AI extraction works
- [ ] JSON export works
- [ ] Data persists to database
- [ ] All routes accessible
- [ ] Static files load correctly
- [ ] Environment variables read correctly

---

## 🆘 Troubleshooting

### Import Errors
- Check `__init__.py` files exist
- Verify Python path includes app directory
- Update import statements

### Database Errors
- Run `init_db()` to create tables
- Check DATABASE_URL in .env
- Verify write permissions

### File Upload Errors
- Check uploads directory exists
- Verify write permissions
- Check MAX_UPLOAD_SIZE setting

### OpenAI Errors
- Verify API key in .env
- Check internet connection
- Verify account has credits

---

## 📚 Next Steps

After migration:
1. Test all functionality
2. Update documentation
3. Configure production settings
4. Set up monitoring/logging
5. Deploy to production environment

---

## 🔗 Related Documentation

- `STANDALONE_MAIN.py` - Complete standalone app
- `STANDALONE_MODELS.py` - Data models
- `STANDALONE_CONFIG.py` - Configuration
- `STANDALONE_DATABASE.py` - Database setup
- `INSTALL_PDF_SUPPORT.md` - PDF dependencies
- `QUICK_START_BLUEPRINT.md` - Quick start guide
