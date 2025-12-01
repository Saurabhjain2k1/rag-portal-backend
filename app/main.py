# # app/main.py
# from dotenv import load_dotenv
# load_dotenv()
# from fastapi import FastAPI, Depends
# from fastapi.middleware.cors import CORSMiddleware

# from app.db import Base, engine
# from app.ai import get_ai_provider
# from app.ai.base import AIProvider
# from app.api.routes_auth import router as auth_router
# from app.api.routes_documents import router as documents_router
# from app.api.routes_chat import router as chat_router
# from app.api.routes_users import router as users_router 

# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]

# app = FastAPI(title="Multi-Tenant RAG Portal")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],          # allows OPTIONS, GET, POST, etc.
#     allow_headers=["*"],
# )


# # Create tables (in real production, use Alembic migrations)
# Base.metadata.create_all(bind=engine)

# app.include_router(auth_router)
# app.include_router(documents_router)
# app.include_router(
#     chat_router,
#     prefix="/chat",
#     tags=["chat"]
# )
# app.include_router(users_router)

# @app.get("/health")
# def health_check():
#     return {"status": "ok"}

# @app.get("/ai-test")
# def ai_test(
#     prompt: str = "Say hello!",
#     ai: AIProvider = Depends(get_ai_provider),
# ):
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": prompt},
#     ]
#     answer = ai.chat(messages)
#     return {"answer": answer}

# app/main.py
# app/main.py
# from dotenv import load_dotenv
# load_dotenv()

# from fastapi import FastAPI, Depends
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# import logging

# from app.db import Base, engine
# # from app.ai import get_ai_provider
# # from app.ai.base import AIProvider
# from app.api.routes_auth import router as auth_router
# from app.api.routes_documents import router as documents_router
# from app.api.routes_chat import router as chat_router
# from app.api.routes_users import router as users_router


# logger = logging.getLogger(__name__)


# # -----------------------
# # 🚀 Lifespan (startup)
# # -----------------------
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Runs before the app starts and after it stops."""
#     try:
#         logger.info("Creating database tables if not existing...")
#         Base.metadata.create_all(bind=engine)
#         logger.info("Database tables ready.")
#     except Exception as e:
#         logger.exception("Error during DB initialization on startup: %s", e)
#         raise

#     yield  # startup complete

#     # (Optional) add shutdown logic here
#     logger.info("Application shutdown complete.")


# # -----------------------
# # FastAPI App
# # -----------------------
# app = FastAPI(
#     title="Multi-Tenant RAG Portal",
#     lifespan=lifespan,
# )

# # CORS
# origins = [
#     "http://localhost:5173",
#     "http://127.0.0.1:5173",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# # Routers
# app.include_router(auth_router)
# app.include_router(documents_router)
# app.include_router(chat_router, prefix="/chat", tags=["chat"])
# app.include_router(users_router)


# # Health check
# @app.get("/health")
# def health_check():
#     return {"status": "ok"}


# @app.get("/ai-test")
# def ai_test(
#     prompt: str = "Say hello!",
#     ai: AIProvider = Depends(get_ai_provider),
# ):
#     messages = [
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": prompt},
#     ]
#     answer = ai.chat(messages)
#     return {"answer": answer}

# app/main.py

# app/main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.db import Base, engine
from app.api.routes_auth import router as auth_router   # 👈 only this router added
from app.api.routes_users import router as users_router
from app.api.routes_chat import router as chat_router
from app.api.routes_documents import router as documents_router

logger = logging.getLogger(__name__)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://rag-portal.onrender.com"
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Creating database tables if not existing...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables ready.")
    except Exception as e:
        logger.exception("Error during DB initialization on startup: %s", e)
        raise

    yield


app = FastAPI(title="Multi-Tenant RAG Portal", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers (only auth for now)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(documents_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}
