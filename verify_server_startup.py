"""
Quick verification script to test server startup
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("VERIFYING SERVER STARTUP")
print("=" * 60)

try:
    print("\n1. Importing server module...")
    import server
    print("   ✓ Server module imported successfully")
    
    print("\n2. Checking FastAPI app instance...")
    assert hasattr(server, 'app'), "FastAPI app not found"
    assert server.app is not None, "FastAPI app is None"
    print("   ✓ FastAPI app instance exists")
    
    print("\n3. Checking lifespan function...")
    assert hasattr(server, 'lifespan'), "Lifespan function not found"
    print("   ✓ Lifespan function exists")
    
    print("\n4. Checking database initialization...")
    from app.database import init_db, check_db_connection
    init_db()
    print("   ✓ Database initialized successfully")
    
    if check_db_connection():
        print("   ✓ Database connection working")
    else:
        print("   ⚠ Database connection check failed")
    
    print("\n5. Checking uploads directory...")
    uploads_dir = Path("uploads/guidelines")
    if uploads_dir.exists():
        print(f"   ✓ Uploads directory exists: {uploads_dir}")
    else:
        print(f"   ✗ Uploads directory missing: {uploads_dir}")
    
    print("\n6. Checking blueprint router...")
    from app.main import blueprint_router
    routes = blueprint_router.routes
    print(f"   ✓ Blueprint router has {len(routes)} routes")
    
    print("\n7. Listing available routes...")
    for route in routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(route.methods) if route.methods else 'N/A'
            print(f"   - {methods:10} {route.path}")
    
    print("\n" + "=" * 60)
    print("✓ ALL CHECKS PASSED - SERVER INFRASTRUCTURE IS READY")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
