from fastapi import FastAPI
from database import Base

app = FastAPI()

db = Base.metadata.create_all()




@app.get("/")
async def root():
    return {"message": "Hello World"}

