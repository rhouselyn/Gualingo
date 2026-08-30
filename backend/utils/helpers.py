"""通用工具函数与常量。"""

import re
import json
import asyncio
import time
import unicodedata

from text_processor import is_punctuation_only, strip_edge_punctuation, is_source_lang_text, NO_SPACE_LANGUAGES


class RateLimiter:
    def __init__(self, rpm=None, interval=None):
        if interval is not None:
            self.interval = interval
        elif rpm is not None and rpm > 0:
            self.interval = 60.0 / rpm
        else:
            self.interval = 1.0
        self.last_call = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_call
            if elapsed < self.interval:
                wait_time = self.interval - elapsed
                await asyncio.sleep(wait_time)
            self.last_call = time.time()


MAX_SENTENCE_WORDS_FOR_QUIZ = 8


def is_speaker_label(text):
    if not text or not isinstance(text, str):
        return False
    stripped = text.strip()
    return bool(re.match(r'^[A-Za-z\u0410-\u042F\u0430-\u044F]\s*[:：]$', stripped))


def vocab_sort_key(entry):
    """按索引顺序排序：先按 sentence_index，再按 token_index"""
    si = entry.get("sentence_index", 9999)
    ti = entry.get("token_index", 9999)
    return (si, ti)


def get_translation_phrases(translation_result, max_phrases=6):
    if not translation_result or not isinstance(translation_result, dict):
        return []

    llm_phrases = translation_result.get("translation_phrases", [])
    if isinstance(llm_phrases, list) and len(llm_phrases) >= 2:
        valid = [p.strip() for p in llm_phrases if isinstance(p, str) and p.strip() and not is_punctuation_only(p)]
        if len(valid) >= 2:
            return valid[:max_phrases]

    raw_translation = translation_result.get("tokenized_translation", "")
    if raw_translation and isinstance(raw_translation, str):
        return split_translation_to_phrases(raw_translation, max_phrases)

    return []


