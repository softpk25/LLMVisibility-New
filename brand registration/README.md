# Brand Registration Backend System

## Overview
Complete brand registration backend system with FastAPI integration, file upload handling, and JSON data persistence.

## Features Completed ✅

### Backend API (`brand_registration_api.py`)
- **FastAPI Router**: Complete REST API with all endpoints
- **Data Models**: Pydantic models for validation and serialization
- **File Upload**: PDF/DOCX brand guideline upload (up to 50MB)
- **JSON Persistence**: Data stored in `brand_registrations.json` in root directory
- **Error Handling**: Comprehensive error handling and validation
- **Auto-timestamps**: Automatic creation and update timestamps

### Frontend Integration (`templates/FACEBOOK-BRAND-REGISTRATION.html`)
- **Real API Calls**: All form interactions connected to backend
- **File Upload**: Drag-and-drop file upload with progress indicators
- **Auto-save**: Debounced auto-save for settings and blueprint changes
- **Form Validation**: Client-side validation with error handling
- **Tab Navigation**: Complete tab system for different sections
- **Real-time Updates**: Live form updates with backend synchronization

### Server Integration (`server.py`)
- **Router Integration**: Brand registration API mounted at `/api/brand-registration`
- **CORS Support**: Cross-origin requests enabled
- **Static File Serving**: HTML templates served correctly

## API Endpoints

### Brand Management
- `GET /api/brand-registration/brands` - List all brands
- `GET /api/brand-registration/brand/{brand_id}` - Get specific brand
- `POST /api/brand-registration/create-brand` - Create new brand
- `PUT /api/brand-registration/update-brand/{brand_id}` - Update brand
- `DELETE /api/brand-registration/brand/{brand_id}` - Delete brand

### Data Operations
- `POST /api/brand-registration/save-settings/{brand_id}` - Save brand settings
- `POST /api/brand-registration/save-blueprint/{brand_id}` - Save brand blueprint
- `POST /api/brand-registration/upload-guideline/{brand_id}` - Upload brand guideline

## Data Structure

### Settings
- Default language (en, es, fr, de, hi)
- Default LLM model (gpt-4.1, claude-3.5, gemini-pro)
- Product inclusion percentage (0-100%)

### Blueprint
- **Voice Profile**: Formality, humor, warmth sliders + emoji policy
- **Content Pillars**: Name, description, weight for each pillar
- **Policies**: Forbidden phrases, max hashtags, brand hashtags

### File Uploads
- Stored in `brand registration/uploads/{brand_id}/`
- Metadata tracked in brand data
- Support for PDF and DOCX files

## Usage

### Start Server
```bash
python server.py
```

### Access Interface
Navigate to: `http://localhost:8000/FACEBOOK-BRAND-REGISTRATION.html`

### Features Available
1. **Onboarding Tab**: Upload brand guidelines, set defaults
2. **Blueprint Tab**: Configure voice profile, content pillars, policies
3. **Auto-save**: Changes automatically saved to backend
4. **File Upload**: Drag-and-drop brand guideline documents
5. **Form Validation**: Real-time validation and error handling

## File Structure
```
brand registration/
├── brand_registration_api.py    # FastAPI backend
├── brand_registration_client.js  # Standalone client (optional)
├── requirements.txt             # Python dependencies
├── uploads/                     # File upload directory
└── README.md                   # This file

templates/
└── FACEBOOK-BRAND-REGISTRATION.html  # Frontend interface

brand_registrations.json        # Data persistence (root directory)
server.py                      # Main server with integration
```

## Integration Status
- ✅ Backend API fully functional
- ✅ Frontend form completely integrated
- ✅ File upload working with validation
- ✅ Auto-save implemented with debouncing
- ✅ Error handling and user feedback
- ✅ Data persistence to JSON file
- ✅ Server integration complete
- ✅ All form elements connected to backend
- ✅ Tab navigation working
- ✅ Real-time form updates

## Next Steps
The brand registration system is now complete and ready for use. Users can:
1. Upload brand guideline documents
2. Configure default settings (language, LLM, product percentage)
3. Create detailed brand blueprints with voice profiles and content pillars
4. Set brand policies including forbidden phrases and hashtags
5. All data is automatically saved and persisted

The system provides a solid foundation for AI-powered brand content management.