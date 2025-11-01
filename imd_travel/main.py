from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IMDTravel", version="1.0.0")

AIRLINES_HUB_URL = "http://localhost:8001"
EXCHANGE_URL = "http://localhost:8002"
FIDELITY_URL = "http://localhost:8003"


class BuyTicketRequest(BaseModel):
    flight: str
    day: str
    user: str


class BuyTicketResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    value_in_dollars: Optional[float] = None
    value_in_reais: Optional[float] = None
    bonus_credited: Optional[int] = None


@app.post("/buyTicket", response_model=BuyTicketResponse)
async def buy_ticket(request: BuyTicketRequest):
    try:
        async with httpx.AsyncClient() as client:
            
            logger.info(f"[Request 1] Consultando voo {request.flight} em {request.day}")
            flight_response = await client.get(
                f"{AIRLINES_HUB_URL}/flight",
                params={"flight": request.flight, "day": request.day},
                timeout=10.0
            )
            flight_response.raise_for_status()
            flight_data = flight_response.json()
            value_in_dollars = flight_data.get("value", 0.0)
            logger.info(f"[Request 1] Voo encontrado: ${value_in_dollars}")
            
            logger.info("[Request 2] Consultando taxa de câmbio")
            exchange_response = await client.get(
                f"{EXCHANGE_URL}/convert",
                timeout=10.0
            )
            exchange_response.raise_for_status()
            exchange_data = exchange_response.json()
            exchange_rate = exchange_data.get("exchange_rate", 5.5)
            logger.info(f"[Request 2] Taxa de câmbio: {exchange_rate}")
            
            value_in_reais = value_in_dollars * exchange_rate
            bonus_to_credit = round(value_in_dollars)  # Valor inteiro mais próximo
            
            logger.info(f"Cálculos: ${value_in_dollars} * {exchange_rate} = R${value_in_reais:.2f}")
            logger.info(f"Bônus a creditar: {bonus_to_credit} pontos")
            
            logger.info(f"[Request 3] Processando venda do voo {request.flight}")
            sell_response = await client.post(
                f"{AIRLINES_HUB_URL}/sell",
                json={"flight": request.flight, "day": request.day},
                timeout=10.0
            )
            sell_response.raise_for_status()
            sell_data = sell_response.json()
            transaction_id = sell_data.get("transaction_id")
            logger.info(f"[Request 3] Venda realizada com ID: {transaction_id}")
            
            logger.info(f"[Request 4] Creditando {bonus_to_credit} pontos para usuário {request.user}")
            bonus_response = await client.post(
                f"{FIDELITY_URL}/bonus",
                json={"user": request.user, "bonus": bonus_to_credit},
                timeout=10.0
            )
            bonus_response.raise_for_status()
            bonus_data = bonus_response.json()
            logger.info(f"[Request 4] Bônus creditado com sucesso")
            
            return BuyTicketResponse(
                success=True,
                message=f"Compra realizada com sucesso! Transação: {transaction_id}",
                transaction_id=transaction_id,
                value_in_dollars=value_in_dollars,
                value_in_reais=round(value_in_reais, 2),
                bonus_credited=bonus_to_credit
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Erro HTTP ao chamar microsserviço: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao comunicar com microsserviço: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Erro inesperado: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao processar compra: {str(e)}"
        )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "IMDTravel"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
