"""
Test Infrastructure Setup for Brand Blueprint Integration
Tests Task 4: Checkpoint - Verify infrastructure setup

This test verifies:
- All imports are working correctly
- The lifespan function is properly implemented
- The database can be initialized
- The uploads/guidelines directory is created
- No errors occur during server initialization
"""

import pytest
import sys
from pathlib import Path
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestImports:
    """Test that all imports work correctly"""
    
    def test_app_config_import(self):
        """Test that app.config can be imported"""
        from app.config import get_settings, Settings
        assert get_settings is not None
        assert Settings is not None
    
    def test_app_database_import(self):
        """Test that app.database can be imported"""
        from app.database import init_db, get_db, Base
        assert init_db is not None
        assert get_db is not None
        assert Base is not None
    
    def test_app_models_import(self):
        """Test that app.models can be imported"""
        from app.models import (
            BrandBlueprint,
            BrandBlueprintRequest,
            BrandBlueprintResponse,
            VoiceProfile,
            ContentPillar,
            Policies,
            BlueprintData
        )
        assert BrandBlueprint is not None
        assert BrandBlueprintRequest is not None
        assert BrandBlueprintResponse is not None
    
    def test_app_main_import(self):
        """Test that app.main can be imported"""
        from app.main import blueprint_router
        assert blueprint_router is not None
    
    def test_app_services_pdf_processor_import(self):
        """Test that app.services.pdf_processor can be imported"""
        from app.services.pdf_processor import PDFProcessor
        assert PDFProcessor is not None
    
    def test_no_standalone_imports_in_database(self):
        """Verify no STANDALONE imports remain in app/database.py"""
        database_file = project_root / "app" / "database.py"
        content = database_file.read_text(encoding='utf-8')
        
        assert "STANDALONE_CONFIG" not in content, "Found STANDALONE_CONFIG import in database.py"
        assert "STANDALONE_MODELS" not in content, "Found STANDALONE_MODELS import in database.py"
        assert "from app.config import" in content, "Missing app.config import in database.py"
        assert "from app.models import" in content, "Missing app.models import in database.py"
    
    def test_no_standalone_imports_in_models(self):
        """Verify no STANDALONE imports remain in app/models.py"""
        models_file = project_root / "app" / "models.py"
        content = models_file.read_text(encoding='utf-8')
        
        assert "STANDALONE_DATABASE" not in content, "Found STANDALONE_DATABASE import in models.py"
        assert "from app.database import" in content, "Missing app.database import in models.py"
    
    def test_no_standalone_imports_in_main(self):
        """Verify no STANDALONE imports remain in app/main.py"""
        main_file = project_root / "app" / "main.py"
        content = main_file.read_text(encoding='utf-8')
        
        assert "STANDALONE_CONFIG" not in content, "Found STANDALONE_CONFIG import in main.py"
        assert "STANDALONE_DATABASE" not in content, "Found STANDALONE_DATABASE import in main.py"
        assert "STANDALONE_MODELS" not in content, "Found STANDALONE_MODELS import in main.py"
        assert "from app.config import" in content, "Missing app.config import in main.py"
        assert "from app.database import" in content, "Missing app.database import in main.py"
        assert "from app.models import" in content, "Missing app.models import in main.py"
    
    def test_no_standalone_imports_in_pdf_processor(self):
        """Verify no standalone config imports remain in app/services/pdf_processor.py"""
        pdf_processor_file = project_root / "app" / "services" / "pdf_processor.py"
        content = pdf_processor_file.read_text(encoding='utf-8')
        
        # Check for old import patterns
        assert "from config import" not in content or "from app.config import" in content, \
            "Found standalone config import in pdf_processor.py"
        assert "from app.config import" in content, "Missing app.config import in pdf_processor.py"


class TestLifespanFunction:
    """Test that the lifespan function is properly implemented"""
    
    def test_lifespan_function_exists(self):
        """Test that lifespan function exists in server.py"""
        server_file = project_root / "server.py"
        content = server_file.read_text(encoding='utf-8')
        
        assert "async def lifespan" in content, "Lifespan function not found in server.py"
        assert "@asynccontextmanager" in content, "asynccontextmanager decorator not found"
        assert "from contextlib import asynccontextmanager" in content, \
            "asynccontextmanager import not found"
    
    def test_lifespan_calls_init_db(self):
        """Test that lifespan function calls init_db()"""
        server_file = project_root / "server.py"
        content = server_file.read_text(encoding='utf-8')
        
        assert "init_db()" in content, "init_db() call not found in lifespan function"
        assert "from app.database import init_db" in content, \
            "init_db import not found in server.py"
    
    def test_lifespan_creates_uploads_directory(self):
        """Test that lifespan function creates uploads/guidelines directory"""
        server_file = project_root / "server.py"
        content = server_file.read_text(encoding='utf-8')
        
        assert "uploads/guidelines" in content, "uploads/guidelines path not found in lifespan"
        assert "mkdir" in content, "mkdir call not found in lifespan function"
    
    def test_fastapi_app_uses_lifespan(self):
        """Test that FastAPI app is initialized with lifespan parameter"""
        server_file = project_root / "server.py"
        content = server_file.read_text(encoding='utf-8')
        
        assert "FastAPI(lifespan=lifespan)" in content, \
            "FastAPI app not initialized with lifespan parameter"


