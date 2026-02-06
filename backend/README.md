# Prometrix Backend

Production-ready FastAPI backend for the Prometrix AI-powered Facebook Social Media Marketing Agent platform.

## Features

- **Campaign Management**: Create, manage, and optimize social media campaigns
- **Brand Registration**: Upload brand guidelines and generate AI-powered brand blueprints
- **Inspire Me**: AI-powered creative content generation with Visual DNA analysis
- **Engage Boost**: Intelligent comment analysis and automated response generation
- **Settings Management**: Comprehensive platform configuration and integrations
- **LLM Orchestration**: Provider-agnostic AI integration supporting OpenAI, Anthropic, and Google
- **JSON-First Storage**: Versioned JSON file storage with easy database migration path

## Architecture

### Tech Stack
- **Framework**: FastAPI with async/await support
- **Data Validation**: Pydantic v2 with comprehensive schemas
- **Storage**: JSON-based file storage (production-ready, database-migration friendly)
- **LLM Integration**: Provider-agnostic orchestration layer
- **Authentication**: JWT-ready (stubbed for development)
- **Logging**: Structured logging with configurable levels
- **Error Handling**: Centralized exception handling

### Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── core/                   # Core configuration and utilities
│   ├── config.py          # Application settings
│   ├── logging_config.py  # Logging configuration
│   └── exceptions.py      # Custom exceptions and handlers
├── schemas/               # Pydantic data models
│   ├── campaign.py        # Campaign-related schemas
│   ├── brand.py          # Brand registration schemas
│   ├── inspire.py        # Creative generation schemas
│   ├── engage.py         # Comment engagement schemas
│   └── settings.py       # Settings and configuration schemas
├── services/              # Business logic layer
│   ├── llm_orchestrator.py # LLM provider abstraction
│   └── storage.py         # JSON storage implementation
├── api/                   # API endpoints
│   └── v1/               # API version 1
│       ├── router.py     # Main API router
│       ├── campaigns.py  # Campaign endpoints
│       ├── brands.py     # Brand registration endpoints
│       ├── inspire.py    # Creative generation endpoints
│       ├── engage.py     # Comment engagement endpoints
│       └── settings.py   # Settings endpoints
├── data/                  # JSON data storage (created automatically)
├── uploads/              # File uploads (created automatically)
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md           # This file
```

## Quick Start

### 1. Installation

```bash
# Navigate to backend directory
cd LLMVisibility-New/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env file with your settings
# At minimum, add your LLM provider API keys:
# OPENAI_API_KEY=your-openai-key
# ANTHROPIC_API_KEY=your-anthropic-key
```

### 3. Run the Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### 4. API Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Modules

### 1. Campaign Management (`/api/v1/campaigns`)

- `POST /campaigns/create` - Create new campaign
- `POST /campaigns/post-mix` - Configure post type distribution
- `GET /campaigns/{campaign_id}` - Get campaign details
- `GET /campaigns/` - List campaigns with pagination
- `PUT /campaigns/{campaign_id}/post` - Update post content
- `DELETE /campaigns/{campaign_id}` - Delete campaign

### 2. Brand Registration (`/api/v1/brands`)

- `POST /brands/register` - Register new brand
- `POST /brands/upload` - Upload brand guideline documents
- `POST /brands/extract/{file_id}` - Extract guidelines using AI
- `PUT /brands/{brand_id}/blueprint` - Update brand blueprint
- `GET /brands/{brand_id}` - Get brand details
- `GET /brands/` - List brands
- `DELETE /brands/{brand_id}` - Delete brand

### 3. Inspire Me (`/api/v1/inspire`)

- `POST /inspire/upload` - Upload creative reference files
- `POST /inspire/analyze` - Generate Visual DNA analysis
- `POST /inspire/generate` - Generate creative content
- `POST /inspire/edit-prompt` - Edit prompts with sliders
- `GET /inspire/assets` - List creative assets
- `GET /inspire/generations/{generation_id}` - Get generation results
- `DELETE /inspire/assets/{asset_id}` - Delete creative asset

### 4. Engage Boost (`/api/v1/engage`)

- `POST /engage/comment` - Analyze comment and generate response
- `POST /engage/decision` - Approve/reject/edit AI responses
- `GET /engage/comments` - List analyzed comments
- `GET /engage/analytics` - Get engagement analytics
- `POST /engage/templates` - Create response templates
- `GET /engage/templates` - List response templates

### 5. Settings (`/api/v1/settings`)

- `GET/PUT /settings/language` - Language configuration
- `GET/PUT /settings/llm` - LLM provider settings
- `GET/PUT /settings/guardrails` - Content safety settings
- `GET/PUT /settings/content` - Content generation settings
- `GET/PUT /settings/sector` - Industry sector settings
- `GET/PUT /settings/integrations/{platform}` - Platform integrations
- `GET/POST/PUT/DELETE /settings/personas` - Persona management
- `GET/POST/PUT/DELETE /settings/products` - Product catalog management

## LLM Integration

The backend includes a provider-agnostic LLM orchestration layer that supports:

### Supported Providers
- **OpenAI**: GPT-4, GPT-4 Vision, text-moderation
- **Anthropic**: Claude 3 (Sonnet, Haiku, Opus)
- **Google**: Gemini Pro (planned)
- **Mock Provider**: For testing and development

### Usage Example

```python
from services.llm_orchestrator import orchestrator

