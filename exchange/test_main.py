import pytest
from httpx import AsyncClient
from .main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Exchange"}

@pytest.mark.asyncio
async def test_convert_currency():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/convert")
    
    assert response.status_code == 200
    response_data = response.json()
    assert "exchange_rate" in response_data
    
    rate = response_data["exchange_rate"]
    assert isinstance(rate, float)
    assert 5.0 <= rate <= 6.0