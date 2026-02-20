# Complete Brand Blueprint Migration Package

## 📦 Package Contents

This package contains everything needed to run the Brand Blueprint application as a standalone system.

---

## 🗂️ Files Included

### Core Application Files (Standalone)

1. **STANDALONE_MAIN.py** - Complete FastAPI application
   - All API endpoints
   - File upload handling
   - Frontend routes
   - Health check endpoint

2. **STANDALONE_MODELS.py** - Data models
   - SQLAlchemy database models
   - Pydantic request/response schemas
   - Type definitions

3. **STANDALONE_CONFIG.py** - Configuration management
   - Environment variable handling
   - Settings class
   - Directory initialization

4. **STANDALONE_DATABASE.py** - Database setup
   - SQLAlchemy engine configuration
   - Session management
   - Database utilities

### Services

5. **services/pdf_processor.py** - PDF processing service
   - Text extraction from PDF/DOCX
   - AI-powered brand analysis
   - File upload handling

### Templates

6. **templates/brand-blueprint.html** - Main UI
   - Complete frontend interface
   - Alpine.js for interactivity
   - JSON export functionality

7. **templates/agent.html** - Agent page (if needed)

### Migration Tools

8. **MIGRATION_SCRIPT.py** - Automated migration script
   - Creates directory structure
   - Copies all files
   - Updates imports
   - Creates configuration files

### Documentation

9. **BRAND_BLUEPRINT_MIGRATION_PACKAGE.md** - Migration guide
10. **INSTALL_PDF_SUPPORT.md** - PDF dependencies installation
11. **PDF_PROCESSING_FEATURE.md** - PDF feature documentation
12. **JSON_EXPORT_FEATURE.md** - Export feature documentation
13. **QUICK_START_BLUEPRINT.md** - Quick start guide
14. **IMPLEMENTATION_SUMMARY.md** - Implementation details
15. **COMPLETE_MIGRATION_PACKAGE.md** - This file

### Configuration

16. **requirements.txt** - Python dependencies
17. **.env.example** - Environment variables template

---

## 🚀 Quick Migration (3 Methods)

### Method 1: Automated Script (Recommended)

```bash
# Run the migration script
python MIGRATION_SCRIPT.py --target /path/to/new/directory

# Follow the prompts
# Script will:
# - Create directory structure
# - Copy all files
# - Update imports
# - Create README and .gitignore
```

### Method 2: Manual Copy

```bash
# Create new directory
mkdir -p brand-blueprint-app/app/{services,templates,static,uploads/guidelines,docs}

# Copy standalone files
cp STANDALONE_MAIN.py brand-blueprint-app/app/main.py
cp STANDALONE_MODELS.py brand-blueprint-app/app/models.py
cp STANDALONE_CONFIG.py brand-blueprint-app/app/config.py
cp STANDALONE_DATABASE.py brand-blueprint-app/app/database.py

# Copy services
cp -r services/pdf_processor.py brand-blueprint-app/app/services/
cp services/__init__.py brand-blueprint-app/app/services/

# Copy templates
cp templates/brand-blueprint.html brand-blueprint-app/app/templates/
cp templates/agent.html brand-blueprint-app/app/templates/

# Copy configuration
cp requirements.txt brand-blueprint-app/
cp .env.example brand-blueprint-app/

# Copy documentation
mkdir brand-blueprint-app/docs
cp *_FEATURE.md brand-blueprint-app/docs/
cp INSTALL_PDF_SUPPORT.md brand-blueprint-app/docs/
cp QUICK_START_BLUEPRINT.md brand-blueprint-app/docs/

# Update imports (see Method 3 for details)
```

### Method 3: Import Updates

After copying files, update these import statements:

**In app/main.py:**
```python
# Change:
from STANDALONE_CONFIG import get_settings, Settings
from STANDALONE_DATABASE import get_db, init_db
from STANDALONE_MODELS import BrandBlueprint, BrandBlueprintRequest

# To:
from app.config import get_settings, Settings
from app.database import get_db, init_db
from app.models import BrandBlueprint, BrandBlueprintRequest
```

**In app/models.py:**
```python
# Change:
from STANDALONE_DATABASE import Base

# To:
from app.database import Base
```

**In app/database.py:**
```python
# Change:
from STANDALONE_CONFIG import get_settings

# To:
from app.config import get_settings
```

**In app/main.py (PDF processor import):**
```python
# Change:
from services.pdf_processor import PDFProcessor

# To:
from app.services.pdf_processor import PDFProcessor
```

---

## 📋 Post-Migration Setup

### 1. Install Dependencies

```bash
cd brand-blueprint-app
pip install -r requirements.txt
```

### 2. Install External Tools (Optional - for OCR)

**Windows:**
- Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Poppler: http://blog.alivate.com.au/poppler-windows/

**Mac:**
```bash
brew install tesseract poppler
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

### 3. Configure Environment

```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add your credentials
nano .env  # or use your preferred editor
```

Required in `.env`:
```env
OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=sqlite:///./brand_blueprint.db
UPLOAD_DIR=./uploads/guidelines
```

### 4. Initialize Database

```bash
python -c "from app.database import init_db; init_db()"
```

### 5. Run Application

```bash
# Method 1: Direct
python app/main.py

