# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

LLMVisibility (branded "VisualClone AI") is a Facebook social media marketing tool that uses AI to generate and transform ad creatives (images and videos). It has a FastAPI backend serving HTML template frontends. The core workflow is: upload inspiration media → AI analyzes it ("visual DNA") → generate new creatives based on that analysis.

## Running the Server

```bash
python server.py
```

Runs on `http://localhost:8000` using uvicorn. No separate build step; HTML templates are served directly.

## Environment Variables

All API keys live in a root `.env` file (never committed). Required keys:

- `OPENAI_API_KEY` — used by `ImageRater` for GPT-4o vision analysis, DALL-E 3 image generation, and gpt-image-1 transformations
- `GEMINI_API_KEY` — used by video modules for Gemini 2.0 Flash (video understanding) and Veo 3.1 (video generation)
- `KLING_ACCESS_KEY` / `KLING_SECRET_KEY` — used by Kling AI video inpainting (optional)

## Architecture

**Backend** — `server.py` is a single FastAPI app. All API endpoints are defined inline (no routers). Key endpoints:

| Endpoint | What it does |
|---|---|
| `POST /api/analyze-image` | Upload image → GPT-4o extracts structured "visual DNA" JSON |
| `POST /api/generate-creative` | Prompt → DALL-E 3 generates image, then auto-analyzes it |
| `POST /api/transform-image` | Base image + reference image → gpt-image-1 produces transformed creative |
| `POST /api/save-brief` | Saves creative brief JSON to `creative_briefs/` |
| `POST /api/generate-video` | Upload file → analyze → Gemini Veo generates video |
| `GET /FACEBOOK-INSPIRE-ME.html` | Serves the main "Inspire Me" UI |

**Core AI Module** — `inspire me/newimg.py` contains the `ImageRater` class which wraps all OpenAI interactions (vision analysis, DALL-E generation, image transformation via Responses API). This is the central intelligence layer.

**Video Pipeline** — `inspire me/video gen/` contains:
- `video_processor.py` — orchestrator: analyze input → build prompt → generate video
- `videounderstand.py` — Gemini-based video analysis (uploads video, returns descriptive prompt)
- `videogeneration.py` — Gemini Veo text-to-video generation
- `image_to_video.py` — CLI tool: image → OpenAI analysis → Gemini Veo video
- `klinggeneration.py` — Kling AI video inpainting (alternative video provider)

**Frontend** — Static HTML files in `templates/`. The main UI is `FACEBOOK-INSPIRE-ME.html`, a self-contained SPA with inline CSS/JS that calls the backend API endpoints via fetch.

## Module Import Pattern

The project uses `sys.path.append` to import across directories with spaces in names. `server.py` appends `inspire me/` to import `ImageRater` and appends `inspire me/video gen/` to import `video_processor`. When adding new modules, follow this same pattern.

## Auto-Created Directories

The server auto-creates these directories at startup (all gitignored): `generated/`, `creative_briefs/`, `temp_uploads/`, `transformed/`, `analyzed_images/`, `image_analysis/`.

## Key Data Flow

1. **Image Analysis**: Upload → `ImageRater.get_image_description()` → returns `{visual_dna, strategic_analysis, image_composition_analysis, prompt_reconstruction}` → saved to `image_analysis/`
2. **Image Generation**: prompt → `ImageRater.generate_image_dalle()` → saved to `generated/` with companion `.json` metadata
3. **Image Transformation**: base + reference images → `ImageRater.transform_image_with_reference()` (uses OpenAI Responses API with `gpt-4.1` model and `image_generation` tool) → saved to `transformed/`
4. **Video Generation**: file → `process_creative_request()` → analyze (OpenAI for images, Gemini for videos) → extract prompt → `generate_video()` via Gemini Veo → saved to `generated/`