def split_translation_to_phrases(translation, max_phrases=8):
    if not translation or not isinstance(translation, str):
        return [translation] if translation else []

    parts = re.split(r'[，。、；：！？,;:!?]', translation)
    parts = [p.strip() for p in parts if p.strip() and not is_punctuation_only(p)]

    if not parts:
        chars = list(translation)
        chunk_size = max(1, len(chars) // max_phrases)
        parts = [''.join(chars[i:i+chunk_size]) for i in range(0, len(chars), chunk_size)]

    if len(parts) <= max_phrases:
        return parts

    result = []
    current = ""
    for p in parts:
        if current:
            candidate = current + "，" + p
            if len(result) + 1 + (1 if candidate else 0) <= max_phrases:
                current = candidate
            else:
                result.append(current)
                current = p
        else:
            current = p

    if current:
        result.append(current)

    while len(result) > max_phrases:
        last = result.pop()
        result[-1] = result[-1] + "，" + last

    return result


def select_key_tokens(seg_words, max_tokens=10):
    content_words = []
    short_words = []
    for w in seg_words:
        if len(w) <= 1:
            short_words.append(w)
        else:
            content_words.append(w)

    if len(content_words) <= max_tokens:
        result = content_words + short_words[:max(0, max_tokens - len(content_words))]
    else:
        step = len(content_words) / max_tokens
        result = [content_words[int(i * step)] for i in range(max_tokens)]

    return result[:max_tokens]


def get_fallback_options(correct_meaning, file_id, count=3):
    import random as rnd
    from utils.state import storage
    distractors = []
    try:
        vocab_data = storage.load_vocab(file_id)
        all_vocab = vocab_data.get("vocab", vocab_data) if isinstance(vocab_data, dict) else vocab_data
        candidates = []
        for v in all_vocab:
            meaning = v.get("meaning") or v.get("enriched_meaning") or ""
            if meaning and meaning != correct_meaning:
                candidates.append(meaning)
        rnd.shuffle(candidates)
        distractors = candidates[:count]
    except:
        pass
    while len(distractors) < count:
        distractors.append(f"释义{len(distractors)+1}")
    return distractors


def fix_llm_options_result(result: dict, source_lang="en", file_id=None) -> dict:
    if not isinstance(result, dict):
        return result
    mc = result.get("multiple_choice")
    if isinstance(mc, dict) and "options" in mc and isinstance(mc["options"], list):
        raw_options = mc["options"]
        correct_text = result.get("enriched_meaning", result.get("meaning", ""))

        normalized_options = []
        for opt in raw_options:
            if isinstance(opt, dict) and "text" in opt:
                text = opt["text"]
                is_correct = opt.get("is_correct", None)
                if is_correct is not None:
                    if isinstance(is_correct, str):
                        is_correct = is_correct.lower() in ("true", "yes", "1")
                    elif isinstance(is_correct, (int, float)):
                        is_correct = bool(is_correct)
                    else:
                        is_correct = bool(is_correct)
                    normalized_options.append({"text": text, "is_correct": is_correct})
                else:
                    normalized_options.append({"text": text, "is_correct": False})
            elif isinstance(opt, str):
                normalized_options.append({"text": opt, "is_correct": False})

        if not any(o["is_correct"] for o in normalized_options):
            if normalized_options:
                normalized_options[0]["is_correct"] = True
            elif correct_text:
                normalized_options.insert(0, {"text": correct_text, "is_correct": True})

        filtered_options = []
        placeholder_pattern = re.compile(r'^(释义|含义|meaning|sense|definition)\s*\d+$', re.IGNORECASE)
        correct_opt = None
        for opt in normalized_options:
            if opt["is_correct"]:
                correct_opt = opt
            elif placeholder_pattern.match(opt["text"].strip()):
                continue
            else:
                filtered_options.append(opt)

        if correct_opt:
            filtered_options.insert(0, correct_opt)

        if len(filtered_options) < 4:
            existing_texts = {o["text"] for o in filtered_options}
            correct_text_val = correct_opt["text"] if correct_opt else correct_text
            fallback_distractors = get_fallback_options(correct_text_val, file_id, count=4 - len(filtered_options))
            for fd in fallback_distractors:
                if len(filtered_options) >= 4:
                    break
                if fd not in existing_texts:
                    filtered_options.append({"text": fd, "is_correct": False})
                    existing_texts.add(fd)

        if len(filtered_options) < 4:
            existing_texts = {o["text"] for o in filtered_options}
            generic_fallbacks = ["other meaning", "different sense", "unrelated", "alternative", "different concept"]
            for fb in generic_fallbacks:
                if len(filtered_options) >= 4:
                    break
                if fb not in existing_texts:
                    filtered_options.append({"text": fb, "is_correct": False})
                    existing_texts.add(fb)

        final_options = filtered_options[:4]
        correct_idx = next((i for i, o in enumerate(final_options) if o["is_correct"]), 0)
        correct_text_val = final_options[correct_idx]["text"]
        for o in final_options:
            o["is_correct"] = o["text"] == correct_text_val

        import random as _random
        _random.seed(hash(correct_text_val) + hash(file_id or ""))
        _random.shuffle(final_options)

        mc["options"] = final_options
        mc.pop("correct_answer", None)
        result["multiple_choice"] = mc
        return result
    if isinstance(mc, str) and not mc.strip():
        result.pop("multiple_choice", None)
    if "options" in result:
        raw_opts = result["options"]
        if isinstance(raw_opts, str):
            try:
                raw_opts = json.loads(raw_opts)
            except (json.JSONDecodeError, TypeError):
                raw_opts = []
        if isinstance(raw_opts, list):
            mc_options = []
            for opt in raw_opts:
                if isinstance(opt, dict) and "text" in opt:
                    mc_options.append(opt)
                elif isinstance(opt, str):
                    mc_options.append({"text": opt, "is_correct": False})
            if mc_options:
                result["multiple_choice"] = {
                    "options": mc_options
                }
    if "multiple_choice" not in result or not isinstance(result.get("multiple_choice"), dict) or "options" not in result.get("multiple_choice", {}):
        correct_meaning = result.get("enriched_meaning", result.get("meaning", ""))
        fallback_distractors = get_fallback_options(correct_meaning, file_id, count=3)
        fb_opts = [{"text": correct_meaning, "is_correct": True}]
        for fd in fallback_distractors:
            fb_opts.append({"text": fd, "is_correct": False})
        result["multiple_choice"] = {
            "options": fb_opts[:4]
        }
    return result


def get_listening_correct_words(sentence, sentence_data):
    clean_sentence = re.sub(r'^[A-Za-z\u0410-\u042F\u0430-\u044F]\s*[:：]\s*', '', sentence)

    def normalize_for_compare(text):
        return re.sub(r'[\s\u3000]+', '', re.sub(r'[^\w\u00C0-\u024F\u0400-\u052F\u0370-\u03FF\u0600-\u06FF\u0900-\u0D7F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u1000-\u109F\u10A0-\u10FF\u1100-\u11FF]', '', text)).lower()

    sentence_normalized = normalize_for_compare(clean_sentence)

    tr = sentence_data.get("translation_result", {})
    translation_tokens = tr.get("translation", [])

    if translation_tokens and isinstance(translation_tokens, list):
        raw_words = []
        for token in translation_tokens:
            if isinstance(token, dict) and "text" in token:
                t = token["text"].strip()
                if t and not is_punctuation_only(t) and not is_speaker_label(t):
                    cleaned = strip_edge_punctuation(t)
                    if cleaned and not is_speaker_label(cleaned):
                        raw_words.append(cleaned)

        if raw_words:
            tokens_normalized = normalize_for_compare(''.join(raw_words))

            if tokens_normalized == sentence_normalized:
                return raw_words

            deduped_words = []
            seen = set()
            for w in raw_words:
                key = w.lower()
                if key not in seen:
                    seen.add(key)
                    deduped_words.append(w)
            deduped_normalized = normalize_for_compare(''.join(deduped_words))
            if deduped_normalized == sentence_normalized:
                return deduped_words

            words_from_sentence = [w for w in clean_sentence.split() if w.strip()]
            words_cleaned = []
            for w in words_from_sentence:
                w_clean = strip_edge_punctuation(w)
                if w_clean and not is_punctuation_only(w_clean):
                    words_cleaned.append(w_clean)
            if words_cleaned and normalize_for_compare(''.join(words_cleaned)) == sentence_normalized:
                return words_cleaned

            return raw_words if tokens_normalized else deduped_words

    source_lang = sentence_data.get("source_lang", "en")
    if source_lang in NO_SPACE_LANGUAGES:
        return [c for c in clean_sentence if c.strip() and not is_punctuation_only(c)]

    words = [w for w in clean_sentence.split() if w.strip()]
    filtered = []
    for w in words:
        w_clean = strip_edge_punctuation(w)
        if w_clean and not is_punctuation_only(w_clean):
            filtered.append(w_clean)
    return filtered


def get_listening_distractors_from_sentences(sentence, all_sentences, correct_lower_set):
    distractor_words = []
    distractor_set = set()
    for sd in all_sentences:
        other_s = sd.get("sentence", "")
        if not other_s or other_s == sentence:
            continue
        other_tr = sd.get("translation_result", {})
        other_translation = other_tr.get("translation", [])
        if other_translation and isinstance(other_translation, list):
            for token in other_translation:
                if isinstance(token, dict) and "text" in token:
                    vt = token["text"].strip()
                    if vt and not is_punctuation_only(vt) and vt.lower() not in correct_lower_set and vt.lower() not in distractor_set:
                        distractor_words.append(vt)
                        distractor_set.add(vt.lower())
        if not (other_translation and isinstance(other_translation, list)):
            clean_other = re.sub(r'^[A-Za-z]\s*[:：]\s*', '', other_s)
            for w in clean_other.split():
                w_clean = strip_edge_punctuation(w)
                if w_clean and not is_punctuation_only(w_clean) and w_clean.lower() not in correct_lower_set and w_clean.lower() not in distractor_set:
                    distractor_words.append(w_clean)
                    distractor_set.add(w_clean.lower())
    return distractor_words, distractor_set


def filter_eligible_sentences(sentences):
    eligible = []
    for s in sentences:
        if "sentence" not in s:
            continue
        word_count = s.get("word_count", 0)
        if word_count < 2:
            if "translation_result" in s and "translation" in s["translation_result"]:
                word_count = len(s["translation_result"]["translation"])
            if word_count < 2:
                continue
        eligible.append(s)
    return eligible


def find_item_in_plan(plan, flat_index):
    accumulated = 0
    for unit_id, unit_plan in enumerate(plan):
        items = unit_plan.get("items", [])
        if flat_index < accumulated + len(items):
            return unit_id, flat_index - accumulated
        accumulated += len(items)
    return None, None


def get_unit_flat_range(plan, target_unit_id):
    accumulated = 0
    for i, unit_plan in enumerate(plan):
        items = unit_plan.get("items", [])
        if i == target_unit_id:
            return accumulated, accumulated + len(items)
        accumulated += len(items)
    return None, None


def _is_word_item_learned(item, vocab, learned_words):
    """判断单元项中的单词是否属于已学集合（仅对 word 类型有效）"""
    if not learned_words:
        return False
    if item.get("type") != "word":
        return False
    vocab_idx = item.get("vocab_index")
    if vocab_idx is None or vocab_idx >= len(vocab):
        return False
    word = vocab[vocab_idx].get("word", "").lower()
    return word in learned_words


def get_filtered_unit_total(items, vocab, learned_words, only_new_words):
    """根据开关计算单元内需要展示的题目数量"""
    if not only_new_words or not learned_words:
        return len(items)
    count = 0
    for item in items:
        if _is_word_item_learned(item, vocab, learned_words):
            continue
        count += 1
    return count


def get_filtered_step_in_unit(items, vocab, learned_words, only_new_words, original_step):
    """返回原下标在过滤后列表中的位置（0-based），若已被过滤则返回其在过滤后列表中应有的下标"""
    if not only_new_words or not learned_words:
        return original_step
    step = 0
    for i, item in enumerate(items):
        if _is_word_item_learned(item, vocab, learned_words):
            continue
        if i >= original_step:
            return step
        step += 1
    return step


def find_next_non_learned_position(plan, vocab, learned_words, only_new_words, start_index):
    """从 start_index 开始寻找下一个需要展示的题目（不包含已学单词的 word 项）。
    返回 (unit_id, step_in_unit, original_step)；找不到时返回 (None, None, None)。"""
    if not only_new_words or not learned_words:
        unit_id, step = find_item_in_plan(plan, start_index)
        return unit_id, step, step
    accumulated = 0
    for unit_id, unit_plan in enumerate(plan):
        items = unit_plan.get("items", [])
        for step, item in enumerate(items):
            flat_index = accumulated + step
            if flat_index < start_index:
                continue
            if _is_word_item_learned(item, vocab, learned_words):
                continue
            return unit_id, step, step
        accumulated += len(items)
    return None, None, None
