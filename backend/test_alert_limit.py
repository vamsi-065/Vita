import os
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Must set the environment var to not conflict, or just let it use sqlite
os.environ["DATABASE_URL"] = "sqlite:///./sql_app.db"

def test_chat_endpoint():
    from app.main import app
    from app.core.database import engine

    client = TestClient(app)
    
    # 1. Setup DB
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS inventory (id INTEGER PRIMARY KEY, item_name TEXT, quantity INTEGER, status TEXT, alert_limit INTEGER);"))
        conn.execute(text("DELETE FROM inventory WHERE item_name = 'Eggs';"))
        conn.execute(text("INSERT INTO inventory (item_name, quantity, status) VALUES ('Eggs', 10, 'In Stock');"))
        conn.commit()

    # 2. Test set limit command
    print("Sending command: 'set limit 5 for eggs'")
    response = client.post("/api/v1/chat/", json={"message": "set limit 5 for eggs"})
    
    assert response.status_code == 200, f"Request failed: {response.text}"
    data = response.json()
    
    print("Response message:", data.get("message"))
    assert "Alert limit for" in data.get("message") and "has been set to 5" in data.get("message"), "Unexpected success message"
    
    # 3. Verify in DB
    with engine.connect() as conn:
        res = conn.execute(text("SELECT alert_limit FROM inventory WHERE item_name ILIKE '%eggs%'")).fetchone()
        assert res[0] == 5, f"Expected alert_limit 5, got {res[0]}"
        print("Database updated correctly.")
        
    # 4. Test non-existent product
    print("Sending command: 'set limit 10 for unicorns'")
    response = client.post("/api/v1/chat/", json={"message": "set limit 10 for unicorns"})
    assert response.status_code == 200
    data = response.json()
    print("Response message:", data.get("message"))
    assert "Product not found" in data.get("message"), "Did not receive Product not found error"

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    test_chat_endpoint()
    print("All tests passed successfully!")
