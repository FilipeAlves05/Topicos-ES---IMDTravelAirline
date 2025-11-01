from fastapi import FastAPI
import random

app = FastAPI(title="Exchange", version="1.0.0")


@app.get("/convert")
async def convert_currency():
    exchange_rate = round(random.uniform(5.0, 6.0), 2)
    return {"exchange_rate": exchange_rate}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Exchange"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
