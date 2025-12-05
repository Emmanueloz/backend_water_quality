import os
from fastapi import FastAPI
from app.share.firebase import FirebaseInitializer
from fastapi.middleware.cors import CORSMiddleware
from app.share.firebase.domain.config import FirebaseConfigImpl

from app.features.auth import auth_router
from app.features.workspaces import workspaces_router
from app.features.meters import meters_router
from app.features.alerts import alerts_router
from app.features.users import users_router
from app.features.analysis import analysis_router
from app.share.socketio import socket_app

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.mount("/socket.io/", socket_app, name="socketio")


if not os.getenv("SKIP_FIREBASE_INIT", "false").lower() == "true":
    FirebaseInitializer.initialize(FirebaseConfigImpl())

app.include_router(auth_router)
app.include_router(workspaces_router)
app.include_router(meters_router)
app.include_router(alerts_router)
app.include_router(users_router)
app.include_router(analysis_router)


@app.get("/")
def get_index():
    return {"message": "API"}
