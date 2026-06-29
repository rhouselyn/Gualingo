"""少邻国 - Gualingo 后端入口。

职责：创建 FastAPI 应用、挂载 CORS 中间件、注册路由、启动事件、前端静态文件服务。
"""

import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

from llm_api import get_settings
from config import UI_TRANSLATIONS_DIR, FRONTEND_DIR, HOST, PORT
from utils.state import _ui_translation_cache, storage

# ── 创建应用 ──────────────────────────────────────────────
app = FastAPI(title="少邻国 - Gualingo", version="1.6.1")

# ── CORS 中间件 ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 静态资源缓存 ──────────────────────────────────────────
# Vite 构建产物文件名带 hash，内容变化时 hash 会变，因此可以永久缓存；
# index.html 不缓存，确保用户始终拿到最新的入口 HTML。
class CachedStaticFiles(StaticFiles):
    """StaticFiles 子类：为 /assets 下带 hash 的文件设置一年 immutable 缓存。"""

    async def get_response(self, path: str, scope: Scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return response


def _no_cache_headers():
    return {"Cache-Control": "no-cache, no-store, must-revalidate"}

# ── 注册路由 ──────────────────────────────────────────────
from routers import text_processing, learning, phases, vocabulary, history, settings, tts, favorites

app.include_router(text_processing.router)
app.include_router(learning.router)
app.include_router(phases.router)
app.include_router(vocabulary.router)
app.include_router(history.router)
app.include_router(settings.router)
app.include_router(tts.router)
app.include_router(favorites.router)

# ── 启动事件 ──────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    # Load existing translation files into cache
    if UI_TRANSLATIONS_DIR.exists():
        for cache_file in UI_TRANSLATIONS_DIR.glob("*.json"):
            lang_code = cache_file.stem
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    _ui_translation_cache[lang_code] = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass


# ── 前端静态文件服务 ────────────────────────────────────────

# 挂载前端的 assets 目录（带 hash 的文件长期缓存）
_assets_dir = FRONTEND_DIR / "assets"
if _assets_dir.exists():
    app.mount("/assets", CachedStaticFiles(directory=str(_assets_dir)), name="assets")


# 根路径：返回前端 index.html（不缓存，确保拿到最新入口）
@app.get("/")
async def serve_root():
    return FileResponse(str(FRONTEND_DIR / "index.html"), headers=_no_cache_headers())


# SPA fallback：所有非 /api 路由返回 index.html（不缓存）
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    return FileResponse(str(FRONTEND_DIR / "index.html"), headers=_no_cache_headers())


# ── 直接运行 ──────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, timeout_keep_alive=600)
