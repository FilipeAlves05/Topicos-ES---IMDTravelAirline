import pytest
from httpx import AsyncClient
from .main import app, USERS_DATABASE

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "Fidelity"}

@pytest.mark.asyncio
async def test_get_user_bonus_new_user():
    # Testa um usuário que ainda não existe
    user_id = "new_user_123"
    USERS_DATABASE.clear() # Limpa o DB simulado
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/user/{user_id}")
    
    assert response.status_code == 200
    assert response.json() == {"user": user_id, "bonus_balance": 0.0}

@pytest.mark.asyncio
async def test_add_bonus():
    user_id = "test_user_456"
    bonus_to_add = 100
    USERS_DATABASE.clear() # Limpa o DB simulado
    
    request_data = {"user": user_id, "bonus": bonus_to_add}
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/bonus", json=request_data)
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "success"
    assert response_data["message"] == f"Bônus de {bonus_to_add} creditado para o usuário {user_id}. Saldo total: {float(bonus_to_add)}"
    
    # Verifica se foi salvo no "banco"
    assert USERS_DATABASE.get(user_id) == float(bonus_to_add)

@pytest.mark.asyncio
async def test_add_bonus_multiple_times():
    user_id = "test_user_789"
    USERS_DATABASE.clear() # Limpa o DB simulado
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Primeira adição
        await ac.post("/bonus", json={"user": user_id, "bonus": 50})
        # Segunda adição
        response = await ac.post("/bonus", json={"user": user_id, "bonus": 75})

    assert response.status_code == 200
    assert USERS_DATABASE.get(user_id) == 125.0
    assert "Saldo total: 125.0" in response.json()["message"]