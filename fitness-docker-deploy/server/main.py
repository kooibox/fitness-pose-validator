# -*- coding: utf-8 -*-
"""FastAPI 服务入口 - 替代原有的 http.server 实现"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth_router, sessions_router, dashboard_router, llm_router

app = FastAPI(
    title="Fitness Pose Server",
    description="健身姿态检测服务器 - FastAPI 版本",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(llm_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    init_db()
    print("=" * 60)
    print("Fitness Pose Server v2.0 (FastAPI)")
    print("=" * 60)
    print("API 文档: http://localhost:8080/docs")
    print("=" * 60)


@app.get("/")
async def root():
    return {
        "name": "Fitness Pose Server",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)