# Method 2: Uvicorn
uvicorn app.main:app --reload

# Method 3: With custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

### 6. Access Application

Open browser:
- Home: http://localhost:8000
- Brand Blueprint: http://localhost:8000/brand-blueprint
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

---

## 📁 Final Directory Structure

```
brand-blueprint-app/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Data models
│   ├── config.py               # Configuration
│   ├── database.py             # Database setup
│   ├── services/
│   │   ├── __init__.py
│   │   └── pdf_processor.py   # PDF processing
│   ├── templates/
│   │   ├── brand-blueprint.html
│   │   └── agent.html
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   └── uploads/
│       └── guidelines/         # Uploaded PDFs
├── docs/
│   ├── INSTALL_PDF_SUPPORT.md
│   ├── PDF_PROCESSING_FEATURE.md
│   ├── JSON_EXPORT_FEATURE.md
│   └── QUICK_START.md
├── tests/
│   └── __init__.py
├── .env                        # Your credentials (not in git)
├── .env.example                # Template
├── .gitignore
├── requirements.txt
├── README.md
└── brand_blueprint.db          # SQLite database (created on init)
```

---

## ✅ Verification Checklist

After migration, verify:

- [ ] All files copied successfully
- [ ] Imports updated correctly
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Database initialized
- [ ] Server starts without errors
- [ ] Brand blueprint page loads
- [ ] PDF upload works
- [ ] AI extraction works
- [ ] JSON export works
- [ ] Data persists to database

---

## 🧪 Testing

### Test PDF Upload

1. Start server: `python app/main.py`
2. Open: http://localhost:8000/brand-blueprint
3. Upload a PDF with brand guidelines
4. Verify data extracts correctly

### Test JSON Export

1. Configure brand blueprint
2. Click "💾 Save JSON"
3. Verify JSON file downloads
4. Check JSON structure

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Get blueprint
curl http://localhost:8000/api/brand/blueprint?brand_id=brand-001

# Upload file (use Postman or similar)
# POST http://localhost:8000/api/brand/upload-guideline
```

---

## 🔧 Customization

### Change Database

Edit `app/config.py`:
```python
# PostgreSQL
DATABASE_URL = "postgresql://user:password@localhost/dbname"

# MySQL
DATABASE_URL = "mysql://user:password@localhost/dbname"
```

### Change Upload Directory

Edit `.env`:
```env
UPLOAD_DIR=/custom/path/to/uploads
```

### Add Custom Routes

Edit `app/main.py`:
```python
@app.get("/custom-route")
async def custom_route():
    return {"message": "Custom route"}
```

### Modify AI Prompts

Edit `app/services/pdf_processor.py`:
```python
def analyze_brand_guidelines(self, text: str) -> Dict:
    prompt = f"""Your custom prompt here..."""
```

---

## 🐛 Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:**
```bash
# Run from project root
cd brand-blueprint-app
python app/main.py

# Or use PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python app/main.py
```

### Database Errors

**Problem:** `OperationalError: no such table`

**Solution:**
```bash
python -c "from app.database import init_db; init_db()"
```

### OpenAI Errors

**Problem:** `AuthenticationError: Invalid API key`

**Solution:**
- Check `.env` file has correct API key
- Verify key starts with `sk-`
- Check account has credits

### File Upload Errors

**Problem:** `PermissionError: [Errno 13] Permission denied`

**Solution:**
```bash
# Create uploads directory with correct permissions
mkdir -p uploads/guidelines
chmod 755 uploads/guidelines
```

---

## 📚 Additional Resources

### Documentation Files

- `docs/INSTALL_PDF_SUPPORT.md` - Detailed installation guide
- `docs/PDF_PROCESSING_FEATURE.md` - PDF feature documentation
- `docs/JSON_EXPORT_FEATURE.md` - Export feature documentation
- `docs/QUICK_START.md` - Quick start guide

### API Documentation

Access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Example Files

Create `examples/` directory with sample PDFs and JSON files for testing.

---

## 🚢 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in .env
- [ ] Use production database (PostgreSQL/MySQL)
- [ ] Set up proper CORS origins
- [ ] Use environment variables for secrets
- [ ] Set up logging
- [ ] Configure reverse proxy (nginx)
- [ ] Set up SSL/TLS
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Configure backups

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY .env .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t brand-blueprint .
docker run -p 8000:8000 brand-blueprint
```

---

## 🎉 Success!

Your Brand Blueprint application is now standalone and ready to use!

**Key Features:**
- ✅ PDF/DOCX upload and processing
- ✅ AI-powered brand analysis
- ✅ Dynamic content pillars
- ✅ Forbidden phrases management
- ✅ Brand hashtags
- ✅ JSON export
- ✅ Content package export
- ✅ Complete documentation

**Next Steps:**
1. Customize for your needs
2. Add additional features
3. Deploy to production
4. Share with your team

For support or questions, refer to the documentation in the `docs/` directory.

Happy coding! 🚀
