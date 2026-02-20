"""
JSON-based storage service for Prometrix backend
"""

import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from core.config import settings
from core.logging_config import get_logger
from core.exceptions import StorageError, NotFoundError

logger = get_logger("storage")


class JSONStorage:
    """JSON-based storage implementation"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or settings.DATA_DIR)
        self.base_dir.mkdir(exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create a lock for a specific key"""
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]
    
    def _get_file_path(self, collection: str, item_id: str) -> Path:
        """Get file path for an item"""
        collection_dir = self.base_dir / collection
        collection_dir.mkdir(exist_ok=True)
        return collection_dir / f"{item_id}.json"
    
    def _get_collection_dir(self, collection: str) -> Path:
        """Get collection directory"""
        collection_dir = self.base_dir / collection
        collection_dir.mkdir(exist_ok=True)
        return collection_dir
    
    async def save(self, collection: str, item_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save data to JSON file"""
        lock_key = f"{collection}:{item_id}"
        
        async with self._get_lock(lock_key):
            try:
                file_path = self._get_file_path(collection, item_id)
                
                # Add metadata
                now = datetime.utcnow()
                if "created_at" not in data:
                    data["created_at"] = now.isoformat()
                data["updated_at"] = now.isoformat()
                
                # Write to temporary file first, then rename (atomic operation)
                temp_path = file_path.with_suffix('.tmp')
                
                with open(temp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
                import os
                os.replace(str(temp_path), str(file_path))
                
                logger.debug(f"Saved {collection}/{item_id}")
                return data
                
            except Exception as e:
                logger.error(f"Failed to save {collection}/{item_id}: {e}")
                raise StorageError("save", f"Failed to save {collection}/{item_id}: {str(e)}")
    
    async def load(self, collection: str, item_id: str) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            file_path = self._get_file_path(collection, item_id)
            
            if not file_path.exists():
                raise NotFoundError(f"{collection}/{item_id}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded {collection}/{item_id}")
            return data
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load {collection}/{item_id}: {e}")
            raise StorageError("load", f"Failed to load {collection}/{item_id}: {str(e)}")
    
    async def delete(self, collection: str, item_id: str) -> bool:
        """Delete item from storage"""
        lock_key = f"{collection}:{item_id}"
        
        async with self._get_lock(lock_key):
            try:
                file_path = self._get_file_path(collection, item_id)
                
                if not file_path.exists():
                    return False
                
                file_path.unlink()
                logger.debug(f"Deleted {collection}/{item_id}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete {collection}/{item_id}: {e}")
                raise StorageError("delete", f"Failed to delete {collection}/{item_id}: {str(e)}")
    
    async def list_items(self, collection: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List items in collection"""
        try:
            collection_dir = self._get_collection_dir(collection)
            
            # Get all JSON files
            json_files = list(collection_dir.glob("*.json"))
            json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Sort by modification time
            
            # Apply pagination
            paginated_files = json_files[offset:offset + limit]
            
            items = []
            for file_path in paginated_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    items.append(data)
                except Exception as e:
                    logger.warning(f"Failed to load {file_path}: {e}")
                    continue
            
            logger.debug(f"Listed {len(items)} items from {collection}")
            return items
            
        except Exception as e:
            logger.error(f"Failed to list {collection}: {e}")
            raise StorageError("list", f"Failed to list {collection}: {str(e)}")
    
    async def count_items(self, collection: str) -> int:
        """Count items in collection"""
        try:
            collection_dir = self._get_collection_dir(collection)
            json_files = list(collection_dir.glob("*.json"))
            return len(json_files)
            
        except Exception as e:
            logger.error(f"Failed to count {collection}: {e}")
            raise StorageError("count", f"Failed to count {collection}: {str(e)}")
    
    async def exists(self, collection: str, item_id: str) -> bool:
        """Check if item exists"""
        file_path = self._get_file_path(collection, item_id)
        return file_path.exists()
    
    async def search(self, collection: str, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Simple search within collection"""
        try:
            all_items = await self.list_items(collection, limit=1000)  # Get more items for search
            
            results = []
            for item in all_items:
                match = True
                for key, value in query.items():
                    if key not in item or item[key] != value:
                        match = False
                        break
                
                if match:
                    results.append(item)
                    if len(results) >= limit:
                        break
            
            logger.debug(f"Search in {collection} returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search {collection}: {e}")
            raise StorageError("search", f"Failed to search {collection}: {str(e)}")


class CampaignStorage:
    """Campaign-specific storage operations"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
        self.collection = "campaigns"
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign"""
        campaign_id = str(uuid.uuid4())
        campaign_data["id"] = campaign_id
        
        await self.storage.save(self.collection, campaign_id, campaign_data)
        return campaign_id
    
    async def get_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Get campaign by ID"""
        return await self.storage.load(self.collection, campaign_id)
    
    async def update_campaign(self, campaign_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign"""
        campaign_data = await self.get_campaign(campaign_id)
        campaign_data.update(updates)
        await self.storage.save(self.collection, campaign_id, campaign_data)
        return campaign_data
    
    async def list_campaigns(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List campaigns"""
        return await self.storage.list_items(self.collection, limit, offset)
    
    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete campaign"""
        return await self.storage.delete(self.collection, campaign_id)


class BrandStorage:
    """Brand-specific storage operations"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
        self.collection = "brands"
    
    async def create_brand(self, brand_data: Dict[str, Any]) -> str:
        """Create a new brand"""
        brand_id = str(uuid.uuid4())
        brand_data["id"] = brand_id
        
        await self.storage.save(self.collection, brand_id, brand_data)
        return brand_id
    
    async def get_brand(self, brand_id: str) -> Dict[str, Any]:
        """Get brand by ID"""
        return await self.storage.load(self.collection, brand_id)
    
    async def update_brand(self, brand_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update brand"""
        brand_data = await self.get_brand(brand_id)
        brand_data.update(updates)
        await self.storage.save(self.collection, brand_id, brand_data)
        return brand_data
    
    async def list_brands(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List brands"""
        return await self.storage.list_items(self.collection, limit, offset)


class PersonaStorage:
    """Persona-specific storage operations"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
        self.collection = "personas"
    
    async def get_persona(self, persona_id: str) -> Dict[str, Any]:
        """Get persona by ID"""
        return await self.storage.load(self.collection, persona_id)
    
    async def list_personas(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List personas"""
        return await self.storage.list_items(self.collection, limit, offset)


class ProductStorage:
    """Product-specific storage operations"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
        self.collection = "products"
    
    async def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get product by ID"""
        return await self.storage.load(self.collection, product_id)
    
    async def list_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List products"""
        return await self.storage.list_items(self.collection, limit, offset)


class SettingsStorage:
    """Settings-specific storage operations"""
    
    def __init__(self, storage: JSONStorage):
        self.storage = storage
        self.collection = "settings"
    
    async def get_settings(self, settings_type: str) -> Dict[str, Any]:
        """Get settings by type"""
        try:
            return await self.storage.load(self.collection, settings_type)
        except NotFoundError:
            # Return default settings if not found
            return self._get_default_settings(settings_type)
    
    async def update_settings(self, settings_type: str, settings_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update settings"""
        await self.storage.save(self.collection, settings_type, settings_data)
        return settings_data
    
    def _get_default_settings(self, settings_type: str) -> Dict[str, Any]:
        """Get default settings for a type"""
        defaults = {
            "language": {
                "primary_language": "en",
                "supported_languages": ["en"],
                "auto_translate": False,
                "translation_quality": "standard"
            },
            "llm": {
                "primary_provider": "openai",
                "fallback_providers": [],
                "monthly_budget_limit": 100.0,
                "current_usage": 0.0,
                "models": {
                    "text_generation": "gpt-4",
                    "image_analysis": "gpt-4-vision-preview",
                    "content_moderation": "text-moderation-latest"
                }
            },
            "guardrails": {
                "forbidden_phrases": [],
                "required_disclaimers": [],
                "content_moderation_enabled": True,
                "profanity_filter": True,
                "political_content_filter": True,
                "adult_content_filter": True,
                "violence_filter": True
            },
            "content": {
                "emoji_policy": "moderate",
                "hashtag_limit": 10,
                "max_caption_length": 2200,
                "include_call_to_action": True,
                "brand_mention_frequency": 0.3
            }
        }
        
        return defaults.get(settings_type, {})


# Global storage instances
storage = JSONStorage()
campaign_storage = CampaignStorage(storage)
brand_storage = BrandStorage(storage)
persona_storage = PersonaStorage(storage)
product_storage = ProductStorage(storage)
settings_storage = SettingsStorage(storage)