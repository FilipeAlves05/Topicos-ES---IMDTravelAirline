from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import logging
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="IMDTravel", version="1.0.0")

AIRLINES_HUB_URL = "http://airlines_hub:8001"
EXCHANGE_URL = "http://exchange:8002"
FIDELITY_URL = "http://fidelity:8003"

class BuyTicketRequest(BaseModel):
    flight: str
    day: str
    user: str
    ft: bool = False 

class BuyTicketResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    value_in_dollars: Optional[float] = None
    value_in_reais: Optional[float] = None
    bonus_credited: Optional[int] = None

@app.post("/buyTicket", response_model=BuyTicketResponse)
async def buy_ticket(request: BuyTicketRequest):
    ft_enabled = request.ft
    
    exchange_rate_history = [5.5, 5.4, 5.6, 5.55, 5.45, 5.65, 5.5, 5.4, 5.6, 5.55] 

    flight_cache = {}
    try:
        async with httpx.AsyncClient() as client:
            
            logger.info(f"[Request 1] Consultando voo {request.flight} em {request.day}")
            
            flight_key = f"{request.flight}-{request.day}"
            
            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type(httpx.HTTPError),
                reraise=True
            )
            async def get_flight_data():
                logger.info(f"[Request 1] Tentativa de consulta de voo (Retry)")
                response = await client.get(
                    f"{AIRLINES_HUB_URL}/flight",
                    params={"flight": request.flight, "day": request.day},
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

            try:
                flight_data = await get_flight_data()
                value_in_dollars = flight_data.get("value", 0.0)
                flight_cache[flight_key] = value_in_dollars
                logger.info(f"[Request 1] Voo encontrado: ${value_in_dollars}")
            except httpx.HTTPError as e:
                if ft_enabled and flight_key in flight_cache:
                    value_in_dollars = flight_cache[flight_key]
                    logger.warning(f"[Request 1 - FT] Falha na consulta. Usando valor em cache: ${value_in_dollars}")
                elif ft_enabled:
                    value_in_dollars = 100.00 
                    logger.warning(f"[Request 1 - FT] Falha na consulta e sem cache. Usando valor padrão: ${value_in_dollars}")
                else:
                    raise e
            
            if value_in_dollars is None:
                value_in_dollars = 0.0 
                
            logger.info(f"[Request 1] Valor final do voo: ${value_in_dollars}")
            
            logger.info("[Request 2] Consultando taxa de câmbio")
            
            try:
                exchange_response = await client.get(
                    f"{EXCHANGE_URL}/convert",
                    timeout=10.0
                )
                exchange_response.raise_for_status()
                exchange_data = exchange_response.json()
                exchange_rate = exchange_data.get("exchange_rate", 5.5)
                
                exchange_rate_history.pop(0)
                exchange_rate_history.append(exchange_rate)
                
                logger.info(f"[Request 2] Taxa de câmbio: {exchange_rate}")
            except httpx.HTTPError as e:
                if ft_enabled:
                    avg_rate = sum(exchange_rate_history) / len(exchange_rate_history)
                    exchange_rate = round(avg_rate, 4)
                    logger.warning(f"[Request 2 - FT] Falha na consulta. Usando média histórica: {exchange_rate}")
                else:
                    raise e
            
            logger.info(f"[Request 2] Taxa de câmbio final: {exchange_rate}")
            
            value_in_reais = value_in_dollars * exchange_rate
            bonus_to_credit = round(value_in_dollars)  
            
            logger.info(f"Cálculos: ${value_in_dollars} * {exchange_rate} = R${value_in_reais:.2f}")
            logger.info(f"Bônus a creditar: {bonus_to_credit} pontos")
            
            logger.info(f"[Request 3] Processando venda do voo {request.flight}")
            
            sell_timeout = 2.0 if ft_enabled else 10.0 
            
            try:
                sell_response = await client.post(
                    f"{AIRLINES_HUB_URL}/sell",
                    json={"flight": request.flight, "day": request.day},
                    timeout=sell_timeout
                )
                sell_response.raise_for_status()
                sell_data = sell_response.json()
                transaction_id = sell_data.get("transaction_id")
                logger.info(f"[Request 3] Venda realizada com ID: {transaction_id}")
            except httpx.TimeoutException as e:
                logger.error(f"[Request 3 - FT] Timeout de {sell_timeout}s excedido. Falha na venda.")
                raise HTTPException(
                    status_code=504,
                    detail="504 Erro de latência no serviço de venda (AirlinesHub). Operação cancelada."
                )
            except httpx.HTTPError as e:
                raise e 

            logger.info(f"[Request 4] Creditando {bonus_to_credit} pontos para usuário {request.user}")
            
            bonus_credited = bonus_to_credit
            
            try:
                if ft_enabled:
                    if random.random() < 0.3:
                        raise httpx.HTTPError("Falha simulada no serviço Fidelity.")

                    bonus_response = await client.post(
                        f"{FIDELITY_URL}/bonus",
                        json={"user": request.user, "bonus": bonus_to_credit},
                        timeout=5.0
                    )
                    bonus_response.raise_for_status()
                    logger.info(f"[Request 4 - FT] Bônus creditado com sucesso (Fire and Forget)")
                else:
                    bonus_response = await client.post(
                        f"{FIDELITY_URL}/bonus",
                        json={"user": request.user, "bonus": bonus_to_credit},
                        timeout=10.0
                    )
                    bonus_response.raise_for_status()
                    logger.info(f"[Request 4] Bônus creditado com sucesso")
                    
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if ft_enabled:
                    logger.warning(f"[Request 4 - FT] Falha ao creditar bônus: {str(e)}. A venda não foi impedida.")
                    bonus_credited = 0 
                else:
                    raise e
            
            return BuyTicketResponse(
                success=True,
                message=f"Compra realizada com sucesso! Transação: {transaction_id}",
                transaction_id=transaction_id,
                value_in_dollars=value_in_dollars,
                value_in_reais=round(value_in_reais, 2),
                bonus_credited=bonus_credited
            )
            
    except httpx.HTTPError as e:
        logger.error(f"Erro HTTP ao chamar microsserviço: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"502 Erro ao comunicar com microsserviço: {str(e)}"
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
