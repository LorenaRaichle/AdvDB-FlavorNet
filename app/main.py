from fastapi import FastAPI
from app.routes import users

app = FastAPI(title="FlavorNet API")

app.include_router(users.router)

@app.get("/")
def root():
    return {"message": "FlavorNet backend is running!"}