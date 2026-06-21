"""设置与UI翻译相关路由：settings, user-preferences, translate_ui"""

import json
import asyncio
import os

import requests
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from llm_api import get_settings as get_llm_settings_raw, save_configs, set_active_index, get_lang_name, call_with_rotation
from ui_translations import UI_TRANSLATION_SCHEMA, TRANSLATION_PROMPT
from config import UI_TRANSLATIONS_DIR
from utils.state import storage, _ui_translation_cache, _ui_translation_tasks

router = APIRouter(prefix="/api", tags=["settings"])


class ConfigItem(BaseModel):
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class SettingsUpdate(BaseModel):
    configs: Optional[List[ConfigItem]] = None
    active_index: Optional[int] = None


class UserPreferencesUpdate(BaseModel):
    source_lang: Optional[str] = None
    target_lang: Optional[str] = None
    ui_lang: Optional[str] = None
    rpm: Optional[int] = None
    retry_interval: Optional[float] = None
    skip_listening: Optional[bool] = None
    recent_languages: Optional[List[str]] = None
    page_size: Optional[int] = None
    only_new_words: Optional[bool] = None
    auto_update: Optional[bool] = None


@router.get("/settings")
async def get_settings():
    try:
        settings = get_llm_settings_raw()
        configs = settings.get("configs", [])
        active_index = settings.get("active_index", 0)
        masked_configs = []
        for cfg in configs:
            masked_key = cfg.get("api_key", "")
            if masked_key and len(masked_key) > 8:
                masked_key = masked_key[:4] + "*" * (len(masked_key) - 8) + masked_key[-4:]
            masked_configs.append({
                "api_key": masked_key,
                "base_url": cfg.get("base_url", ""),
                "model": cfg.get("model", ""),
                "has_key": bool(cfg.get("api_key", ""))
            })
        return {
            "configs": masked_configs,
            "active_index": active_index
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_settings(req: SettingsUpdate):
    try:
        if req.configs is not None:
            new_configs = []
            for cfg in req.configs:
                api_key = cfg.api_key if cfg.api_key and not cfg.api_key.startswith("****") and cfg.api_key.strip() else None
                base_url = cfg.base_url
                model = cfg.model
                new_configs.append({
                    "api_key": api_key or "",
                    "base_url": base_url or "",
                    "model": model or ""
                })
            save_configs(new_configs)
        if req.active_index is not None:
            set_active_index(req.active_index)
        settings = get_llm_settings_raw()
        configs = settings.get("configs", [])
        active_index = settings.get("active_index", 0)
        masked_configs = []
        for cfg in configs:
            masked_key = cfg.get("api_key", "")
            if masked_key and len(masked_key) > 8:
                masked_key = masked_key[:4] + "*" * (len(masked_key) - 8) + masked_key[-4:]
            masked_configs.append({
                "api_key": masked_key,
                "base_url": cfg.get("base_url", ""),
                "model": cfg.get("model", ""),
                "has_key": bool(cfg.get("api_key", ""))
            })
        return {
            "configs": masked_configs,
            "active_index": active_index
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-preferences")
async def get_user_preferences():
    try:
        prefs = storage.load_user_preferences()
        return prefs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-preferences")
async def update_user_preferences(req: UserPreferencesUpdate):
    try:
        current = storage.load_user_preferences()
        if req.source_lang is not None:
            current["source_lang"] = req.source_lang
        if req.target_lang is not None:
            current["target_lang"] = req.target_lang
        if req.ui_lang is not None:
            current["ui_lang"] = req.ui_lang
        if req.rpm is not None:
            current["rpm"] = req.rpm
        if req.retry_interval is not None:
            current["retry_interval"] = req.retry_interval
        if req.skip_listening is not None:
            current["skip_listening"] = req.skip_listening
        if req.recent_languages is not None:
            current["recent_languages"] = req.recent_languages
        if req.page_size is not None:
            current["page_size"] = req.page_size
        if req.only_new_words is not None:
            current["only_new_words"] = req.only_new_words
        if req.auto_update is not None:
            current["auto_update"] = req.auto_update
        storage.save_user_preferences(current)
        return current
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/translate_ui/{lang_code}")
async def translate_ui(lang_code: str):
    # Check in-memory cache first
    if lang_code in _ui_translation_cache:
        return _ui_translation_cache[lang_code]

    # Check file cache (works for zh/en and all other languages)
    UI_TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = UI_TRANSLATIONS_DIR / f"{lang_code}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            _ui_translation_cache[lang_code] = result
            return result
        except (json.JSONDecodeError, IOError):
            pass

    # For zh and en, generate from schema and save to file
    if lang_code in ('zh', 'en'):
        result = {}
        for key, val in UI_TRANSLATION_SCHEMA.items():
            result[key] = val.get(lang_code, val.get('en', ''))
        result["_lang_code"] = lang_code
        _ui_translation_cache[lang_code] = result
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except IOError:
            pass
        return result

    # Check if there's an ongoing task for this language
    if lang_code in _ui_translation_tasks:
        task = _ui_translation_tasks[lang_code]
        if task["status"] == "pending":
            return {"_status": "pending", "_lang_code": lang_code}
        elif task["status"] == "done":
            result = task["result"]
            del _ui_translation_tasks[lang_code]
            _ui_translation_cache[lang_code] = result
            return result
        elif task["status"] == "error":
            del _ui_translation_tasks[lang_code]
            return {"_status": "error", "_lang_code": None, "_error": True}

    # Start background translation task
    _ui_translation_tasks[lang_code] = {"status": "pending"}
    asyncio.create_task(_do_translate_ui(lang_code))
    return {"_status": "pending", "_lang_code": lang_code}


async def _do_translate_ui(lang_code: str):
    """Background task to translate UI strings via LLM."""
    cache_file = UI_TRANSLATIONS_DIR / f"{lang_code}.json"

    lang_name = get_lang_name(lang_code)

    strings_for_prompt = {}
    for key, val in UI_TRANSLATION_SCHEMA.items():
        strings_for_prompt[key] = {
            "description": val["desc"],
            "chinese": val["zh"],
            "english": val["en"]
        }

    prompt = TRANSLATION_PROMPT.format(
        target_lang_name=lang_name,
        target_lang_code=lang_code,
        strings_json=json.dumps(strings_for_prompt, ensure_ascii=False, indent=2)
    )

    messages = [
        {"role": "system", "content": "You are a professional UI translator. Always respond with valid JSON only."},
        {"role": "user", "content": prompt}
    ]

    try:
        result = await call_with_rotation(messages, temperature=0, max_tokens=4096)

        if result and result.get("choices"):
            content = result["choices"][0]["message"]["content"]
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            translated = json.loads(content.strip())
            translated["_lang_code"] = lang_code

            # Save to file
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(translated, f, ensure_ascii=False, indent=2)
            except IOError as e:
                print(f"Failed to save UI translation cache: {e}")

            _ui_translation_tasks[lang_code] = {"status": "done", "result": translated}
            return
    except Exception as e:
        print(f"UI translation error: {e}")

    _ui_translation_tasks[lang_code] = {"status": "error"}


@router.get("/version-check")
async def version_check():
    # Read current version from desktop/package.json
    current_version = "1.6.0"
    package_json_path = os.path.join(os.path.dirname(__file__), "..", "desktop", "package.json")
    try:
        with open(package_json_path, "r", encoding="utf-8") as f:
            pkg = json.load(f)
            current_version = pkg.get("version", "1.6.0")
    except Exception:
        pass

    try:
        resp = requests.get(
            "https://api.github.com/repos/rhouselyn/Gualingo/releases/latest",
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        download_url = ""
        assets = data.get("assets", [])
        if assets:
            download_url = assets[0].get("browser_download_url", "")
        release_notes = data.get("body", "")
        has_update = latest_version != current_version and latest_version != ""
        return {
            "current_version": current_version,
            "latest_version": latest_version,
            "has_update": has_update,
            "download_url": download_url,
            "release_notes": release_notes,
        }
    except Exception:
        return {
            "current_version": current_version,
            "latest_version": None,
            "has_update": False,
            "error": "Failed to check for updates",
        }


@router.post("/auto-update")
async def auto_update():
    return {
        "status": "not_available",
        "message": "Auto-update is only available in the desktop application",
    }
