from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import uuid
import json
from datetime import datetime

app = FastAPI(title="AirlinesHub", version="1.0.0")

FLIGHTS_DATABASE = {
    "AA100": {
        "2025-01-15": {"flight": "AA100", "day": "2025-01-15", "value": 450.00},
        "2025-01-20": {"flight": "AA100", "day": "2025-01-20", "value": 480.00},
    },
    "UA200": {
        "2025-01-15": {"flight": "UA200", "day": "2025-01-15", "value": 520.00},
        "2025-01-22": {"flight": "UA200", "day": "2025-01-22", "value": 550.00},
    },
    "DL300": {
        "2025-02-10": {"flight": "DL300", "day": "2025-02-10", "value": 380.00},
        "2025-02-15": {"flight": "DL300", "day": "2025-02-15", "value": 400.00},
    },
}

TRANSACTIONS = {}


class FlightResponse(BaseModel):
    flight: str
    day: str
    value: float


class SellRequest(BaseModel):
    flight: str
    day: str


class SellResponse(BaseModel):
    transaction_id: str


@app.get("/flight", response_model=FlightResponse)
async def get_flight(flight: str, day: str):
    if flight in FLIGHTS_DATABASE and day in FLIGHTS_DATABASE[flight]:
        return FLIGHTS_DATABASE[flight][day]
    else:
        return FlightResponse(
            flight=flight,
            day=day,
            value=500.00 
        )


@app.post("/sell", response_model=SellResponse)
async def sell_flight(request: SellRequest):
    transaction_id = str(uuid.uuid4())

    TRANSACTIONS[transaction_id] = {
        "flight": request.flight,
        "day": request.day,
        "timestamp": datetime.now().isoformat()
    }
    
    return SellResponse(transaction_id=transaction_id)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AirlinesHub"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
