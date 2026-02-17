from sqlalchemy import Column, String, Integer, DateTime, Boolean
from app.core.db_sqlalchemy import Base
import datetime

class FacebookIntegration(Base):
    """
    Model for storing Facebook account and page integration details.
    Tokens are stored in encrypted format.
    """
    __tablename__ = "facebook_integrations"

    id = Column(Integer, primary_key=True, index=True)
    brand_id = Column(String, index=True, nullable=False)
    facebook_user_id = Column(String, nullable=True)
    page_id = Column(String, unique=True, index=True, nullable=False)
    page_name = Column(String, nullable=False)
    page_access_token = Column(String, nullable=False)  # Encrypted
    user_access_token = Column(String, nullable=False)  # Encrypted
    token_expiry = Column(DateTime, nullable=True)
    connected = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
