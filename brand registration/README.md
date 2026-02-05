# Brand Registration Backend System

## Overview
Complete brand registration backend system with FastAPI integration, file upload handling, JSON data persistence, and JSON export functionality.

## Features Completed ✅

### Backend API (`brand_registration_api.py`)
- **FastAPI Router**: Complete REST API with all endpoints
- **Data Models**: Pydantic models for validation and serialization
- **File Upload**: PDF/DOCX brand guideline upload (up to 50MB)
- **JSON Persistence**: Data stored in `brand_registrations.json` in root directory
- **JSON Export**: Server-side JSON export endpoint with download headers
- **Error Handling**: Comprehensive error handling and validation
- **Auto-timestamps**: Automatic creation and update timestamps

### Frontend Integration (`templates/FACEBOOK-BRAND-REGISTRATION.html`)
- **Real API Calls**: All form interactions connected to backend
- **File Upload**: Drag-and-drop file upload with progress indicators
- **Auto-save**: Debounced auto-save for settings and blueprint changes
- **JSON Download**: "Save JSON" button for complete data export
- **Dual Download**: Client-side and server-side download options
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
- `GET /api/brand-registration/export-json/{brand_id}` - Export brand data as JSON

## JSON Export Feature 🆕

### Save JSON Button
- Located in the Blueprint tab header
- Renamed from "Save Draft" to "Save JSON"
- Downloads complete form data as JSON file

### Export Data Structure
The exported JSON includes:
- **Brand Information**: ID, name, guideline document details
- **Voice Profile**: Formality, humor, warmth settings, emoji policy
- **Content Pillars**: Names, descriptions, and weights
- **Brand Policies**: Forbidden phrases, hashtag limits, brand hashtags
- **Settings**: Default language, LLM model, product percentage
- **Campaign Data**: Objectives, duration, language, posts
- **Creator Settings**: Language and LLM preferences
- **Export Metadata**: Timestamp, version, export method

### Download Methods
1. **Client-side**: JavaScript generates and downloads JSON immediately
2. **Server-side**: Backend creates JSON with proper download headers
3. **Dual Approach**: Both methods triggered for reliability

### File Naming
Downloaded files use format: `brand-content-data-{brand-id}-{date}.json`
Example: `brand-content-data-brand-001-2026-02-05.json`

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

### Export JSON Data
1. Fill out the form in Onboarding and Blueprint tabs
2. Click "Save JSON" button in Blueprint tab header
3. JSON file downloads automatically to local machine
4. File contains complete form data in structured format

### Features Available
1. **Onboarding Tab**: Upload brand guidelines, set defaults
2. **Blueprint Tab**: Configure voice profile, content pillars, policies
3. **Save JSON**: Export all form data as downloadable JSON file
4. **Auto-save**: Changes automatically saved to backend
5. **File Upload**: Drag-and-drop brand guideline documents
6. **Form Validation**: Real-time validation and error handling

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
sample-brand-export.json       # Example export file
server.py                      # Main server with integration
```

## Integration Status
- ✅ Backend API fully functional
- ✅ Frontend form completely integrated
- ✅ File upload working with validation
- ✅ Auto-save implemented with debouncing
- ✅ JSON export functionality complete
- ✅ Client-side and server-side download options
- ✅ Error handling and user feedback
- ✅ Data persistence to JSON file
- ✅ Server integration complete
- ✅ All form elements connected to backend
- ✅ Tab navigation working
- ✅ Real-time form updates

## Recent Updates ✨
- **Save JSON Button**: Renamed from "Save Draft" to "Save JSON"
- **JSON Export**: Complete form data export functionality
- **Dual Download**: Both client-side and server-side download methods
- **Export Endpoint**: New API endpoint for server-side JSON export
- **Structured Export**: Comprehensive data structure with metadata

## Next Steps
The brand registration system is now complete with full JSON export capabilities. Users can:
1. Upload brand guideline documents
2. Configure default settings (language, LLM, product percentage)
3. Create detailed brand blueprints with voice profiles and content pillars
4. Set brand policies including forbidden phrases and hashtags
5. Export all data as JSON file for backup or integration purposes
6. All data is automatically saved and can be exported on demand

The system provides a solid foundation for AI-powered brand content management with complete data portability.