# Generate text content
payload = {
    "task_type": "text_generation",
    "prompt": "Create a social media caption for a tech product",
    "parameters": {
        "max_tokens": 500,
        "temperature": 0.7
    }
}

result = await orchestrator.generate(payload, provider="openai")
```

### Provider Configuration

Configure providers in your `.env` file:

```env
# Primary provider
DEFAULT_LLM_PROVIDER=openai

# API keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# Model settings
DEFAULT_MODEL=gpt-4
MAX_TOKENS=2000
TEMPERATURE=0.7
```

## Data Storage

The backend uses a JSON-first storage approach that provides:

- **Immediate functionality**: No database setup required
- **Version control friendly**: JSON files can be tracked in git
- **Easy migration**: Simple transition to database when needed
- **Atomic operations**: Safe concurrent access with file locking
- **Structured data**: Full Pydantic validation

### Storage Collections

Data is organized into collections:

- `campaigns/` - Campaign data and metadata
- `brands/` - Brand information and guidelines
- `inspire_assets/` - Creative reference files
- `inspire_analyses/` - Visual DNA analysis results
- `inspire_generations/` - Generated content variants
- `engage_analyses/` - Comment analysis results
- `engage_decisions/` - Human review decisions
- `settings/` - Platform configuration
- `personas/` - Target audience personas
- `products/` - Product catalog

### Example Data Structure

```json
{
  "id": "campaign-uuid",
  "campaign_metadata": {
    "name": "Summer Campaign 2024",
    "objective": "awareness",
    "status": "active"
  },
  "brand_context": {
    "brand_id": "brand-uuid",
    "voice_profile": {...},
    "content_pillars": [...]
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "version": "v1"
}
```

## Frontend Integration

The backend is designed to work seamlessly with the existing HTML frontend:

### Campaign Creation Flow
1. Frontend sends campaign data to `POST /api/v1/campaigns/create`
2. Backend validates data, creates campaign JSON
3. Backend generates content plan using LLM
4. Frontend receives campaign ID and can fetch full data

### Brand Registration Flow
1. Frontend uploads guidelines to `POST /api/v1/brands/upload`
2. Backend extracts content using AI via `POST /api/v1/brands/extract/{file_id}`
3. Frontend creates brand with extracted data via `POST /api/v1/brands/register`
4. Backend generates brand blueprint using LLM

### Creative Generation Flow
1. Frontend uploads references to `POST /api/v1/inspire/upload`
2. Backend analyzes visual DNA via `POST /api/v1/inspire/analyze`
3. Frontend generates content via `POST /api/v1/inspire/generate`
4. Backend returns multiple variants with metadata

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html
```

### Code Structure Guidelines

- **Async First**: All operations use async/await
- **Type Hints**: Full type annotations throughout
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging for debugging
- **Validation**: Pydantic schemas for all data
- **Separation of Concerns**: Clear API/Service/Storage layers

### Adding New Endpoints

1. Define Pydantic schemas in `schemas/`
2. Implement business logic in `services/`
3. Create API endpoints in `api/v1/`
4. Add route to main router
5. Update documentation

## Production Deployment

### Environment Variables

Set these environment variables for production:

```env
DEBUG=false
SECRET_KEY=your-production-secret-key
ALLOWED_ORIGINS=https://yourdomain.com
LOG_LEVEL=WARNING
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Database Migration

When ready to migrate from JSON to database:

1. Choose database (PostgreSQL recommended)
2. Install SQLAlchemy + Alembic
3. Create database models matching Pydantic schemas
4. Write migration script to import JSON data
5. Update storage service to use database

The JSON structure is designed to map directly to database tables.

## Troubleshooting

### Common Issues

1. **LLM Provider Errors**: Check API keys in `.env` file
2. **File Upload Issues**: Verify `UPLOAD_DIR` permissions
3. **Storage Errors**: Check `DATA_DIR` write permissions
4. **CORS Issues**: Update `ALLOWED_ORIGINS` in configuration

### Logging

Enable debug logging:

```env
LOG_LEVEL=DEBUG
```

Check logs for detailed error information and request tracing.

## Contributing

1. Follow existing code structure and patterns
2. Add comprehensive error handling
3. Include type hints and docstrings
4. Write tests for new functionality
5. Update documentation

## License

This project is part of the Prometrix platform. See main project license for details.