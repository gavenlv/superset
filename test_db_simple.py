#!/usr/bin/env python3
"""
Simple database test script
"""

import os
import sys

# Set config path
os.environ['SUPERSET_CONFIG_PATH'] = r'D:\workspace\superset-github\superset\superset_config.py'

def test_postgresql():
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        
        print("Testing PostgreSQL connection...")
        conn = psycopg2.connect(
            host='localhost',
            port=25011,
            database='superset_db',
            user='superset_user',
            password='superset_password'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✓ PostgreSQL connected: {version[:50]}...")
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"✓ Found {len(tables)} tables")
        
        if len(tables) > 0:
            print("Tables:", ", ".join(tables[:10]))
            if len(tables) > 10:
                print(f"... and {len(tables) - 10} more")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL connection failed: {e}")
        return False

def test_superset_import():
    """Test Superset import"""
    try:
        print("Testing Superset import...")
        from superset.app import create_app
        print("✓ Superset import successful")
        
        print("Creating Superset app...")
        app = create_app()
        print("✓ Superset app created")
        return True
        
    except Exception as e:
        print(f"✗ Superset import/creation failed: {e}")
        return False

def main():
    print("=== Simple Database Test ===")
    
    # Test 1: PostgreSQL
    pg_ok = test_postgresql()
    
    # Test 2: Superset
    if pg_ok:
        superset_ok = test_superset_import()
    else:
        print("Skipping Superset test due to PostgreSQL failure")
        superset_ok = False
    
    print("\n=== Summary ===")
    print(f"PostgreSQL: {'✓ OK' if pg_ok else '✗ FAILED'}")
    print(f"Superset:   {'✓ OK' if superset_ok else '✗ FAILED'}")
    
    if pg_ok and superset_ok:
        print("\n🎉 All tests passed! Database is ready.")
    elif pg_ok:
        print("\n⚠️  PostgreSQL OK, but Superset needs initialization.")
        print("Run: superset db upgrade")
    else:
        print("\n❌ PostgreSQL connection failed. Check your database.")

if __name__ == "__main__":
    main() 