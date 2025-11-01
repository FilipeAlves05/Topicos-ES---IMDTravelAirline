import pytest
from httpx import AsyncClient, Response
from .main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "IMDTravel"}

@pytest.mark.asyncio
async def test_buy_ticket_success(mocker):
    mock_flight_response = {"flight": "AA100", "day": "2025-01-15", "value": 400.0}
    
    mock_exchange_response = {"exchange_rate": 5.5}
    
    mock_sell_response = {"transaction_id": "mock-tx-12345"}
    
    mock_bonus_response = {"status": "success", "message": "Bonus creditado"}

    mock_async_client = mocker.patch("httpx.AsyncClient", autospec=True)
    
    async def mock_get(url, **kwargs):
        if "flight" in str(url):
            return Response(200, json=mock_flight_response) 
        if "convert" in str(url):
            return Response(200, json=mock_exchange_response) 
        raise NotImplementedError()

    async def mock_post(url, **kwargs):
        if "sell" in str(url):
            return Response(200, json=mock_sell_response) 
        if "bonus" in str(url):
            return Response(200, json=mock_bonus_response) 
        raise NotImplementedError()

    mock_instance = mock_async_client.return_value.__aenter__.return_value
    mock_instance.get.side_effect = mock_get
    mock_instance.post.side_effect = mock_post

    request_data = {"flight": "AA100", "day": "2025-01-15", "user": "test_user"}
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/buyTicket", json=request_data)
    
    assert response.status_code == 200
    response_data = response.json()
    
    assert response_data["success"] is True
    assert response_data["transaction_id"] == "mock-tx-12345"
    assert response_data["value_in_dollars"] == 400.0
    assert response_data["value_in_reais"] == 400.0 * 5.5
    assert response_data["bonus_credited"] == 400 

@pytest.mark.asyncio
async def test_buy_ticket_service_fails(mocker):
    mock_flight_response = {"flight": "AA100", "day": "2025-01-15", "value": 400.0}
    
    mock_exchange_response = Response(500, json={"detail": "Exchange service is down"})

    mock_async_client = mocker.patch("httpx.AsyncClient", autospec=True)
    
    async def mock_get(url, **kwargs):
        if "flight" in str(url):
            return Response(200, json=mock_flight_response)
        if "convert" in str(url):
            raise_for_status_mock = mocker.Mock()
            raise_for_status_mock.side_effect = lambda: mock_exchange_response.raise_for_status()
            mock_exchange_response.raise_for_status = raise_for_status_mock
            return mock_exchange_response
        raise NotImplementedError()

    mock_instance = mock_async_client.return_value.__aenter__.return_value
    mock_instance.get.side_effect = mock_get

    request_data = {"flight": "AA100", "day": "2025-01-15", "user": "test_user"}
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/buyTicket", json=request_data)

    assert response.status_code == 502
    assert "Erro ao comunicar com microsserviço" in response.json()["detail"]