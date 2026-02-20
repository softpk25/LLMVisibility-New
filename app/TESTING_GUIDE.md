# Facebook Module Testing Guide

This guide provides steps to verify the functionality of the Facebook integration module.

## 1. Prerequisites
Before testing, ensure you have followed the [Setup Instructions](file:///c:/Users/acer/Desktop/SMM-final/LLMVisibility-New/app/SETUP_INSTRUCTIONS.md) and have the following running:
- **SQLite**: Local database created automatically.
- **Redis**: Required for token caching.
- **FastAPI Server**: Run with `python backend/main.py`.

## 2. Automated Smoke Test
I have provided a smoke test script `backend/test_facebook_logic.py` to verify encryption and database models without needing a real Facebook connection.

Run it using:
```bash
python backend/test_facebook_logic.py
```

## 3. Manual Verification (via Swagger UI)
Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### A. Connectivity Test
1. Locate the `GET /api/v1/facebook/status` endpoint.
2. Click "Try it out" and enter a `brand_id` (e.g., `test_brand_123`).
3. Execute. You should receive a `connected: false` response (as no account is linked yet).

### B. Mocking the OAuth Flow
Since real Facebook credentials require an app setup, you can test the database integration by manually triggering the callback:
1. Copy this URL (replace with your local host if different):
   `http://localhost:8000/api/v1/auth/facebook/callback?code=mock_code&state=test_brand_123`
2. Open it in your browser.
3. You should see a success message: `Connected to page: ...`.

### C. Verify Linked Status
1. Go back to `GET /api/v1/facebook/status` for `test_brand_123`.
2. Execute again. It should now show `connected: true` and the page name.

### D. Publishing Test (Mocked)
1. Locate `POST /api/v1/facebook/publish/post`.
2. Enter `brand_id`: `test_brand_123`.
3. Enter Body:
   ```json
   {
     "message": "Hello from Prometrix!",
     "link": "https://example.com"
   }
   ```
4. Execute. Note: Without a real token, the Graph API will return an error, but the request flow is now verified.

## 4. Troubleshooting
- **Database Error**: Ensure `DATABASE_URL` in `.env` is correct and PostgreSQL is accessible.
- **Encryption Error**: Ensure `ENCRYPTION_KEY` is a valid 32-byte base64 string (generate using the tip in Setup Instructions).
- **Redis Error**: Ensure Redis is running and `REDIS_URL` is set.
