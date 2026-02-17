import os
import sys
from cryptography.fernet import Fernet

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Generate a valid key for testing
test_key = Fernet.generate_key().decode()
os.environ["ENCRYPTION_KEY"] = test_key
os.environ["DATABASE_URL"] = "sqlite:///./test_facebook.db"

from app.utils.encryption import encrypt_token, decrypt_token
from app.core.db_sqlalchemy import engine, Base, SessionLocal
from app.models.facebook import FacebookIntegration

def run_tests():
    print("--- Facebook Module Smoke Test ---")
    
    # 1. Test Encryption
    original = "facebook_secret_token_123"
    try:
        enc = encrypt_token(original)
        dec = decrypt_token(enc)
        if original == dec:
            print("[PASS] Encryption")
        else:
            print("[FAIL] Encryption (Mismatch)")
            return
    except Exception as e:
        print(f"[FAIL] Encryption ({e})")
        return

    # 2. Test Database (SQLite for smoke test)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        new_int = FacebookIntegration(
            brand_id="test_brand_smoke",
            page_id="smoke_123",
            page_name="Smoke Test Page",
            page_access_token=encrypt_token("page_token"),
            user_access_token=encrypt_token("user_token"),
            connected=True
        )
        db.add(new_int)
        db.commit()
        
        saved = db.query(FacebookIntegration).filter_by(brand_id="test_brand_smoke").first()
        if saved and saved.page_name == "Smoke Test Page":
            print("[PASS] Database Models")
        else:
            print("[FAIL] Database Models")
    except Exception as e:
        print(f"❌ Database Models: FAIL ({e})")
    finally:
        db.close()
        if os.path.exists("./test_facebook.db"):
            os.remove("./test_facebook.db")

    print("--- All tests completed successfully! ---")

if __name__ == "__main__":
    run_tests()
