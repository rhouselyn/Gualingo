"""文本处理相关路由：process-text, status, detect-language, translate-text, generate-text"""

import re
import time
import asyncio
import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks

from llm_api import detect_language, get_lang_name
from utils.state import llm_api, storage, processing_status
from utils.exercise_generators import process_text_background, generate_title

router = APIRouter(prefix="/api", tags=["text-processing"])


async def _preprocess_and_run(file_id: str, text: str, source_lang: str, target_lang: str, mode: str, original_text: str):
    """后台任务：先做翻译/生成/语言检测，再执行文本处理。"""
    try:
        # 直接输入模式：原文就是用户输入的文本，立即保存
        if mode == "direct":
            if file_id in processing_status:
                processing_status[file_id]["original_text"] = text

        # 1. 翻译/生成预处理
        if mode == "translate":
            _preserve_tr = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status.get(file_id, {})}
            processing_status[file_id] = {"status": "processing", "progress": 0, "current_sentence": 0, "total_sentences": 0, "preprocess": "translating", **_preserve_tr}
            # 翻译方向：target→source（母语→学习语言），把母语翻译为正在学习的语言
            source_lang_name = get_lang_name(source_lang)
            target_lang_name = get_lang_name(target_lang)
            llm_api.reload()
            messages = [
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the following text from {target_lang_name} to {source_lang_name}. Output ONLY the translated text, nothing else. Do not add any explanations, notes, or commentary. The translation should be natural and fluent. CRITICAL: Output must be plain text only. Do NOT use any markdown formatting (no bold, italic, headers, lists, code blocks, etc.), no emojis, no special symbols. Output pure plain text only."
                },
                {"role": "user", "content": text}
            ]
            response = await llm_api.call_llm(messages, temperature=0.3, max_tokens=4096)
            if "choices" in response and len(response["choices"]) > 0:
                translated = response["choices"][0].get("message", {}).get("content", "").strip()
                if translated:
                    text = translated
            # 翻译完成后立即保存原文
            if file_id in processing_status:
                processing_status[file_id]["original_text"] = text
                processing_status[file_id]["preprocess"] = None
        elif mode == "generate":
            _preserve_gen = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status.get(file_id, {})}
            processing_status[file_id] = {"status": "processing", "progress": 0, "current_sentence": 0, "total_sentences": 0, "preprocess": "generating", **_preserve_gen}
            source_lang_name = get_lang_name(source_lang)
            llm_api.reload()
            messages = [
                {
                    "role": "system",
                    "content": f"You are a text generator. Generate a text in {source_lang_name} based on the user's description. CRITICAL RULES: 1. Generate text content that can include articles, stories, essays, descriptions, dialogues, conversations, or any other natural text form. 2. If the user requests dialogue or conversation content, generate natural exchanges between speakers with clear speaker labels (e.g. A:, B:, or names). 3. Do NOT include any meta-commentary, explanations, or notes about the text itself. 4. The text should be natural, coherent, and suitable for language learning. 5. The text should be at least 3-5 sentences long (or 3-5 exchanges for dialogue). 6. Output ONLY the generated text, nothing else. 7. CRITICAL: Output must be plain text only. Do NOT use any markdown formatting (no bold, italic, headers, lists, code blocks, etc.), no emojis, no special symbols. Output pure plain text only."
                },
                {"role": "user", "content": text}
            ]
            response = await llm_api.call_llm(messages, temperature=0.7, max_tokens=4096)
            if "choices" in response and len(response["choices"]) > 0:
                generated = response["choices"][0].get("message", {}).get("content", "").strip()
                if generated:
                    text = generated
            # 生成完成后立即保存原文
            if file_id in processing_status:
                processing_status[file_id]["original_text"] = text
                processing_status[file_id]["preprocess"] = None

        # 2. 语言检测
        if source_lang == "auto":
            _preserve_lang = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status.get(file_id, {})}
            processing_status[file_id] = {"status": "processing", "progress": 0, "current_sentence": 0, "total_sentences": 0, "preprocess": "detecting", **_preserve_lang}
            try:
                source_lang = await detect_language(text)
            except Exception as e:
                print(f"[WARN] Language detection failed: {e}")
                source_lang = "en"
            # 语言检测完成后同步更新 processing_status 中的 source_lang
            if file_id in processing_status:
                processing_status[file_id]["source_lang"] = source_lang

        # 3. 更新语言设置和历史记录
        storage.save_language_settings(file_id, source_lang, target_lang, original_text=text)
        app_settings = storage.load_user_preferences()
        recent_langs = app_settings.get("recent_languages", [])
        if source_lang in recent_langs:
            recent_langs.remove(source_lang)
        recent_langs.insert(0, source_lang)
        recent_langs = recent_langs[:10]
        app_settings["recent_languages"] = recent_langs
        storage.save_user_preferences(app_settings)

        # 4. 生成标题
        title = await generate_title(text, source_lang)
        # 更新 processing_status 中的标题
        if file_id in processing_status:
            processing_status[file_id]["title"] = title

        # 5. 写入历史记录（提前到处理前，用户能立即看到新条目）
        text_preview = text.strip()[:100]
        storage.add_history_record(file_id, title, source_lang, target_lang, text_preview)
        # 非 auto 模式下，endpoint 已先写入空标题记录，这里更新标题
        storage.rename_history_record(file_id, title)

        # 6. 执行文本处理
        await process_text_background(file_id, text, source_lang, target_lang)
    except Exception as e:
        print(f"[ERROR] 预处理或处理出错: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
        # 提供更友好的错误信息
        if "401" in error_msg or "Unauthorized" in error_msg or "authentication" in error_msg.lower():
            error_msg = "API Key 无效或已过期，请检查设置中的 API Key"
        elif "429" in error_msg or "rate_limit" in error_msg.lower() or "too many requests" in error_msg.lower():
            error_msg = "API 请求频率超限，请稍后重试或降低 LLM 速率"
        elif "402" in error_msg or "payment" in error_msg.lower() or "quota" in error_msg.lower() or "balance" in error_msg.lower():
            error_msg = "API 余额不足，请充值后重试"
        elif "ConnectionError" in error_msg or "ConnectionRefused" in error_msg:
            error_msg = "无法连接到 API 服务，请检查网络或 API 地址"
        processing_status[file_id] = {
            "status": "error",
            "error": error_msg
        }


@router.post("/process-text")
async def process_text(request: dict, background_tasks: BackgroundTasks):
    try:
        text = request.get("text", "")
        source_lang = request.get("source_language", "en")
        target_lang = request.get("target_language", "en")
        mode = request.get("mode", "direct")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        # 检查 API Key 是否已配置
        llm_api.reload()
        if not llm_api.api_key:
            raise HTTPException(status_code=400, detail="API Key 未配置，请先在设置中填写 API Key")

        now = datetime.datetime.now()
        file_id = f"text_{now.strftime('%Y%m%d_%H%M%S_%f')[:-3]}"

        # 立即设置初始状态
        preprocess_label = ""
        if mode == "translate":
            preprocess_label = "translating"
        elif mode == "generate":
            preprocess_label = "generating"
        elif source_lang == "auto":
            preprocess_label = "detecting"

        processing_status[file_id] = {
            "status": "processing",
            "progress": 0,
            "current_sentence": 0,
            "total_sentences": 0,
            "preprocess": preprocess_label if preprocess_label else None
        }

        # 非 auto 模式：在后台任务启动前立即保存语言设置和历史记录，用户能立即看到新条目
        if source_lang != "auto":
            storage.save_language_settings(file_id, source_lang, target_lang, original_text=text)
            text_preview = text.strip()[:100]
            storage.add_history_record(file_id, "", source_lang, target_lang, text_preview)

        # 所有耗时操作（翻译/生成/语言检测/标题生成/文本处理）全部在后台执行
        background_tasks.add_task(_preprocess_and_run, file_id, text, source_lang, target_lang, mode, text)

        return {
            "file_id": file_id,
            "status": "processing",
            "title": ""
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{file_id}")
async def get_status(file_id: str):
    if file_id not in processing_status:
        raise HTTPException(status_code=404, detail="File not found")
    return processing_status[file_id]


@router.post("/detect-language")
async def detect_language_endpoint(request: dict):
    try:
        text = request.get("text", "")
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        lang = await detect_language(text)
        return {"detected_language": lang}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate-text")
async def translate_text(request: dict):
    try:
        text = request.get("text", "")
        source_lang = request.get("source_language", "zh")
        target_lang = request.get("target_language", "en")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        source_lang_name = get_lang_name(source_lang)
        target_lang_name = get_lang_name(target_lang)

        llm_api.reload()
        messages = [
            {
                "role": "system",
                "content": f"You are a professional translator. Translate the following text from {source_lang_name} to {target_lang_name}. Output ONLY the translated text, nothing else. Do not add any explanations, notes, or commentary. The translation should be natural and fluent. CRITICAL: Output must be plain text only. Do NOT use any markdown formatting (no bold, italic, headers, lists, code blocks, etc.), no emojis, no special symbols. Output pure plain text only."
            },
            {
                "role": "user",
                "content": text
            }
        ]
        response = await llm_api.call_llm(messages, temperature=0.3, max_tokens=4096)

        translated_text = ""
        if "choices" in response and len(response["choices"]) > 0:
            translated_text = response["choices"][0].get("message", {}).get("content", "").strip()

        if not translated_text:
            raise HTTPException(status_code=500, detail="Translation failed")

        return {"translated_text": translated_text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-text")
async def generate_text(request: dict):
    try:
        prompt = request.get("prompt", "")
        source_lang = request.get("source_language", "en")
        target_lang = request.get("target_language", "zh")

        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        source_lang_name = get_lang_name(source_lang)

        llm_api.reload()
        messages = [
            {
                "role": "system",
                "content": f"You are a text generator. Generate a text in {source_lang_name} based on the user's description. CRITICAL RULES: 1. Generate text content that can include articles, stories, essays, descriptions, dialogues, conversations, or any other natural text form. 2. If the user requests dialogue or conversation content, generate natural exchanges between speakers with clear speaker labels (e.g. A:, B:, or names). 3. Do NOT include any meta-commentary, explanations, or notes about the text itself. 4. The text should be natural, coherent, and suitable for language learning. 5. The text should be at least 3-5 sentences long (or 3-5 exchanges for dialogue). 6. Output ONLY the generated text, nothing else. 7. CRITICAL: Output must be plain text only. Do NOT use any markdown formatting (no bold, italic, headers, lists, code blocks, etc.), no emojis, no special symbols. Output pure plain text only."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        response = await llm_api.call_llm(messages, temperature=0.7, max_tokens=4096)

        generated_text = ""
        if "choices" in response and len(response["choices"]) > 0:
            generated_text = response["choices"][0].get("message", {}).get("content", "").strip()

        if not generated_text:
            raise HTTPException(status_code=500, detail="Text generation failed")

        return {"generated_text": generated_text}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
