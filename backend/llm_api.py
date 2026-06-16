import os
import json
import requests
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from config import LLM_SETTINGS_FILE


def _repair_truncated_json(json_str):
    if not json_str or not isinstance(json_str, str):
        return []
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        pass

    try:
        if json_str.strip().startswith('['):
            depth = 0
            last_valid_end = -1
            for i, c in enumerate(json_str):
                if c == '[':
                    depth += 1
                elif c == ']':
                    depth -= 1
                    if depth == 0:
                        last_valid_end = i
                        break

            if last_valid_end > 0:
                repaired = json_str[:last_valid_end + 1]
                return json.loads(repaired)

            brace_depth = 0
            for i in range(len(json_str) - 1, -1, -1):
                if json_str[i] == '}':
                    brace_depth += 1
                elif json_str[i] == '{':
                    brace_depth -= 1
                    if brace_depth == 0:
                        repaired = json_str[:i + 1] + ']'
                        return json.loads(repaired)
    except (json.JSONDecodeError, TypeError):
        pass

    return []


_DEFAULT_CONFIGS = [
    {"api_key": "", "base_url": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen3.6-27B"},
    {"api_key": "", "base_url": "https://api.siliconflow.cn/v1", "model": "Qwen/Qwen3.5-27B"},
    {"api_key": "", "base_url": "https://api.siliconflow.cn/v1", "model": "deepseek-ai/DeepSeek-V3.2"},
]

def _load_settings():
    if LLM_SETTINGS_FILE.exists():
        try:
            with open(LLM_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "configs" in data and isinstance(data["configs"], list):
                return {
                    "configs": data["configs"],
                    "active_index": data.get("active_index", 0)
                }
            if "api_key" in data or "base_url" in data or "model" in data:
                migrated_config = {
                    "api_key": data.get("api_key", ""),
                    "base_url": data.get("base_url", _DEFAULT_CONFIGS[0]["base_url"]),
                    "model": data.get("model", _DEFAULT_CONFIGS[0]["model"])
                }
                settings = {
                    "configs": [migrated_config],
                    "active_index": 0
                }
                _save_settings(settings)
                return settings
        except (json.JSONDecodeError, IOError):
            pass
    return {"configs": [dict(c) for c in _DEFAULT_CONFIGS], "active_index": 0}

def _save_settings(settings: dict):
    LLM_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LLM_SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def get_settings():
    return _load_settings()

def update_settings(api_key: str = None, base_url: str = None, model: str = None, config_index: int = 0):
    settings = _load_settings()
    configs = settings.get("configs", [])
    if not configs:
        configs = [dict(c) for c in _DEFAULT_CONFIGS]
        settings["configs"] = configs
    idx = config_index
    if idx < 0 or idx >= len(configs):
        idx = 0
    if api_key is not None:
        configs[idx]["api_key"] = api_key
    if base_url is not None:
        configs[idx]["base_url"] = base_url
    if model is not None:
        configs[idx]["model"] = model
    _save_settings(settings)
    return _load_settings()

def get_configs():
    settings = _load_settings()
    return settings.get("configs", [])

def add_config(config: dict):
    settings = _load_settings()
    configs = settings.get("configs", [])
    new_config = {
        "api_key": config.get("api_key", ""),
        "base_url": config.get("base_url", _DEFAULT_CONFIGS[0]["base_url"]),
        "model": config.get("model", _DEFAULT_CONFIGS[0]["model"])
    }
    configs.append(new_config)
    settings["configs"] = configs
    _save_settings(settings)
    return settings

def remove_config(index: int):
    settings = _load_settings()
    configs = settings.get("configs", [])
    if 0 <= index < len(configs):
        configs.pop(index)
        active_index = settings.get("active_index", 0)
        if active_index >= len(configs):
            active_index = max(0, len(configs) - 1)
        settings["configs"] = configs
        settings["active_index"] = active_index
        _save_settings(settings)
    return settings

def update_config(index: int, config: dict):
    settings = _load_settings()
    configs = settings.get("configs", [])
    if 0 <= index < len(configs):
        if "api_key" in config:
            configs[index]["api_key"] = config["api_key"]
        if "base_url" in config:
            configs[index]["base_url"] = config["base_url"]
        if "model" in config:
            configs[index]["model"] = config["model"]
        settings["configs"] = configs
        _save_settings(settings)
    return settings

def save_configs(new_configs: list):
    settings = _load_settings()
    old_configs = settings.get("configs", [])
    for i, cfg in enumerate(new_configs):
        api_key = cfg.get("api_key", "")
        if not api_key and i < len(old_configs):
            api_key = old_configs[i].get("api_key", "")
        if i < len(old_configs):
            old_configs[i]["api_key"] = api_key
            old_configs[i]["base_url"] = cfg.get("base_url", old_configs[i].get("base_url", ""))
            old_configs[i]["model"] = cfg.get("model", old_configs[i].get("model", ""))
        else:
            old_configs.append({
                "api_key": api_key,
                "base_url": cfg.get("base_url", _DEFAULT_CONFIGS[0]["base_url"]),
                "model": cfg.get("model", _DEFAULT_CONFIGS[0]["model"])
            })
    settings["configs"] = old_configs[:len(new_configs)]
    _save_settings(settings)
    return _load_settings()

def set_active_index(index: int):
    settings = _load_settings()
    configs = settings.get("configs", [])
    if 0 <= index < len(configs):
        settings["active_index"] = index
        _save_settings(settings)
    return settings


SUPPORTED_LANGUAGES = [
    "en", "fr", "pt", "de", "ro", "sv", "da", "bg", "ru", "cs", "el", "uk",
    "es", "nl", "sk", "hr", "pl", "lt", "nb", "nn", "fa", "sl", "gu", "lv",
    "it", "oc", "ne", "mr", "be", "sr", "lb", "vec", "as", "cy", "szl",
    "ast", "hne", "awa", "mai", "bho", "sd", "ga", "fo", "hi", "pa", "bn",
    "or", "tg", "yi", "lmo", "lij", "scn", "fur", "sc", "gl", "ca", "is",
    "sq", "li", "prs", "af", "mk", "si", "ur", "mag", "bs", "hy",
    "zh", "zh-TW", "yue", "my",
    "ar", "ars", "apc", "arz", "ary", "acm", "acq", "aeb",
    "he", "mt",
    "id", "ms", "tl", "ceb", "jv", "su", "min", "ban", "bjn", "pag", "ilo", "war",
    "ta", "te", "kn", "ml",
    "tr", "az", "uz", "kk", "ba", "tt",
    "th", "lo",
    "fi", "et", "hu",
    "vi", "km",
    "ja", "ko", "ka", "eu", "ht", "pap", "kea", "tpi", "sw",
]

LANG_NAMES = {
    "en": "English", "fr": "French", "pt": "Portuguese", "de": "German",
    "ro": "Romanian", "sv": "Swedish", "da": "Danish", "bg": "Bulgarian",
    "ru": "Russian", "cs": "Czech", "el": "Greek", "uk": "Ukrainian",
    "es": "Spanish", "nl": "Dutch", "sk": "Slovak", "hr": "Croatian",
    "pl": "Polish", "lt": "Lithuanian", "nb": "Norwegian Bokmål", "nn": "Norwegian Nynorsk",
    "fa": "Persian", "sl": "Slovenian", "gu": "Gujarati", "lv": "Latvian",
    "it": "Italian", "oc": "Occitan", "ne": "Nepali", "mr": "Marathi",
    "be": "Belarusian", "sr": "Serbian", "lb": "Luxembourgish", "vec": "Venetian",
    "as": "Assamese", "cy": "Welsh", "szl": "Silesian", "ast": "Asturian",
    "hne": "Chhattisgarhi", "awa": "Awadhi", "mai": "Maithili", "bho": "Bhojpuri",
    "sd": "Sindhi", "ga": "Irish", "fo": "Faroese", "hi": "Hindi",
    "pa": "Punjabi", "bn": "Bengali", "or": "Odia", "tg": "Tajik",
    "yi": "Yiddish", "lmo": "Lombard", "lij": "Ligurian", "scn": "Sicilian",
    "fur": "Friulian", "sc": "Sardinian", "gl": "Galician", "ca": "Catalan",
    "is": "Icelandic", "sq": "Albanian", "li": "Limburgish", "prs": "Dari",
    "af": "Afrikaans", "mk": "Macedonian", "si": "Sinhala", "ur": "Urdu",
    "mag": "Magahi", "bs": "Bosnian", "hy": "Armenian",
    "zh": "Chinese (Simplified)", "zh-TW": "Chinese (Traditional)", "yue": "Cantonese", "my": "Burmese",
    "ar": "Arabic (Standard)", "ars": "Arabic (Najdi)", "apc": "Arabic (Levantine)",
    "arz": "Arabic (Egyptian)", "ary": "Arabic (Moroccan)", "acm": "Arabic (Mesopotamian)",
    "acq": "Arabic (Ta'izzi-Adeni)", "aeb": "Arabic (Tunisian)",
    "he": "Hebrew", "mt": "Maltese",
    "id": "Indonesian", "ms": "Malay", "tl": "Tagalog", "ceb": "Cebuano",
    "jv": "Javanese", "su": "Sundanese", "min": "Minangkabau", "ban": "Balinese",
    "bjn": "Banjar", "pag": "Pangasinan", "ilo": "Ilokano", "war": "Waray",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "ml": "Malayalam",
    "tr": "Turkish", "az": "Azerbaijani", "uz": "Uzbek", "kk": "Kazakh",
    "ba": "Bashkir", "tt": "Tatar",
    "th": "Thai", "lo": "Lao",
    "fi": "Finnish", "et": "Estonian", "hu": "Hungarian",
    "vi": "Vietnamese", "km": "Khmer",
    "ja": "Japanese", "ko": "Korean", "ka": "Georgian", "eu": "Basque",
    "ht": "Haitian Creole", "pap": "Papiamento", "kea": "Kabuverdianu",
    "tpi": "Tok Pisin", "sw": "Swahili",
}

def get_lang_name(code):
    return LANG_NAMES.get(code, code)


async def call_with_rotation(messages: List[Dict], tools: List[Dict] = None, temperature: float = 0.0, max_tokens: int = 4096):
    import time as _time
    settings = _load_settings()
    configs = settings.get("configs", [])
    active_index = settings.get("active_index", 0)
    if not configs:
        configs = [dict(c) for c in _DEFAULT_CONFIGS]
        active_index = 0
    num_configs = len(configs)

    try:
        from utils.state import storage
        prefs = storage.load_user_preferences()
        interval = prefs.get("retry_interval", 1.0)
    except Exception:
        interval = 1.0

    fail_start = None
    last_exception = None
    attempt = 0
    while True:
        # 持续失败超过10分钟则放弃
        if fail_start is not None:
            fail_duration = _time.time() - fail_start
            if fail_duration >= 600:
                if last_exception:
                    raise last_exception
                raise Exception("API calls failed continuously for 10 minutes")

        idx = (active_index + attempt) % num_configs
        config = configs[idx]
        # 提交请求的同时开始计算间隔
        api = LLMAPI(config_index=idx)
        request_task = asyncio.create_task(api.call_llm(messages, tools=tools, temperature=temperature, max_tokens=max_tokens))
        timer_task = asyncio.ensure_future(asyncio.sleep(interval))
        # 等待请求和间隔两者都完成
        done, pending = await asyncio.wait(
            [request_task, timer_task],
            return_when=asyncio.ALL_COMPLETED
        )
        # 检查请求结果
        try:
            result = request_task.result()
            # 成功：重置失败计时器，保存当前 key 为活跃 key
            fail_start = None
            last_exception = None
            attempt = 0
            if idx != active_index:
                print(f"[ROTATE] Switched from config {active_index} to config {idx} (model={config.get('model', '')})")
                settings["active_index"] = idx
                _save_settings(settings)
            return result
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            # 记录失败开始时间
            if fail_start is None:
                fail_start = _time.time()
            last_exception = e

            status_code = None
            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                status_code = e.response.status_code

            # 401/403 认证错误不需要重试，直接抛出
            if status_code in (401, 403):
                print(f"[ROTATE] Config {idx} auth failed ({status_code}), aborting immediately")
                raise Exception(f"API Key 无效或已过期 (HTTP {status_code})，请检查设置中的 API Key")

            # 402 余额不足不需要重试
            if status_code == 402:
                print(f"[ROTATE] Config {idx} payment required (402), aborting immediately")
                raise Exception("API 余额不足，请充值后重试")

            if status_code in (429, 502, 503):
                print(f"[ROTATE] Config {idx} rate-limited ({status_code}), interval already elapsed, switching to config {(idx + 1) % num_configs}")
            else:
                print(f"[ROTATE] Config {idx} failed: {e}, interval already elapsed, switching to config {(idx + 1) % num_configs}")

            # 间隔已经和请求并行等待过了，直接切换到下一个 key
            attempt += 1
            continue


async def detect_language(text: str) -> str:
    lang_list_str = ", ".join(SUPPORTED_LANGUAGES)
    messages = [
        {
            "role": "system",
            "content": f"You are a language detection expert. Identify the language of the given text. You must respond with ONLY the language code from this exact list: [{lang_list_str}]. Do not output anything else. Pick the single most matching code."
        },
        {
            "role": "user",
            "content": text[:500]
        }
    ]
    result = await call_with_rotation(messages, temperature=0.0, max_tokens=32)
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip().strip('"').strip("'")
    if content in SUPPORTED_LANGUAGES:
        return content
    for lang in SUPPORTED_LANGUAGES:
        if lang.lower() == content.lower():
            return lang
    return "en"


class LLMAPI:
    def __init__(self, config_index: int = None):
        self._config_index = config_index
        self._reload()

    def _reload(self):
        settings = _load_settings()
        configs = settings.get("configs", [])
        if self._config_index is not None:
            idx = self._config_index
        else:
            idx = settings.get("active_index", 0)
        if not configs or idx < 0 or idx >= len(configs):
            config = dict(_DEFAULT_CONFIGS[0])
        else:
            config = configs[idx]
        self.api_key = config.get("api_key", "")
        self.base_url = config.get("base_url", "https://api.siliconflow.cn/v1")
        self.model = config.get("model", "Qwen/Qwen3.6-27B")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def reload(self):
        self._reload()

    def _sync_post(self, url, headers, payload, timeout):
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            reasoning_content = message.get("reasoning_content", "")
            if not content and reasoning_content:
                message["content"] = reasoning_content
                result["choices"][0]["message"] = message
        return result

    async def call_llm(self, messages: List[Dict], tools: List[Dict] = None, temperature: float = 0.0, max_tokens: int = 4096):
        import time as _time
        self.reload()
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "thinking": {"type": "disabled"}
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            t0 = _time.time()
            result = await asyncio.to_thread(
                self._sync_post,
                f"{self.base_url}/chat/completions",
                self.headers,
                payload,
                600
            )
            t1 = _time.time()
            has_tools = "yes" if tools else "no"
            print(f"[TIMING] call_llm (tools={has_tools}): {t1 - t0:.3f}s")
            return result
        except requests.exceptions.Timeout:
            print("API request timed out. Retrying...")
            t0 = _time.time()
            result = await asyncio.to_thread(
                self._sync_post,
                f"{self.base_url}/chat/completions",
                self.headers,
                payload,
                600
            )
            t1 = _time.time()
            has_tools = "yes" if tools else "no"
            print(f"[TIMING] call_llm retry (tools={has_tools}): {t1 - t0:.3f}s")
            return result

    @classmethod
    async def call_with_rotation(cls, messages: List[Dict], tools: List[Dict] = None, temperature: float = 0.0, max_tokens: int = 4096):
        return await call_with_rotation(messages, tools=tools, temperature=temperature, max_tokens=max_tokens)

    async def generate_multiple_choice(self, word: str, correct_meaning: str, context: str, target_lang: str, source_lang: str = "en", temperature: float = 0.7):
        tool_def = {
            "type": "function",
            "function": {
                "name": "generate_multiple_choice",
                "description": "Generate enriched word information with multiple choice options",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "word": {"type": "string"},
                        "enriched_meaning": {
                            "type": "string",
                            "description": "单词的完整释义，包含多个母语单词的常见含义"
                        },
                        "variants_detail": {
                            "type": "array",
                            "description": "词形变化 + 类型说明，只包含确实存在的词形变化",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "form": {"type": "string"},
                                    "type": {"type": "string"}
                                }
                            }
                        },
                        "examples": {
                            "type": "array",
                            "description": "两个全新的例句（绝不能复用原文句子，必须是不同的句子。尽量使用简单常见的词汇组成例句，不需要与原文中的意思相同）",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "sentence": {"type": "string"},
                                    "translation": {"type": "string"}
                                }
                            },
                            "minItems": 2,
                            "maxItems": 2
                        },
                        "memory_hint": {
                            "type": "string",
                            "description": "记忆辅助（联想/对比母语）"
                        },
                        "multiple_choice": {
                            "type": "object",
                            "properties": {
                                "options": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "text": {"type": "string", "description": "A concrete, meaningful translation or definition. MUST NOT be a placeholder like 'meaning 1', '释义1', '含义1', etc."}
                                        }
                                    },
                                    "minItems": 4,
                                    "maxItems": 4
                                }
                            }
                        }
                    },
                    "required": ["word", "enriched_meaning", "examples", "multiple_choice"]
                }
            }
        }

        target_lang_name = get_lang_name(target_lang)
        source_lang_name = get_lang_name(source_lang)
        prompt = f"""
为 {source_lang_name} 单词 '{word}' 生成丰富的信息，使用 {target_lang_name} 输出。

【极其重要】这个单词属于 {source_lang_name}（学习语言）：
- 词形变化（variants_detail）必须是 {source_lang_name} 语法规则下的词形变化
- 例句（examples）必须使用 {source_lang_name} 编写
- 所有语言相关的内容都必须遵循 {source_lang_name} 的语法和用法规范

上下文释义：{correct_meaning}

上下文：{context}

请生成以下信息：

1. enriched_meaning: 单词的完整释义，包含多个常见含义，用分号分隔。每个含义必须是具体的、有意义的翻译，不能是占位符（如"释义1"、"含义1"等）
2. variants_detail: {source_lang_name} 词形变化列表，带类型说明。对于派生词，必须列出其词根/原形作为词形变化。对于基础词，列出其常见的屈折变化（如名词的复数、动词的变位形式、形容词的比较级/最高级等，必须遵循 {source_lang_name} 语法规则）。只包含确实存在的词形变化，如果没有则返回空数组
3. examples: 两个全新的例句。【极其重要】例句本身必须使用 {source_lang_name}（学习语言）编写，翻译必须使用 {target_lang_name}（用户的母语）。绝不能反过来用母语写例句再用学习语言翻译。尽量使用简单常见的词汇组成例句，不需要与原文中的意思相同
4. memory_hint: 记忆辅助（与用户母语的联想或对比）
5. multiple_choice: 选择题，包含：
   - options: 4个选项，【极其重要】第一个选项必须是正确答案，其余3个是错误答案

要求：
- 所有输出必须使用 {target_lang_name}
- 【极其重要】例句必须使用 {source_lang_name} 编写，翻译使用 {target_lang_name}。绝不能用母语写例句再用学习语言翻译
- 例句要自然，尽量使用简单常见的词汇，不需要与原文中的意思相同
- 记忆辅助对语言学习者要有帮助
- 选择题选项要清晰且合理
- 【重要】正确答案必须是单词的常见、正常释义，不是上下文特定释义
- 【重要】错误答案必须是该单词所没有的意思，而不是非句子中的意思
- 【重要】选项必须是纯单词或短语，不能是完整句子
- 【重要】选项必须与单词本身的意思无关，不能包含单词的任何含义
- 【重要】词形变化必须是 {source_lang_name} 中确实存在的，不要硬加不存在的词形
- 【重要】四个选项的格式和词性必须保持一致：如果正确答案包含两个释义，错误选项也必须各包含两个释义；如果正确答案只有一个释义，错误选项也各只有一个释义。所有选项的词性范围应尽量一致
- 【极其重要】enriched_meaning 中不能包含占位符文本（如"释义1"、"含义1"、"meaning 1"等），必须全部是具体的、有意义的翻译内容
- 【输出约束】除了工具调用的JSON输出外，不要添加任何其他文本、解释或说明。直接生成工具调用所需的JSON参数即可。
"""

        messages = [{"role": "user", "content": prompt}]

        response = await call_with_rotation(messages, [tool_def], temperature=temperature, max_tokens=16384)

        try:
            for choice in response["choices"]:
                if "tool_calls" in choice["message"]:
                    tool_call = choice["message"]["tool_calls"][0]
                    args = json.loads(tool_call["function"]["arguments"])
                    return args
            default_response = {
                "word": word,
                "enriched_meaning": correct_meaning,
                "variants_detail": [],
                "examples": [
                    {"sentence": f"This is a sentence with {word}.", "translation": f"Example translation for {word} in {target_lang_name}."},
                    {"sentence": f"I can use {word} in a sentence.", "translation": f"Example translation for {word} in {target_lang_name}."}
                ],
                "memory_hint": "",
                "multiple_choice": {
                    "options": [
                        {"text": correct_meaning},
                        {"text": f"Option 1 in {target_lang_name}"},
                        {"text": f"Option 2 in {target_lang_name}"},
                        {"text": f"Option 3 in {target_lang_name}"}
                    ]
                }
            }
            return default_response
        except Exception as e:
            print(f"Tool call failed: {e}")
            print(f"Response: {response}")
            error_response = {
                "word": word,
                "enriched_meaning": correct_meaning,
                "variants_detail": [],
                "examples": [
                    {"sentence": f"This is a sentence with {word}.", "translation": f"Example translation for {word} in {target_lang_name}."},
                    {"sentence": f"I can use {word} in a sentence.", "translation": f"Example translation for {word} in {target_lang_name}."}
                ],
                "memory_hint": "",
                "multiple_choice": {
                    "options": [
                        {"text": correct_meaning},
                        {"text": f"Option 1 in {target_lang_name}"},
                        {"text": f"Option 2 in {target_lang_name}"},
                        {"text": f"Option 3 in {target_lang_name}"}
                    ]
                }
            }
            return error_response

    async def process_text_with_dictionary(self, text: str, source_lang: str, target_lang: str, context_sentences: dict = None):
        tool_def = {
            "type": "function",
            "function": {
                "name": "process_text_with_dictionary",
                "description": "同时处理文本拆解翻译和单词词典条目生成",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "original": {
                            "type": "string",
                            "description": "原文文本（完全保留原始空格）"
                        },
                        "translation": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "description": "A single word or fixed multi-word expression from the source text. MUST NOT contain any punctuation marks (periods, commas, question marks, exclamation marks, colons, semicolons, or any language-specific punctuation). Punctuation does NOT belong to any token — it is completely discarded. Hyphens(-) and apostrophes(') must be preserved if they are internal parts of a word in that language. TOKENIZATION PRINCIPLE: Follow the natural word boundaries of the source language. A 'token' is the smallest meaningful unit that can appear independently in a dictionary of that language, OR a fixed multi-word expression whose meaning cannot be derived from its individual parts. Key rules: (1) Characters like hyphens and apostrophes are often internal parts of words (not separators) — respect the orthographic conventions of each language. (2) Inflected/conjugated forms are one token, never split into stem+affix. (3) 【CRITICAL·Fixed Collocations & Multi-Word Expressions】When two or more consecutive words form a fixed collocation, set phrase, phrasal verb, idiom, or any expression where the whole meaning ≠ sum of parts, they MUST be treated as ONE single token (one text field containing the entire multi-word expression). This applies to ALL languages. Examples of patterns that must be one token: discourse markers, greetings, phrasal verbs, compound prepositions, fixed conjunctions, and any expression that functions as a single semantic unit. If you would list it as one entry in a phrase dictionary, it should be one token. 【CRITICAL·Over-merging Warning】Do NOT over-merge! Only merge when the overall meaning truly cannot be deduced from the literal meanings of the individual parts. If each word has its own independent dictionary definition and they are merely in a grammatical combination (subject-verb, verb-object, preposition-noun, etc.), they MUST remain separate tokens. Grammatical constructions (even fixed sentence patterns) are NOT the same as fixed collocations. (4) After removing punctuation from all 'text' values, their concatenation in order MUST equal the original source text with punctuation removed — no characters may be omitted or added. Each character belongs to exactly ONE token; no overlap, no duplication. NEVER split a word into characters, syllables, morphemes, or stem+affix. NEVER add tokens that do not correspond to actual words in the source text."},
                                    "phonetic": {"type": "string", "description": "Pronunciation of this word. Use the most commonly used and widely recognized pronunciation notation for the source language — this may be IPA, pinyin, romaji, or any other standard system that native speakers and learners would expect. For tonal languages, include tone information."},
                                    "morphology": {"type": "string"},
                                    "meaning": {"type": "string", "description": "Meaning in TARGET_LANG based on the context - concise, just a few independent words, not a full sentence explanation"}
                                },
                                "required": ["text", "phonetic", "morphology", "meaning"]
                            }
                        },
                        "tokenized_translation": {
                            "type": "string",
                            "description": "完整自然的 TARGET_LANG 翻译，正常句子格式"
                        },
                        "translation_phrases": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "将 tokenized_translation 按目标语言的词（token）进行分词后的结果，用于翻译排序练习。必须至少拆分为2个片段！【核心原则·这是对目标语言翻译的分词，不是对源语言的分词】每个片段应该是目标语言翻译中的一个词或固定搭配。【拆分原则·严格遵循目标语言的自然词边界】1.遵循目标语言的自然词边界：用空格分隔词语的语言按空格分词；不用空格的语言（如中文、日语等）按语言学上的词边界分词，每个片段应该是一个可以在该语言词典中查到的最小意义单位或固定多词表达；2.【极其重要·禁止按标点拆分】绝对不能按标点符号（逗号、句号等）来拆分片段！标点符号必须被丢弃，不属于任何片段。拆分的依据是目标语言的词边界，而不是标点符号的位置；3.变位/屈折形式是单个片段：不要将变位形式拆分为词干+词缀；4.【极其重要·固定搭配与多词表达】当两个或多个连续的词构成固定搭配、短语动词、习语、惯用语等非组合性表达时，必须作为一个片段，不能拆分。这是所有语言的通用原则。判断标准：如果拆分后各部分无法独立表达整体含义，则必须保持为一个片段；5.【极其重要·标点禁令】每个片段绝对禁止包含任何标点符号（句号、逗号、问号、感叹号、分号、冒号、省略号等），标点不属于任何片段。但连字符(-)和撇号(')如果在该语言中是词的内部组成部分则必须保留；6.所有片段去除标点后按顺序拼接必须等于 tokenized_translation 去除标点后的内容，不能遗漏或增加文字内容；7.【极其重要·禁止增减原则】所有片段必须与 tokenized_translation 中的词语一一对应，绝对不能随意增加不存在的片段，也不能将一个词拆分成多个片段；8.虚词（的、了、地等）可以与相邻词合并；9.每个片段不能是单个无意义虚词"
                        },
                        "grammar_explanation": {
                            "type": "string",
                            "description": "整个文本的一个完整语法解释，用 TARGET_LANG"
                        },
                        "redundant_tokens": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "4个与原文相关的合理冗余tokens，用于测验目的，必须全部使用TARGET_LANG。【极其重要】每个冗余token必须是单个独立的词，不能是多个词组成的短语或词组"
                        }
                    },
                    "required": [
                        "original", "translation", "tokenized_translation", "translation_phrases",
                        "grammar_explanation", "redundant_tokens"
                    ]
                }
            }
        }

        prompt = """处理以下 TEXT_LANG 文本，并翻译成 TARGET_LANG。

【非常非常重要的说明！！！】
1. 所有翻译和解释都必须使用 TARGET_LANG（目标语言）。
2. 不要单独给每个词语法解释 - 只给整个句子一个完整的语法解释。
3. 词性标注（morphology）只能使用以下缩写，不要加其他文字：
   - n (名词), v (动词), adj (形容词), adv (副词), pron (代词), prep (介词), conj (连词), interj (感叹词), det (限定词)
4. morphology 字段必须只包含缩写，不要有其他内容！
5. 【输出约束】除了工具调用的JSON输出外，不要添加任何其他文本、解释或说明。直接生成工具调用所需的JSON参数即可。

═══════════════════════════════════════════════════════════
【最最最重要！！！translation 数组的分词原则！！！】
═══════════════════════════════════════════════════════════

translation 数组中每个条目的 text 字段代表原文中的一个"词"。

【核心原则：遵循源语言的自然词边界】
你是一个语言专家，你精通所有语言的正字法和语法规则。请根据 TEXT_LANG 自身的语言规则来判断什么是"一个词"，而不是套用其他语言的分词标准。

【什么是一个"词"？】
一个"词"是原文中连续出现的、在该语言的词典中可以查到的最小意义单位。
判断标准：这个形式能否作为独立条目出现在该语言的词典中？

【关键规则】
1. 遵循该语言的正字法惯例：每种语言都有自己的词边界规则。连字符(-)、撇号(')等字符在某些语言中是词的内部组成部分，在另一些语言中可能是分隔符。请根据该语言自身的正字法来判断。
2. 变位/屈折形式是单个词：不要将变位形式拆分为词干+词缀。词的形态信息放在 morphology 字段，不通过拆分来表达。
3. 尊重该语言的自然词边界：用空格分隔词语的语言按空格分词；不用空格的语言按语言学上的词边界分词。
4. 【极其重要·固定搭配与多词表达】只有当满足以下全部条件时，才将多个词合并为一个 token：
   - 整体含义无法从各组成部分的字面含义推导出来（即语义不可组合）
   - 在词典中作为独立词条存在（如习语、固定搭配）
   - 替换其中任何一个词都会导致整体含义改变或表达不自然
5. 【极其重要·标点禁令】text 字段绝对禁止包含任何标点符号（句号、逗号、问号、感叹号、分号、冒号、省略号等）。标点不属于任何 token，它们不属于任何词。但连字符(-)和撇号(')如果在该语言中是词的内部组成部分则必须保留。所有标点符号必须被排除在 token 之外，只保留纯文字内容。
6. 所有条目的 text 去除标点后按顺序拼接必须等于原文去除标点后的内容，不能遗漏或增加文字内容。标点符号被完全丢弃，不属于任何 token。每个文字字符必须且只能属于一个 token，不能重叠，也不能重复出现。
7. 【极其重要·禁止增减原则】translation 数组中的 text 条目必须与原文中的词语一一对应，绝对不能随意增加原文中不存在的 token，也不能将原文中的一个词拆分成多个 token。每个 text 必须对应原文中一个真实存在的词语，不得凭空添加任何词语、解释性文字或冗余内容。
8. 绝对禁止将一个完整的词拆分成字符、音节或语素。

═══════════════════════════════════════════════════════════

按照以下结构处理文本：
- original: 原文文本 - 完全保留原始空格！！！
- translation: 对象数组，每个对象包含：
  - text: 原文中的一个词（严格遵循源语言的自然词边界！）
  - phonetic: 发音标注。使用该语言最常用、最被广泛认可的注音系统——可以是 IPA、拼音、罗马字或其他母语者和学习者期望的标准注音方式。声调语言需标注声调信息
  - morphology: 只能是词性缩写（如 n, v, adj）
  - meaning: 基于上下文的 TARGET_LANG 释义，简洁的几个独立词，不需要用完整句子解释
- tokenized_translation: 完整自然的 TARGET_LANG 翻译，正常句子格式。【极其重要】必须翻译完整，不能遗漏任何内容，原文的每个语义成分都必须体现在翻译中。原文中的说话者标识（如 A:、B:、Speaker 1: 等）必须在译文中完整保留，不得省略
- translation_phrases: 将 tokenized_translation 按目标语言的词（token）进行分词后的结果，用于翻译排序练习。必须至少拆分为2个片段！【核心原则·这是对目标语言翻译的分词，不是对源语言的分词】每个片段应该是目标语言翻译中的一个词或固定搭配。【拆分原则·严格遵循目标语言的自然词边界】1.遵循目标语言的自然词边界：用空格分隔词语的语言按空格分词；不用空格的语言按语言学上的词边界分词，每个片段应该是一个可以在该语言词典中查到的最小意义单位或固定多词表达；2.【极其重要·禁止按标点拆分】绝对不能按标点符号（逗号、句号等）来拆分片段！标点符号必须被丢弃，不属于任何片段。拆分的依据是目标语言的词边界，而不是标点符号的位置；3.变位/屈折形式是单个片段；4.【极其重要·固定搭配与多词表达】当两个或多个连续的词构成固定搭配、短语动词、习语、惯用语等非组合性表达时，必须作为一个片段；5.【极其重要·标点禁令】每个片段绝对禁止包含任何标点符号；6.所有片段去除标点后按顺序拼接必须等于 tokenized_translation 去除标点后的内容；7.【极其重要·禁止增减原则】所有片段必须与 tokenized_translation 中的词语一一对应；8.虚词可以与相邻词合并；9.每个片段不能是单个无意义虚词
- grammar_explanation: 整个文本的一个完整语法解释，用 TARGET_LANG
- redundant_tokens: 4个与原文相关的合理冗余tokens，用于测验目的，必须全部使用TARGET_LANG。【极其重要】每个冗余token必须是单个独立的词，不能是多个词组成的短语或词组

【重要要求】
- 翻译题应该用整个句子的翻译按token进行拆分后的结果作为答案，而不是分别每个单词的意思所组成的
- 【极其重要·禁止空白字段】translation 数组中每个条目的 phonetic、morphology、meaning 字段都必须有实际内容，绝对不能留空！即使是虚词、介词等也必须填写完整的音标、词性和释义。如果某个词的音标不确定，请给出最合理的标注，但绝不能留空字符串
- 生成冗余词时要注意：
  1. 必须使用TARGET_LANG（目标语言）生成冗余词
  2. 【极其重要】每个冗余token必须是单个独立的词，不能是多个词组成的短语或词组
  3. 冗余词的意思不能太相近，要避免多个冗余词都表达类似的含义
  4. 确保使用错误的答案组成的意思不是合理的，也不能是与正确答案近似的意思
  5. 冗余词应该是容易混淆但明显不同的概念
  6. 【极其重要】冗余词替换正确答案中的对应词后，组成的句子意思不能与原句意思相同或近似

翻译时请参考上下文，使用符合TARGET_LANG母语者日常表达的翻译，不要机械直译，要自然流畅但不需要文学化。

要处理的文本：
CONTEXT_SENTENCES

【待处理文本】
TEXT_CONTENT

请严格按照 tool 定义的 JSON 结构返回所有字段，不要遗漏任何 required 字段。
"""

        prompt = prompt.replace("TEXT_LANG", get_lang_name(source_lang))
        prompt = prompt.replace("TARGET_LANG", get_lang_name(target_lang))
        prompt = prompt.replace("TEXT_CONTENT", text)

        if context_sentences:
            before = context_sentences.get("before", [])
            after = context_sentences.get("after", [])
            if before or after:
                context_section = "【上下文】\n"
                if before:
                    context_section += "前文：\n" + "\n".join(before) + "\n"
                if after:
                    context_section += "后文：\n" + "\n".join(after) + "\n"
                prompt = prompt.replace("CONTEXT_SENTENCES", context_section)
            else:
                prompt = prompt.replace("CONTEXT_SENTENCES", "")
        else:
            prompt = prompt.replace("CONTEXT_SENTENCES", "")

        messages = [{"role": "user", "content": prompt}]

        response = await call_with_rotation(messages, [tool_def], temperature=0.0, max_tokens=16384)
        try:
            for choice in response["choices"]:
                if "tool_calls" in choice["message"]:
                    tool_call = choice["message"]["tool_calls"][0]
                    args = json.loads(tool_call["function"]["arguments"])
                    if "translation" in args and isinstance(args["translation"], str):
                        repaired_tr = _repair_truncated_json(args["translation"])
                        args["translation"] = repaired_tr if isinstance(repaired_tr, list) else []
                    return args
            return {}
        except Exception as e:
            print(f"Tool call failed: {e}")
            print(f"Response: {response}")
            return {}

    async def process_remaining_words(self, words: list, source_lang: str, target_lang: str, context: str = ""):
        if not words:
            return []

        tool_def = {
            "type": "function",
            "function": {
                "name": "generate_remaining_words",
                "description": "为遗漏的单词生成词信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "words": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "phonetic": {"type": "string", "description": "Pronunciation of this word. Use the most commonly used and widely recognized pronunciation notation for the source language — this may be IPA, pinyin, romaji, or any other standard system that native speakers and learners would expect. For tonal languages, include tone information."},
                                    "morphology": {"type": "string"},
                                    "meaning": {"type": "string", "description": "Meaning in TARGET_LANG based on the context - concise, just a few independent words, not a full sentence explanation"}
                                },
                                "required": [
                                    "text", "phonetic",
                                    "morphology", "meaning"
                                ]
                            }
                        }
                    },
                    "required": ["words"]
                }
            }
        }

        words_str = ", ".join(words)
        target_lang_name = get_lang_name(target_lang)
        prompt = f"""以下单词在之前的处理中被遗漏了，请为它们生成词信息，使用 {target_lang_name} 输出。

遗漏的单词：{words_str}

上下文句子：{context}

请为每个单词提供：
1. text: 单词本身
2. phonetic: 发音标注。使用该语言最常用、最被广泛认可的注音系统——可以是 IPA、拼音、罗马字或其他母语者和学习者期望的标准注音方式。声调语言需标注声调信息
3. morphology: 词性缩写（如 n, v, adj, adv, prep, conj, pron, det 等）
4. meaning: 基于上下文的 {target_lang_name} 释义，简洁的几个独立词，不需要用完整句子解释

【重要】必须为每一个遗漏的单词都生成条目，不要遗漏任何一个！
【输出约束】除了工具调用的JSON输出外，不要添加任何其他文本、解释或说明。"""

        messages = [{"role": "user", "content": prompt}]

        response = await call_with_rotation(messages, [tool_def], temperature=0.0, max_tokens=16384)

        try:
            for choice in response["choices"]:
                if "tool_calls" in choice["message"]:
                    tool_call = choice["message"]["tool_calls"][0]
                    args = json.loads(tool_call["function"]["arguments"])
                    entries = args.get("words", [])
                    if isinstance(entries, str):
                        entries = _repair_truncated_json(entries)
                    if not isinstance(entries, list):
                        entries = []
                    valid_entries = [e for e in entries if isinstance(e, dict) and "text" in e]
                    print(f"[DEBUG] process_remaining_words returned {len(valid_entries)} valid entries")
                    return valid_entries
            return []
        except Exception as e:
            print(f"Process remaining words failed: {e}")
            return []
