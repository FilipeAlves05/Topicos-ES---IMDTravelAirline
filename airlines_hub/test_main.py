import pytest
from httpx import AsyncClient
from .main import app, FLIGHTS_DATABASE

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "AirlinesHub"}

@pytest.mark.asyncio
async def test_get_flight_exists():
    flight_num = "AA100"
    day = "2025-01-15"
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/flight", params={"flight": flight_num, "day": day})
    
    assert response.status_code == 200
    
    assert response.json() == FLIGHTS_DATABASE[flight_num][day]

@pytest.mark.asyncio
async def test_get_flight_not_found_returns_default():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/flight", params={"flight": "ZZ999", "day": "2030-01-01"})
    
    assert response.status_code == 200
    assert response.json()["flight"] == "ZZ999"
    assert response.json()["value"] == 500.00

@pytest.mark.asyncio
async def test_sell_flight():
    request_data = {"flight": "DL300", "day": "2025-02-10"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/sell", json=request_data)
    
    assert response.status_code == 200
    response_data = response.json()
    assert "transaction_id" in response_data
    assert isinstance(response_data["transaction_id"], str)