class TestDatabaseInitialization:
    """Test that the database can be initialized"""
    
    def test_database_initialization(self):
        """Test that init_db() can be called without errors"""
        from app.database import init_db
        
        # This should not raise any exceptions
        try:
            init_db()
        except Exception as e:
            pytest.fail(f"Database initialization failed: {e}")
    
    def test_database_tables_created(self):
        """Test that database tables are created"""
        from app.database import init_db, engine
        from sqlalchemy import inspect
        
        # Initialize database
        init_db()
        
        # Check that tables exist
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        assert "brand_blueprints" in tables, "brand_blueprints table not created"
    
    def test_brand_blueprint_table_schema(self):
        """Test that brand_blueprints table has correct columns"""
        from app.database import init_db, engine
        from sqlalchemy import inspect
        
        # Initialize database
        init_db()
        
        # Check table columns
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('brand_blueprints')]
        
        required_columns = [
            'id', 'brand_id', 'brand_name', 'version', 'status',
            'voice_formality', 'voice_humor', 'voice_warmth', 'emoji_policy',
            'pillars', 'forbidden_phrases', 'max_hashtags', 'brand_hashtags',
            'product_default_pct', 'guideline_doc_name', 'guideline_doc_status',
            'created_at', 'updated_at'
        ]
        
        for col in required_columns:
            assert col in columns, f"Column '{col}' not found in brand_blueprints table"


class TestDirectoryCreation:
    """Test that required directories are created"""
    
    def test_uploads_guidelines_directory_exists(self):
        """Test that uploads/guidelines directory exists"""
        uploads_dir = project_root / "uploads" / "guidelines"
        assert uploads_dir.exists(), "uploads/guidelines directory does not exist"
        assert uploads_dir.is_dir(), "uploads/guidelines is not a directory"
    
    def test_uploads_directory_is_writable(self):
        """Test that uploads/guidelines directory is writable"""
        uploads_dir = project_root / "uploads" / "guidelines"
        test_file = uploads_dir / "test_write.txt"
        
        try:
            test_file.write_text("test")
            test_file.unlink()  # Clean up
        except Exception as e:
            pytest.fail(f"uploads/guidelines directory is not writable: {e}")


class TestServerInitialization:
    """Test that server can be initialized without errors"""
    
    def test_server_module_import(self):
        """Test that server.py can be imported"""
        try:
            import server
        except Exception as e:
            pytest.fail(f"Failed to import server module: {e}")
    
    def test_fastapi_app_exists(self):
        """Test that FastAPI app instance exists"""
        import server
        assert hasattr(server, 'app'), "FastAPI app instance not found in server module"
        assert server.app is not None, "FastAPI app instance is None"
    
    def test_app_has_lifespan(self):
        """Test that FastAPI app has lifespan configured"""
        import server
        # Check if the app was created with lifespan
        # This is implicit in the app creation, so we check the server.py content
        server_file = project_root / "server.py"
        content = server_file.read_text(encoding='utf-8')
        assert "FastAPI(lifespan=lifespan)" in content


class TestRouterConfiguration:
    """Test that blueprint_router is properly configured"""
    
    def test_blueprint_router_is_api_router(self):
        """Test that blueprint_router is an APIRouter instance"""
        from app.main import blueprint_router
        from fastapi import APIRouter
        
        assert isinstance(blueprint_router, APIRouter), \
            "blueprint_router is not an APIRouter instance"
    
    def test_blueprint_router_has_routes(self):
        """Test that blueprint_router has routes registered"""
        from app.main import blueprint_router
        
        routes = blueprint_router.routes
        assert len(routes) > 0, "blueprint_router has no routes registered"
        
        # Check for expected routes
        route_paths = [route.path for route in routes]
        
        expected_paths = [
            "/api/brand/upload-guideline",
            "/api/brand/blueprint",
            "/brand-blueprint"
        ]
        
        for path in expected_paths:
            assert path in route_paths, f"Expected route '{path}' not found in blueprint_router"


class TestEnvironmentConfiguration:
    """Test that environment configuration is working"""
    
    def test_env_file_exists(self):
        """Test that .env file exists"""
        env_file = project_root / ".env"
        assert env_file.exists(), ".env file does not exist"
    
    def test_settings_can_be_loaded(self):
        """Test that settings can be loaded from .env"""
        from app.config import get_settings
        
        settings = get_settings()
        assert settings is not None, "Settings could not be loaded"
    
    def test_database_url_is_configured(self):
        """Test that DATABASE_URL is configured"""
        from app.config import get_settings
        
        settings = get_settings()
        assert settings.DATABASE_URL, "DATABASE_URL is not configured"
        assert len(settings.DATABASE_URL) > 0, "DATABASE_URL is empty"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
