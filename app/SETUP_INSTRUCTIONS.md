Follow these steps to configure and run the Facebook Account Linking & Publishing Module.

## 0. Run Setup Script (IMPORTANT)
The very first step is to run the setup script which installs all required dependencies and sets up the environment:
```bash
cd backend
python setup.py
```
This script will:
- Install core and Facebook-specific dependencies.
- Create a `.env` file from the template.
- Create necessary data directories.

## 1. Environment Variables
Add the following to your `.env` file:

```env
# Facebook App Credentials
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/api/v1/auth/facebook/callback

# Security
ENCRYPTION_KEY=your_fernet_key_here
WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token

# Infrastructure
# DATABASE_URL=sqlite:///./facebook_integrations.db
REDIS_URL=redis://localhost:6379/0
```

## 1.1 How to obtain these values

### Facebook App Credentials
1. Go to [Meta for Developers](https://developers.facebook.com/).
2. Click **My Apps** > **Create App**.
3. Select an app type (e.g., "Business" or "Consumer").
4. Once created, go to **App Settings** > **Basic** to find your **App ID** and **App Secret**.
5. Under **Facebook Login** > **Settings**, add `http://localhost:8000/api/v1/auth/facebook/callback` to the **Valid OAuth Redirect URIs**.

### Security Keys
- **ENCRYPTION_KEY**: Use the Python snippet below to generate a secure 32-byte key.
- **WEBHOOK_VERIFY_TOKEN**: This is a random string you create (e.g., `my_secure_token_2024`). You will enter the same string in the Facebook Developer Portal when setting up Webhooks.

### Infrastructure
- **DATABASE_URL**: Leave commented out to use the default `sqlite:///./facebook_integrations.db`.
- **REDIS_URL**: Usually `redis://localhost:6379/0` if running locally.

> [!TIP]
> To generate an `ENCRYPTION_KEY`, run:
> ```python
> from cryptography.fernet import Fernet
> print(Fernet.generate_key().decode())
> ```

## 2. Verify Dependencies
If you have run `python setup.py` in step 0, most dependencies should be installed. You can verify or install them manually if needed:
```bash
pip install sqlalchemy redis cryptography httpx
```

## 3. Database Initialization
The module automatically initializes a local SQLite database (`facebook_integrations.db`) on startup in `backend/main.py`. No additional database setup is required.

## 4. Running the Background Refresh Job
The token refresh job is implemented in `app/services/token_refresh_job.py`. In production, run this as a separate process or integrate it with a task scheduler:

```bash
python -m app.services.token_refresh_job
```

## 5. Webhook Configuration
1. Go to your Facebook App Dashboard.
2. Add the **Webhooks** product.
3. Set the Callback URL to: `https://your-domain.com/api/v1/webhook/facebook`
4. Set the Verify Token to match your `WEBHOOK_VERIFY_TOKEN`.
5. Subscribe to `feed`, `comments`, and `mention` events for `Page`.

## 6. Testing Endpoints
You can test the following endpoints via Swagger UI at `http://localhost:8000/docs`:
- `GET /api/v1/auth/facebook/login?brand_id=...`
- `POST /api/v1/facebook/publish/post`
- `GET /api/v1/facebook/status`
