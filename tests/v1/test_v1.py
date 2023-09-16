import pytest
from fastapi.testclient import TestClient
import server

client = TestClient(server.app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"detail": "rug-api"}
