"""后台处理与练习生成相关函数。"""

import re
import json
import random
import asyncio
import time

from llm_api import get_settings, get_lang_name
from text_processor import TextProcessor, BACKUP_VOCAB, BACKUP_VOCAB_BY_LANG, is_punctuation_only, is_source_lang_text, strip_edge_punctuation, NO_SPACE_LANGUAGES
from utils.state import llm_api, text_processor, storage, processing_status, word_gen_state
from utils.helpers import (
    RateLimiter, vocab_sort_key, is_speaker_label, is_punctuation_only as _is_punct,
    get_translation_phrases, split_translation_to_phrases, select_key_tokens,
    fix_llm_options_result, get_fallback_options, get_listening_correct_words,
    get_listening_distractors_from_sentences, filter_eligible_sentences,
    find_item_in_plan, get_unit_flat_range, _is_word_item_learned,
    get_filtered_unit_total, get_filtered_step_in_unit, find_next_non_learned_position,
    MAX_SENTENCE_WORDS_FOR_QUIZ,
)


async def process_text_background(file_id: str, text: str, source_lang: str, target_lang: str, rpm: int = 20):
    try:
        t_total_start = time.time()
        app_prefs = storage.load_user_preferences()
        retry_interval = app_prefs.get("retry_interval", 1.0)
        print(f"[DEBUG] 开始处理文件 {file_id}, 请求间隔={retry_interval}s")
        _preserve = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status[file_id]}
        processing_status[file_id] = {"status": "processing", "progress": 0, "current_sentence": 0, "total_sentences": 0, **_preserve}

        storage.save_language_settings(file_id, source_lang, target_lang)

        t_split_start = time.time()
        sentences = text_processor.split_sentences(text)
        total_sentences = len(sentences)
        t_split_end = time.time()
        print(f"[TIMING] 句子分割: {t_split_end - t_split_start:.3f}s, 共 {total_sentences} 个句子")

        _preserve2 = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status[file_id]}
        processing_status[file_id] = {"status": "processing", "progress": 0, "current_sentence": 0, "total_sentences": total_sentences, **_preserve2}

        results_dict = {}
        completed_indices = set()

        async def process_single_sentence(idx, sentence):
            if not sentence.strip():
                return idx, None

            before_indices = [i for i in range(max(0, idx - 2), idx)]
            after_indices = [i for i in range(idx + 1, min(len(sentences), idx + 3))]
            before_sentences = [sentences[i] for i in before_indices if sentences[i].strip()]
            after_sentences = [sentences[i] for i in after_indices if sentences[i].strip()]
            context_sentences = {"before": before_sentences, "after": after_sentences} if (before_sentences or after_sentences) else None

            t_sentence_start = time.time()

            t_llm_start = time.time()
            print(f"[DEBUG] 正在翻译句子 {idx+1}/{total_sentences}: {repr(sentence)}")
            sentence_translation_result = await text_processor.process_translation(
                sentence,
                source_lang,
                target_lang,
                llm_api,
                context_sentences
            )
            t_llm_end = time.time()
            print(f"[TIMING] 句子 {idx+1} LLM翻译调用: {t_llm_end - t_llm_start:.3f}s")

            t_validate_start = time.time()
            sentence_translation_result = text_processor.validate_and_complete_translation(
                sentence, sentence_translation_result, source_lang
            )
            t_validate_end = time.time()
            print(f"[TIMING] 句子 {idx+1} 验证补全: {t_validate_end - t_validate_start:.3f}s")

            t_extract_start = time.time()
            sentence_words = text_processor.extract_words(sentence, source_lang)
            t_extract_end = time.time()
            print(f"[TIMING] 句子 {idx+1} 单词提取: {t_extract_end - t_extract_start:.3f}s")

            translation_words = set()
            if isinstance(sentence_translation_result, dict) and "translation" in sentence_translation_result:
                for token in sentence_translation_result["translation"]:
                    if isinstance(token, dict) and "text" in token:
                        translation_words.add(token["text"].lower())

            if source_lang in NO_SPACE_LANGUAGES:
                def _norm(text):
                    return re.sub(r'[\s\u3000]+', '', re.sub(r'[^\w\u00C0-\u024F\u0400-\u052F\u0370-\u03FF\u0600-\u06FF\u0900-\u0D7F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u1000-\u109F\u10A0-\u10FF\u1100-\u11FF]', '', text)).lower()
                sentence_norm = _norm(sentence)
                tokens_norm = _norm(''.join(translation_words))
                missing_words = [] if tokens_norm == sentence_norm else []
            else:
                multiword_components = set()
                for tw in translation_words:
                    if ' ' in tw:
                        for part in tw.split():
                            multiword_components.add(part.lower())

                missing_words = []
                for w in sentence_words:
                    w_clean = strip_edge_punctuation(w).lower()
                    if w_clean and w_clean not in translation_words and w_clean not in multiword_components and not is_punctuation_only(w):
                        missing_words.append(strip_edge_punctuation(w))

            if missing_words:
                print(f"[DEBUG] 发现遗漏单词: {missing_words}, 正在补充处理...")
                t_missing_start = time.time()
                remaining_entries = await llm_api.process_remaining_words(
                    missing_words, source_lang, target_lang, sentence
                )
                t_missing_end = time.time()
                print(f"[TIMING] 句子 {idx+1} 遗漏单词补充LLM调用: {t_missing_end - t_missing_start:.3f}s")
                if remaining_entries:
                    if isinstance(sentence_translation_result, dict) and "translation" in sentence_translation_result:
                        translation_text_lower = []
                        for token in sentence_translation_result["translation"]:
                            if isinstance(token, dict) and "text" in token:
                                translation_text_lower.append(token["text"].lower())

                        for entry in remaining_entries:
                            if isinstance(entry, dict) and "text" in entry:
                                word = entry["text"]
                                if word.lower() not in translation_text_lower:
                                    sentence_translation_result["translation"].append(entry)
                                    translation_text_lower.append(word.lower())

                    print(f"[DEBUG] 补充了 {len(remaining_entries)} 个遗漏单词")

            sentence_data = {
                "sentence": sentence,
                "source_lang": source_lang,
                "translation_result": sentence_translation_result
            }
            t_sentence_end = time.time()
            print(f"[TIMING] 句子 {idx+1} 总耗时: {t_sentence_end - t_sentence_start:.3f}s")
            return idx, sentence_data

        tasks = [asyncio.create_task(process_single_sentence(i, s)) for i, s in enumerate(sentences)]

        for coro in asyncio.as_completed(tasks):
            idx, sentence_data = await coro
            if sentence_data is not None:
                results_dict[idx] = sentence_data
            completed_indices.add(idx)

            max_sequential = -1
            for ci in sorted(completed_indices):
                if ci == max_sequential + 1:
                    max_sequential = ci
                else:
                    break

            all_completed_translations = []
            for si in sorted(results_dict.keys()):
                all_completed_translations.append(results_dict[si])

            partial_vocab = []
            for si, sd in enumerate(all_completed_translations):
                tr = sd.get("translation_result", {})
                if isinstance(tr, dict) and "translation" in tr:
                    for ti, token in enumerate(tr["translation"]):
                        if isinstance(token, dict) and "text" in token:
                            entry = {
                                "word": token["text"],
                                "ipa": token.get("phonetic", ""),
                                "meaning": token.get("meaning", "") or token.get("context_meaning", ""),
                                "tokens": [token["text"]],
                                "morphology": token.get("morphology", ""),
                                "sentence_index": si,
                                "token_index": ti
                            }
                            partial_vocab.append(entry)

            seen = set()
            unique_partial = []
            for entry in partial_vocab:
                word = entry.get("word", "").lower()
                if word not in seen and word:
                    seen.add(word)
                    unique_partial.append(entry)
            unique_partial.sort(key=vocab_sort_key)

            progress = int(len(completed_indices) / total_sentences * 100)
            _preserve3 = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status[file_id]}
            processing_status[file_id] = {
                "status": "processing",
                "progress": progress,
                "current_sentence": len(completed_indices),
                "total_sentences": total_sentences,
                "vocab": unique_partial,
                "sentence_translations": all_completed_translations,
                **_preserve3
            }
            print(f"[DEBUG] 更新状态: 进度 {progress}%, 已处理 {len(completed_indices)} 个句子, 词汇 {len(unique_partial)} 个")

        sentence_translations = [results_dict.get(i, {"sentence": sentences[i], "translation_result": {}}) for i in range(total_sentences)]

        all_vocab = []
        for i, sentence_data in enumerate(sentence_translations):
            translation_result = sentence_data.get("translation_result", {})
            if isinstance(translation_result, dict) and "translation" in translation_result:
                for ti, token in enumerate(translation_result["translation"]):
                    if isinstance(token, dict) and "text" in token:
                        word = token["text"]
                        if not word or is_punctuation_only(word):
                            continue
                        entry = {
                            "word": word,
                            "ipa": token.get("phonetic", ""),
                            "meaning": token.get("meaning", "") or token.get("context_meaning", ""),
                            "tokens": [word],
                            "morphology": token.get("morphology", ""),
                            "sentence_index": i,
                            "token_index": ti
                        }
                        all_vocab.append(entry)

        seen = set()
        unique_vocab = []
        for entry in all_vocab:
            word = entry.get("word", "")
            cleaned = strip_edge_punctuation(word)
            if cleaned != word:
                entry["word"] = cleaned
                tokens = entry.get("tokens", [])
                if tokens:
                    entry["tokens"] = [cleaned if t == word else t for t in tokens]
            word = cleaned.lower()
            if word not in seen and word:
                seen.add(word)
                unique_vocab.append(entry)
        all_vocab = unique_vocab

        all_words_lower = set(entry.get("word", "").lower() for entry in all_vocab)
        deduplicated = []
        for entry in all_vocab:
            tokens = entry.get("tokens", [])
            if tokens and len(tokens) >= 2:
                all_tokens_covered = all(
                    any(t.lower() == w.lower() for w in all_words_lower if w != entry.get("word", "").lower())
                    for t in tokens
                )
                if all_tokens_covered:
                    continue
            deduplicated.append(entry)
        all_vocab = deduplicated

        all_vocab.sort(key=vocab_sort_key)
        print(f"[DEBUG] 从所有句子中提取词典条目，共 {len(all_vocab)} 个单词: {[word['word'] for word in all_vocab]}")

        learned_words_set = set()
        for entry in all_vocab:
            word = entry.get("word", "").lower()
            if word and storage.find_global_word_cache(word, source_lang):
                learned_words_set.add(word)
        if learned_words_set:
            storage.save_learned_words(file_id, sorted(learned_words_set))
            print(f"[DEBUG] 已识别 {len(learned_words_set)} 个已学单词: {sorted(learned_words_set)}")

        storage.save_pipeline_data(file_id, sentence_translations)
        storage.save_vocab(file_id, all_vocab)

        if all_vocab:
            generate_and_save_learning_plan(file_id, all_vocab, sentence_translations)

        _preserve4 = {k: processing_status[file_id][k] for k in ("original_text", "title") if k in processing_status[file_id]}
        processing_status[file_id] = {
            "status": "completed",
            "progress": 100,
            "vocab": all_vocab,
            "sentence_translations": sentence_translations,
            **_preserve4
        }
        t_total_end = time.time()
        print(f"[TIMING] ========== 全部处理完成 ==========")
        print(f"[TIMING] 总耗时: {t_total_end - t_total_start:.3f}s")
        print(f"[TIMING] 句子数: {total_sentences}, 单词数: {len(all_vocab)}")

        if file_id not in word_gen_state:
            word_gen_state[file_id] = {
                "running": False,
                "vocab": all_vocab,
                "priority_queue": [],
                "task": None,
                "processing_words": set()
            }
        state = word_gen_state[file_id]
        state["vocab"] = all_vocab
        if "processing_words" not in state:
            state["processing_words"] = set()
        if "plan_position" not in state:
            state["plan_position"] = 0
        if not state["running"]:
            state["running"] = True
            state["task"] = asyncio.create_task(background_word_gen(file_id))
            print(f"[DEBUG] 自动启动单词详情生成")
    except Exception as e:
        print(f"[ERROR] 处理出错: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = str(e)
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
        raise  # ponytail: 让调用方也知道失败了，避免写入历史


async def process_single_word_gen(file_id, word_to_gen, vocab, source_lang, target_lang, temperature=0):
    state = word_gen_state.get(file_id)
    if not state:
        return
    processing = state.get("processing_words", set())
    if word_to_gen.lower() in {w.lower() for w in processing}:
        return
    processing.add(word_to_gen)
    try:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if storage.load_word_cache(file_id, word_to_gen):
                    return
                word_entry = None
                for v in vocab:
                    if v.get("word", "").lower() == word_to_gen.lower():
                        word_entry = v
                        break
                if not word_entry:
                    return
                sentences = storage.load_pipeline_data(file_id)
                context = ""
                context_sentences = []
                if sentences:
                    has_cjk = any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\uac00' <= c <= '\ud7af' for c in word_to_gen[:10])
                    if has_cjk:
                        word_pattern = re.compile(re.escape(word_to_gen), re.IGNORECASE)
                    else:
                        word_pattern = re.compile(r'\b' + re.escape(word_to_gen) + r'\b', re.IGNORECASE)
                    for sent_idx, sentence_data in enumerate(sentences):
                        if "sentence" in sentence_data:
                            if word_pattern.search(sentence_data["sentence"]):
                                context = sentence_data["sentence"]
                                translation = ""
                                if "translation_result" in sentence_data:
                                    translation = sentence_data["translation_result"].get("tokenized_translation", "")
                                context_sentences.append({
                                    "sentence": sentence_data["sentence"],
                                    "translation": translation,
                                    "sentence_index": sent_idx
                                })
                    if not context and sentences:
                        context = sentences[0].get("sentence", "")
                correct_meaning = word_entry.get("meaning", "")
                if not correct_meaning:
                    if "translation" in word_entry:
                        correct_meaning = word_entry["translation"]
                    elif "context_meaning" in word_entry:
                        correct_meaning = word_entry["context_meaning"]

                print(f"[DEBUG] Background word gen: {word_to_gen} (attempt {attempt + 1})")
                options_result = await llm_api.generate_multiple_choice(
                    word_to_gen,
                    correct_meaning,
                    context,
                    target_lang,
                    source_lang,
                    temperature
                )

                placeholder_pattern = re.compile(r'(释义|含义|意思|meaning|definition)\s*\d', re.IGNORECASE)
                enriched = options_result.get("enriched_meaning", "")
                if placeholder_pattern.search(enriched):
                    print(f"[WARN] Detected placeholder text in word gen for '{word_to_gen}', retrying...")
                    options_result = await llm_api.generate_multiple_choice(
                        word_to_gen,
                        correct_meaning,
                        context,
                        target_lang,
                        source_lang,
                        temperature
                    )
                    enriched = options_result.get("enriched_meaning", "")
                    if placeholder_pattern.search(enriched):
                        print(f"[WARN] Still placeholder text after retry for '{word_to_gen}', using fallback")
                        if placeholder_pattern.search(enriched):
                            options_result["enriched_meaning"] = correct_meaning

                options_result = fix_llm_options_result(options_result, source_lang, file_id)
                cache_data = dict(options_result)
                cache_data["word"] = options_result.get("word", word_to_gen)
                cache_data["ipa"] = word_entry.get("ipa", "")
                cache_data["meaning"] = correct_meaning
                cache_data["examples"] = options_result.get("examples", [])
                cache_data["context"] = context
                cache_data["context_sentences"] = context_sentences
                cache_data["morphology"] = word_entry.get("morphology", "")
                cache_data["variants_detail"] = options_result.get("variants_detail", [])
                cache_data["memory_hint"] = options_result.get("memory_hint", "")
                cache_data["enriched_meaning"] = options_result.get("enriched_meaning", correct_meaning)
                cache_data["multiple_choice"] = options_result.get("multiple_choice", {})
                if "context_translations" in cache_data:
                    del cache_data["context_translations"]
                storage.save_word_cache(file_id, word_to_gen, cache_data)
                print(f"[DEBUG] Cached word gen: {word_to_gen}")
                return
            except Exception as e:
                print(f"[ERROR] Word gen failed for {word_to_gen} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    app_prefs = storage.load_user_preferences()
                    retry_delay = app_prefs.get("retry_interval", 1.0)
                    print(f"[DEBUG] Retrying {word_to_gen} in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    print(f"[ERROR] Word gen permanently failed for {word_to_gen} after {max_retries} attempts")
    finally:
        processing.discard(word_to_gen)


async def background_word_gen(file_id: str):
    state = word_gen_state.get(file_id)
    if not state:
        return
    language_settings = storage.load_language_settings(file_id)
    target_lang = language_settings["target_lang"]
    source_lang = language_settings.get("source_lang", "en")
    vocab = state["vocab"]

    plan = storage.load_learning_plan(file_id)
    plan_word_order = []
    if plan:
        seen_vocab_indices = set()
        for unit in plan:
            items = unit.get("items", [])
            for item in items:
                vi = item.get("vocab_index")
                if vi is not None and vi not in seen_vocab_indices:
                    seen_vocab_indices.add(vi)
                    plan_word_order.append(vi)
        for i in range(len(vocab)):
            if i not in seen_vocab_indices:
                plan_word_order.append(i)

    if not plan_word_order:
        plan_word_order = list(range(len(vocab)))

    first_uncached = None
    for pi, vi in enumerate(plan_word_order):
        if vi < len(vocab):
            w = vocab[vi].get("word", "")
            if w and not storage.load_word_cache(file_id, w):
                first_uncached = pi
                break
    if first_uncached is not None:
        state["plan_position"] = min(state.get("plan_position", 0), first_uncached)
    elif "plan_position" not in state:
        state["plan_position"] = len(plan_word_order)

    while state["running"]:
        word_to_gen = None
        if state["priority_queue"]:
            word_to_gen = state["priority_queue"].pop(0)
        elif state["plan_position"] < len(plan_word_order):
            vocab_idx = plan_word_order[state["plan_position"]]
            state["plan_position"] += 1
            if vocab_idx < len(vocab):
                word_to_gen = vocab[vocab_idx].get("word", "")

        if not word_to_gen:
            await asyncio.sleep(1)
            continue

        if storage.load_word_cache(file_id, word_to_gen):
            continue

        existing_cache = storage.find_global_word_cache(word_to_gen, source_lang)
        if existing_cache:
            import copy
            cached = copy.deepcopy(existing_cache)
            context_sents = []
            all_sentences = storage.load_pipeline_data(file_id)
            if all_sentences:
                word_pattern = re.compile(r'\b' + re.escape(word_to_gen) + r'\b', re.IGNORECASE)
                for sent_idx, sentence_data in enumerate(all_sentences):
                    if "sentence" in sentence_data:
                        if word_pattern.search(sentence_data["sentence"]):
                            translation = ""
                            if "translation_result" in sentence_data:
                                translation = sentence_data["translation_result"].get("tokenized_translation", "")
                            context_sents.append({
                                "sentence": sentence_data["sentence"],
                                "translation": translation,
                                "sentence_index": sent_idx
                            })
            if context_sents:
                cached["context_sentences"] = context_sents
                cached["context"] = context_sents[0]["sentence"]
            storage.save_word_cache(file_id, word_to_gen, cached)
            continue

        processing = state.get("processing_words", set())
        if word_to_gen.lower() in {w.lower() for w in processing}:
            continue

        asyncio.create_task(process_single_word_gen(file_id, word_to_gen, vocab, source_lang, target_lang))
        await asyncio.sleep(0.1)

    state["task"] = None


def generate_and_save_learning_plan(file_id: str, vocab, sentences):
    language_settings = storage.load_language_settings(file_id)
    source_lang = language_settings.get("source_lang", "en")

    random.seed(42)
    shuffled_indices = list(range(len(vocab)))
    random.shuffle(shuffled_indices)
    storage.save_shuffled_order(file_id, shuffled_indices)

    max_items_per_unit = 10

    word_to_shuffled_pos = {}
    for pos, idx in enumerate(shuffled_indices):
        word_to_shuffled_pos[idx] = pos

    sentence_quiz_info = []
    for sent_idx, sentence_data in enumerate(sentences):
        if "sentence" not in sentence_data:
            continue

        sentence = sentence_data["sentence"]
        if source_lang in NO_SPACE_LANGUAGES:
            word_count = len(sentence.replace(' ', ''))
        else:
            word_count = len(sentence.split())
        if word_count > MAX_SENTENCE_WORDS_FOR_QUIZ:
            continue

        tr = sentence_data.get("translation_result", {})
        if "translation" not in tr:
            continue

        translation_tokens = tr.get("translation", [])
        if not translation_tokens:
            continue

        covering_vocab_indices = []
        for vi, v in enumerate(vocab):
            v_tokens = v.get("tokens", [v["word"]])
            word_covers = False
            for wt in v_tokens:
                for token in translation_tokens:
                    if isinstance(token, dict) and "text" in token:
                        if wt.lower() == token["text"].lower() or wt.lower() in token["text"].lower() or token["text"].lower() in wt.lower():
                            word_covers = True
                            break
                if word_covers:
                    break
            if word_covers:
                covering_vocab_indices.append(vi)

        if not covering_vocab_indices:
            continue

        all_covered = True
        for token in translation_tokens:
            if isinstance(token, dict) and "text" in token:
                token_text = token["text"]
                token_translation = token.get("meaning", "")
                token_morphology = token.get("morphology", "")
                if len(token_text) <= 2 and not token_translation and not token_morphology:
                    continue
                token_text_lower = token_text.lower()
                token_covered = False
                for vi in covering_vocab_indices:
                    w = vocab[vi]
                    w_tokens = w.get("tokens", [w["word"]])
                    for wt in w_tokens:
                        if wt.lower() == token_text_lower or wt.lower() in token_text_lower or token_text_lower in wt.lower():
                            token_covered = True
                            break
                    if token_covered:
                        break
                if not token_covered:
                    all_covered = False
                    break

        if not all_covered:
            continue

        last_covering_shuffled_pos = max(word_to_shuffled_pos.get(vi, len(shuffled_indices)) for vi in covering_vocab_indices)

        sentence_quiz_info.append({
            "sentence": sentence,
            "sentence_data": sentence_data,
            "covering_vocab_indices": covering_vocab_indices,
            "last_covering_shuffled_pos": last_covering_shuffled_pos
        })

    sentence_quiz_info.sort(key=lambda x: x["last_covering_shuffled_pos"])

    plan = []
    unit_start_shuffled_pos = 0
    quiz_insertion_pointer = 0

    while unit_start_shuffled_pos < len(shuffled_indices):
        unit_end_shuffled_pos = min(unit_start_shuffled_pos + max_items_per_unit, len(shuffled_indices))

        unit_word_items = []
        for sp in range(unit_start_shuffled_pos, unit_end_shuffled_pos):
            vocab_idx = shuffled_indices[sp]
            unit_word_items.append({
                "type": "word",
                "vocab_index": vocab_idx,
                "_shuffled_pos": sp
            })

        unit_quiz_items = []
        while quiz_insertion_pointer < len(sentence_quiz_info):
            sqi = sentence_quiz_info[quiz_insertion_pointer]
            last_pos = sqi["last_covering_shuffled_pos"]

            if last_pos < unit_end_shuffled_pos:
                quiz_insertion_pointer += 1

                sentence = sqi["sentence"]
                sentence_data = sqi["sentence_data"]
                covering_vocab_indices = sqi["covering_vocab_indices"]
                tr = sentence_data.get("translation_result", {})
                translation_tokens = tr.get("translation", [])

                raw_translation = tr.get("tokenized_translation", "")
                correct_translation = raw_translation.strip() if raw_translation else ""

                correct_tokens = get_translation_phrases(tr, max_phrases=6)
                correct_tokens = [ct for ct in correct_tokens if not is_punctuation_only(ct)]

                if len(correct_tokens) >= 2 and len(correct_tokens) <= 8:
                    redundant_tokens = tr.get("redundant_tokens", [])
                    cleaned_redundant = []
                    correct_has_source_lang = any(is_source_lang_text(ct, source_lang) for ct in correct_tokens)
                    for rt in redundant_tokens:
                        rt_stripped = rt.strip()
                        if rt_stripped and rt_stripped not in correct_tokens and not is_punctuation_only(rt_stripped):
                            if correct_has_source_lang or not is_source_lang_text(rt_stripped, source_lang):
                                cleaned_redundant.append(rt_stripped)

                    selected_distractors = list(dict.fromkeys(cleaned_redundant))[:4]

                    if len(selected_distractors) < 4:
                        existing_set = set(correct_tokens) | set(selected_distractors)
                        for other_sent in sentences:
                            if other_sent.get("sentence") == sentence:
                                continue
                            other_tr = other_sent.get("translation_result", {})
                            other_phrases = get_translation_phrases(other_tr, max_phrases=10)
                            for op in other_phrases:
                                if op not in existing_set:
                                    if correct_has_source_lang or not is_source_lang_text(op, source_lang):
                                        selected_distractors.append(op)
                                        existing_set.add(op)
                                        if len(selected_distractors) >= 4:
                                            break
                            if len(selected_distractors) >= 4:
                                break

                    all_tokens = correct_tokens + selected_distractors

                    if not correct_translation.strip():
                        correct_translation = "".join(correct_tokens)

                    unit_quiz_items.append({
                        "type": "sentence_quiz",
                        "sentence": sentence,
                        "correct_translation": correct_translation,
                        "correct_tokens": correct_tokens,
                        "tokens": all_tokens,
                        "_last_covering_shuffled_pos": last_pos
                    })

                sentence_words_display = get_listening_correct_words(sentence, sentence_data)

                correct_lower_set = set(w.lower() for w in sentence_words_display)
                distractor_words, distractor_set = get_listening_distractors_from_sentences(sentence, sentences, correct_lower_set)

                for v in vocab:
                    v_tokens = v.get("tokens", [v["word"]])
                    for vt in v_tokens:
                        if vt.lower() not in correct_lower_set and vt.lower() not in distractor_set:
                            distractor_words.append(vt)
                            distractor_set.add(vt.lower())
                    if len(v_tokens) == 1 and v["word"].lower() not in correct_lower_set and v["word"].lower() not in distractor_set:
                        distractor_words.append(v["word"])
                        distractor_set.add(v["word"].lower())

                random.shuffle(distractor_words)
                num_distractors = max(2, len(sentence_words_display) // 2)
                distractor_words = distractor_words[:num_distractors]

                if len(distractor_words) < 2:
                    backup_vocab_list = BACKUP_VOCAB_BY_LANG.get(source_lang, BACKUP_VOCAB_BY_LANG["en"])
                    backup_distractors = list(backup_vocab_list)
                    random.shuffle(backup_distractors)
                    idx = 0
                    while len(distractor_words) < 2:
                        bd = backup_distractors[idx % len(backup_distractors)]
                        if bd.lower() not in correct_lower_set and bd.lower() not in distractor_set:
                            distractor_words.append(bd)
                            distractor_set.add(bd.lower())
                        idx += 1

                if sentence_words_display and len(sentence_words_display) >= 2:
                    unit_quiz_items.append({
                        "type": "listening_quiz",
                        "sentence": sentence,
                        "clean_sentence": re.sub(r'^[A-Za-z\u0410-\u042F\u0430-\u044F]\s*[:：]\s*', '', sentence),
                        "correct_words": sentence_words_display,
                        "distractor_words": distractor_words,
                        "_last_covering_shuffled_pos": last_pos
                    })
            else:
                break

        final_items = list(unit_word_items)

        quizzes_with_anchor = []
        for quiz in unit_quiz_items:
            last_pos = quiz.pop("_last_covering_shuffled_pos", 0)
            anchor_pos = 0
            for i, item in enumerate(final_items):
                if item.get("type") == "word" and item.get("_shuffled_pos", -1) >= last_pos:
                    anchor_pos = i + 1
                    break
            else:
                anchor_pos = len(final_items)
            quizzes_with_anchor.append((quiz, anchor_pos))

        random.shuffle(quizzes_with_anchor)

        for _ in range(len(quizzes_with_anchor)):
            min_anchor = min(a for _, a in quizzes_with_anchor)
            candidates = [(q, a) for q, a in quizzes_with_anchor if a == min_anchor]
            chosen = random.choice(candidates)
            quizzes_with_anchor.remove(chosen)
            quiz, anchor_pos = chosen
            insert_pos = random.randint(anchor_pos, max(anchor_pos, len(final_items)))
            final_items.insert(insert_pos, quiz)
            for i in range(len(quizzes_with_anchor)):
                q, a = quizzes_with_anchor[i]
                if a >= insert_pos:
                    quizzes_with_anchor[i] = (q, a + 1)

        for item in final_items:
            item.pop("_shuffled_pos", None)

        if final_items:
            plan.append({
                "unit_id": len(plan),
                "items": final_items
            })

        unit_start_shuffled_pos = unit_end_shuffled_pos

    final_plan = []
    flat_items = []
    for unit in plan:
        flat_items.extend(unit["items"])

    for i in range(0, len(flat_items), max_items_per_unit):
        chunk = flat_items[i:i + max_items_per_unit]
        final_plan.append({
            "unit_id": len(final_plan),
            "items": chunk
        })

    storage.save_learning_plan(file_id, final_plan)


async def generate_title(text: str, source_lang: str) -> str:
    try:
        messages = [
            {"role": "system", "content": "You are a title generator. Generate a very short title (max 20 characters) that summarizes the given text. If the text already has a clear title in the first line, use that as the title. Output ONLY the title, nothing else."},
            {"role": "user", "content": f"Generate a short title for this text (language: {get_lang_name(source_lang)}):\n\n{text[:500]}"}
        ]
        result = await llm_api.call_llm(messages, temperature=0.3)
        title = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        if title and len(title) <= 50:
            return title
    except Exception as e:
        print(f"[WARN] Title generation failed: {e}")
    first_line = text.strip().split('\n')[0].strip()
    return first_line[:20] + "..." if len(first_line) > 20 else first_line


async def pre_generate_next_word(file_id: str, vocab, next_index: int):
    try:
        language_settings = storage.load_language_settings(file_id)
        target_lang = language_settings["target_lang"]
        source_lang = language_settings.get("source_lang", "en")

        plan = storage.load_learning_plan(file_id)
        if not plan:
            return

        unit_id, step_in_unit = find_item_in_plan(plan, next_index)
        if unit_id is None:
            return

        items = plan[unit_id].get("items", [])
        if step_in_unit >= len(items):
            return

        next_item = items[step_in_unit]
        if next_item["type"] == "sentence_quiz":
            return

        vocab_idx = next_item["vocab_index"]
        random_word = vocab[vocab_idx]
        word = random_word["word"]

        if storage.load_word_cache(file_id, word):
            print(f"[DEBUG] 预生成单词已缓存: {word}")
            return

        sentences = storage.load_pipeline_data(file_id)
        context = ""
        context_sentences = []
        if sentences:
            word_pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            for sent_idx, sentence_data in enumerate(sentences):
                if "sentence" in sentence_data:
                    if word_pattern.search(sentence_data["sentence"]):
                        context = sentence_data["sentence"]
                        translation = ""
                        if "translation_result" in sentence_data:
                            translation = sentence_data["translation_result"].get("tokenized_translation", "")
                        context_sentences.append({
                            "sentence": sentence_data["sentence"],
                            "translation": translation,
                            "sentence_index": sent_idx
                        })
            if not context and sentences:
                context = sentences[0].get("sentence", "")

        correct_meaning = random_word.get("meaning", "")

        if not correct_meaning:
            if "context_meaning" in random_word:
                correct_meaning = random_word["context_meaning"]
            elif "translation" in random_word:
                correct_meaning = random_word["translation"]

        print(f"[DEBUG] 后台预生成单词信息: {word}")

        options_result = await llm_api.generate_multiple_choice(
            word,
            correct_meaning,
            context,
            target_lang,
            source_lang,
            0
        )
        options_result = fix_llm_options_result(options_result, source_lang, file_id)

        cache_data = dict(options_result)
        cache_data["word"] = options_result.get("word", word)
        cache_data["ipa"] = random_word.get("ipa", "")
        cache_data["meaning"] = correct_meaning
        cache_data["examples"] = options_result.get("examples", [])
        cache_data["context"] = context
        cache_data["context_sentences"] = context_sentences
        cache_data["morphology"] = random_word.get("morphology", "")
        cache_data["variants_detail"] = options_result.get("variants_detail", [])
        cache_data["memory_hint"] = options_result.get("memory_hint", "")
        cache_data["enriched_meaning"] = options_result.get("enriched_meaning", correct_meaning)
        cache_data["multiple_choice"] = options_result.get("multiple_choice", {})
        if "context_translations" in cache_data:
            del cache_data["context_translations"]

        storage.save_word_cache(file_id, word, cache_data)
        print(f"[DEBUG] 缓存预生成单词信息: {word}")

    except Exception as e:
        print(f"[ERROR] 预生成单词信息失败: {str(e)}")
