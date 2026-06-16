from typing import List, Set, Dict, Any
import string
import unicodedata

PUNCTUATION_CHARS = frozenset({
    '.', ',', '!', '?', ':', ';',
    '…', '⋯',
    '，', '。', '！', '？', '：', '；', '、',
    '؟', '،',
    '।', '॥',
    '။', '၊',
    '។', '៕', '៖',
    '։', '՜', '՞',
    '።', '፣',
    '།',
    '᪩', '᪪',
    '⳹', '⳾',
    '𐩖', '𐩗',
    '꘎', '꛳',
    '‽',
    '‼', '⁇', '⁈', '⁉',
    '¡', '¿',
    '«', '»', '‹', '›',
    '「', '」', '『', '』', '【', '】', '（', '）', '《', '》',
    '〈', '〉', '〔', '〕', '〖', '〗',
    '"', '"', '"', ''', ''', '`',
    '—', '–', '‐', '‑', '‒',
    '·', '•', '◦',
    '⁊',
})

def is_punctuation_only(text):
    if not text or not isinstance(text, str):
        return False
    stripped = text.strip()
    if not stripped:
        return True
    for ch in stripped:
        if ch in PUNCTUATION_CHARS:
            continue
        cat = unicodedata.category(ch)
        if cat.startswith('P') or cat.startswith('Z'):
            continue
        return False
    return True

WORD_INTERNAL_CHARS = frozenset({
    '-', '\u2010', '\u2011', '\u2012', '\u2013', '\u2014',
    "'", '\u2018', '\u2019', '\u201B',
})

def strip_edge_punctuation(text):
    if not text or not isinstance(text, str):
        return text
    cleaned = text
    while cleaned:
        if not cleaned[-1] in WORD_INTERNAL_CHARS and is_punctuation_only(cleaned[-1]):
            cleaned = cleaned[:-1]
        else:
            break
    while cleaned:
        if not cleaned[0] in WORD_INTERNAL_CHARS and is_punctuation_only(cleaned[0]):
            cleaned = cleaned[1:]
        else:
            break
    return cleaned

SCRIPT_RANGES = {
    'Latin': [
        (0x0041, 0x005A), (0x0061, 0x007A), (0x00C0, 0x024F),
        (0x1E00, 0x1EFF), (0x2C60, 0x2C7F), (0xA720, 0xA7FF), (0xAB30, 0xAB6F),
    ],
    'Cyrillic': [(0x0400, 0x052F)],
    'Greek': [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    'Arabic': [(0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF)],
    'Hebrew': [(0x0590, 0x05FF), (0xFB1D, 0xFB4F)],
    'Devanagari': [(0x0900, 0x097F), (0xA8E0, 0xA8FF)],
    'Bengali': [(0x0980, 0x09FF)],
    'Gurmukhi': [(0x0A00, 0x0A7F)],
    'Gujarati': [(0x0A80, 0x0AFF)],
    'Oriya': [(0x0B00, 0x0B7F)],
    'Tamil': [(0x0B80, 0x0BFF)],
    'Telugu': [(0x0C00, 0x0C7F)],
    'Kannada': [(0x0C80, 0x0CFF)],
    'Malayalam': [(0x0D00, 0x0D7F)],
    'Sinhala': [(0x0D80, 0x0DFF)],
    'Thai': [(0x0E00, 0x0E7F)],
    'Lao': [(0x0E80, 0x0EFF)],
    'Tibetan': [(0x0F00, 0x0FFF)],
    'Myanmar': [(0x1000, 0x109F), (0xAA60, 0xAA7F)],
    'Georgian': [(0x10A0, 0x10FF), (0x2D00, 0x2D2F)],
    'Hangul': [(0xAC00, 0xD7AF), (0x1100, 0x11FF), (0x3130, 0x318F)],
    'CJK': [(0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF), (0xF900, 0xFAFF)],
    'Hiragana': [(0x3040, 0x309F)],
    'Katakana': [(0x30A0, 0x30FF)],
    'Armenian': [(0x0530, 0x058F)],
    'Ethiopic': [(0x1200, 0x139F)],
    'Khmer': [(0x1780, 0x17FF)],
    'Thaana': [(0x0780, 0x07BF)],
}

LANG_SCRIPTS = {
    'en': {'Latin'}, 'fr': {'Latin'}, 'de': {'Latin'}, 'es': {'Latin'}, 'it': {'Latin'},
    'pt': {'Latin'}, 'nl': {'Latin'}, 'sv': {'Latin'}, 'da': {'Latin'}, 'nb': {'Latin'},
    'nn': {'Latin'}, 'ro': {'Latin'}, 'pl': {'Latin'}, 'cs': {'Latin'}, 'sk': {'Latin'},
    'hr': {'Latin'}, 'sl': {'Latin'}, 'bg': {'Cyrillic'}, 'ru': {'Cyrillic'}, 'uk': {'Cyrillic'},
    'be': {'Cyrillic'}, 'sr': {'Cyrillic'}, 'mk': {'Cyrillic'},
    'el': {'Greek'}, 'hy': {'Armenian'}, 'ka': {'Georgian'},
    'zh': {'CJK'}, 'zh-TW': {'CJK'}, 'yue': {'CJK'},
    'ja': {'CJK', 'Hiragana', 'Katakana'},
    'ko': {'Hangul', 'CJK'},
    'ar': {'Arabic'}, 'ars': {'Arabic'}, 'apc': {'Arabic'}, 'arz': {'Arabic'},
    'ary': {'Arabic'}, 'acm': {'Arabic'}, 'acq': {'Arabic'}, 'aeb': {'Arabic'},
    'he': {'Hebrew'}, 'mt': {'Latin'},
    'fa': {'Arabic'}, 'prs': {'Arabic'}, 'tg': {'Cyrillic'},
    'hi': {'Devanagari'}, 'mr': {'Devanagari'}, 'ne': {'Devanagari'},
    'bn': {'Bengali'}, 'as': {'Bengali'},
    'pa': {'Gurmukhi'}, 'gu': {'Gujarati'}, 'or': {'Oriya'},
    'ta': {'Tamil'}, 'te': {'Telugu'}, 'kn': {'Kannada'}, 'ml': {'Malayalam'},
    'si': {'Sinhala'},
    'th': {'Thai'}, 'lo': {'Lao'},
    'my': {'Myanmar'}, 'km': {'Khmer'},
    'tr': {'Latin'}, 'az': {'Latin'}, 'uz': {'Latin'}, 'kk': {'Cyrillic'},
    'ba': {'Cyrillic'}, 'tt': {'Cyrillic'},
    'fi': {'Latin'}, 'et': {'Latin'}, 'hu': {'Latin'},
    'vi': {'Latin'}, 'id': {'Latin'}, 'ms': {'Latin'}, 'tl': {'Latin'},
    'sw': {'Latin'}, 'ht': {'Latin'}, 'af': {'Latin'},
    'cy': {'Latin'}, 'ga': {'Latin'}, 'is': {'Latin'}, 'fo': {'Latin'},
    'sq': {'Latin'}, 'lt': {'Latin'}, 'lv': {'Latin'}, 'lb': {'Latin'},
    'eu': {'Latin'}, 'ca': {'Latin'}, 'gl': {'Latin'}, 'oc': {'Latin'},
    'vec': {'Latin'}, 'lmo': {'Latin'}, 'lij': {'Latin'}, 'scn': {'Latin'},
    'fur': {'Latin'}, 'sc': {'Latin'}, 'ast': {'Latin'}, 'szl': {'Latin'},
    'li': {'Latin'}, 'bs': {'Latin'},
    'sd': {'Arabic'}, 'ur': {'Arabic'},
    'yi': {'Hebrew'},
    'mag': {'Devanagari'}, 'mai': {'Devanagari'}, 'bho': {'Devanagari'},
    'awa': {'Devanagari'}, 'hne': {'Devanagari'},
    'ceb': {'Latin'}, 'jv': {'Latin'}, 'su': {'Latin'}, 'min': {'Latin'},
    'ban': {'Latin'}, 'bjn': {'Latin'}, 'pag': {'Latin'}, 'ilo': {'Latin'},
    'war': {'Latin'}, 'kea': {'Latin'}, 'pap': {'Latin'}, 'tpi': {'Latin'},
}

def _detect_script(ch):
    cp = ord(ch)
    for script, ranges in SCRIPT_RANGES.items():
        for start, end in ranges:
            if start <= cp <= end:
                return script
    return None

def is_source_lang_text(text, source_lang="en"):
    if not text or not isinstance(text, str):
        return False
    text = text.strip()
    if len(text.split()) > 3:
        return False
    detected_scripts = set()
    for ch in text:
        if unicodedata.category(ch).startswith('L'):
            s = _detect_script(ch)
            if s:
                detected_scripts.add(s)
    if not detected_scripts:
        return True
    expected = LANG_SCRIPTS.get(source_lang, {'Latin'})
    return detected_scripts.issubset(expected)

BACKUP_VOCAB_BY_LANG = {
    "en": [
        "morning", "evening", "family", "friend", "school", "teacher", "student", "classroom",
        "garden", "flower", "animal", "water", "river", "mountain", "forest", "weather",
        "summer", "winter", "spring", "autumn", "holiday", "birthday", "breakfast", "dinner",
        "kitchen", "window", "door", "table", "chair", "picture", "color", "music",
        "story", "letter", "number", "question", "answer", "example", "practice", "lesson",
        "country", "village", "market", "bridge", "station", "library", "hospital", "museum",
        "travel", "visit", "arrive", "return", "carry", "follow", "listen", "remember",
        "beautiful", "important", "different", "difficult", "wonderful", "careful", "together", "between",
        "always", "usually", "sometimes", "quickly", "slowly", "carefully", "certainly", "already",
        "enough", "another", "several", "perhaps", "almost", "during", "without", "against",
        "believe", "prepare", "discover", "explain", "imagine", "include", "provide", "suppose",
        "produce", "collect", "protect", "connect", "develop", "improve", "increase", "consider",
        "nature", "science", "culture", "future", "history", "language", "knowledge", "attention",
        "special", "possible", "popular", "similar", "simple", "strange", "useful", "serious",
        "decide", "depend", "divide", "enter", "happen", "invite", "notice", "promise",
        "suggest", "support", "achieve", "continue", "organize", "introduce", "celebrate", "communicate",
        "opinion", "decision", "direction", "information", "experience", "education", "condition", "position",
        "ancient", "modern", "correct", "exact", "proper", "necessary", "original", "traditional",
        "accept", "agree", "allow", "appear", "cause", "create", "expect", "force",
        "influence", "observe", "prefer", "receive", "require", "serve", "share", "spread",
    ],
    "zh": [
        "早上", "晚上", "家人", "朋友", "学校", "老师", "学生", "教室",
        "花园", "花朵", "动物", "喝水", "河流", "高山", "森林", "天气",
        "夏天", "冬天", "春天", "秋天", "假期", "生日", "早餐", "晚餐",
        "厨房", "窗户", "门", "桌子", "椅子", "图画", "颜色", "音乐",
        "故事", "信件", "数字", "问题", "回答", "例子", "练习", "课程",
        "国家", "村庄", "市场", "桥梁", "车站", "图书馆", "医院", "博物馆",
        "旅行", "参观", "到达", "回来", "携带", "跟随", "听", "记得",
        "美丽", "重要", "不同", "困难", "精彩", "小心", "一起", "之间",
        "总是", "通常", "有时", "快速", "慢慢", "仔细", "当然", "已经",
        "足够", "另一个", "几个", "也许", "几乎", "期间", "没有", "反对",
        "相信", "准备", "发现", "解释", "想象", "包括", "提供", "假设",
        "生产", "收集", "保护", "连接", "发展", "改善", "增加", "考虑",
        "自然", "科学", "文化", "未来", "历史", "语言", "知识", "注意",
        "特别", "可能", "流行", "相似", "简单", "奇怪", "有用", "认真",
        "决定", "依靠", "分开", "进入", "发生", "邀请", "注意", "承诺",
        "建议", "支持", "实现", "继续", "组织", "介绍", "庆祝", "交流",
        "意见", "决定", "方向", "信息", "经验", "教育", "条件", "位置",
        "古老", "现代", "正确", "精确", "适当", "必要", "原始", "传统",
        "接受", "同意", "允许", "出现", "原因", "创造", "期望", "力量",
        "影响", "观察", "偏好", "收到", "需要", "服务", "分享", "传播",
    ],
    "es": [
        "mañana", "tarde", "familia", "amigo", "escuela", "profesor", "estudiante", "aula",
        "jardín", "flor", "animal", "agua", "río", "montaña", "bosque", "clima",
        "verano", "invierno", "primavera", "otoño", "vacaciones", "cumpleaños", "desayuno", "cena",
        "cocina", "ventana", "puerta", "mesa", "silla", "imagen", "color", "música",
        "historia", "carta", "número", "pregunta", "respuesta", "ejemplo", "práctica", "lección",
        "país", "pueblo", "mercado", "puente", "estación", "biblioteca", "hospital", "museo",
        "viaje", "visita", "llegada", "regreso", "llevar", "seguir", "escuchar", "recordar",
        "hermoso", "importante", "diferente", "difícil", "maravilloso", "cuidadoso", "juntos", "entre",
        "siempre", "generalmente", "a veces", "rápido", "lento", "cuidadosamente", "ciertamente", "ya",
        "suficiente", "otro", "varios", "quizás", "casi", "durante", "sin", "contra",
        "creer", "preparar", "descubrir", "explicar", "imaginar", "incluir", "proporcionar", "suponer",
        "producir", "recolectar", "proteger", "conectar", "desarrollar", "mejorar", "aumentar", "considerar",
        "naturaleza", "ciencia", "cultura", "futuro", "historia", "idioma", "conocimiento", "atención",
        "especial", "posible", "popular", "similar", "simple", "extraño", "útil", "serio",
        "decidir", "depender", "dividir", "entrar", "pasar", "invitar", "notar", "prometer",
        "sugerir", "apoyar", "lograr", "continuar", "organizar", "presentar", "celebrar", "comunicar",
        "opinión", "decisión", "dirección", "información", "experiencia", "educación", "condición", "posición",
        "antiguo", "moderno", "correcto", "exacto", "apropiado", "necesario", "original", "tradicional",
        "aceptar", "acordar", "permitir", "aparecer", "causar", "crear", "esperar", "fuerza",
        "influencia", "observar", "preferir", "recibir", "requerir", "servir", "compartir", "extender",
    ],
    "de": [
        "Morgen", "Abend", "Familie", "Freund", "Schule", "Lehrer", "Schüler", "Klassenzimmer",
        "Garten", "Blume", "Tier", "Wasser", "Fluss", "Berg", "Wald", "Wetter",
        "Sommer", "Winter", "Frühling", "Herbst", "Urlaub", "Geburtstag", "Frühstück", "Abendessen",
        "Küche", "Fenster", "Tür", "Tisch", "Stuhl", "Bild", "Farbe", "Musik",
        "Geschichte", "Brief", "Zahl", "Frage", "Antwort", "Beispiel", "Übung", "Lektion",
        "Land", "Dorf", "Markt", "Brücke", "Bahnhof", "Bibliothek", "Krankenhaus", "Museum",
        "Reise", "Besuch", "Ankunft", "Rückkehr", "tragen", "folgen", "zuhören", "erinnern",
        "schön", "wichtig", "verschieden", "schwierig", "wunderbar", "vorsichtig", "zusammen", "zwischen",
        "immer", "gewöhnlich", "manchmal", "schnell", "langsam", "sorgfältig", "bestimmt", "schon",
        "genug", "anderer", "mehrere", "vielleicht", "fast", "während", "ohne", "gegen",
        "glauben", "vorbereiten", "entdecken", "erklären", "vorstellen", "einschließen", "bieten", "annehmen",
        "produzieren", "sammeln", "schützen", "verbinden", "entwickeln", "verbessern", "erhöhen", "bedenken",
        "Natur", "Wissenschaft", "Kultur", "Zukunft", "Geschichte", "Sprache", "Wissen", "Aufmerksamkeit",
        "besonders", "möglich", "beliebt", "ähnlich", "einfach", "seltsam", "nützlich", "ernst",
        "entscheiden", "abhängen", "teilen", "eintreten", "passieren", "einladen", "bemerken", "versprechen",
        "vorschlagen", "unterstützen", "erreichen", "fortsetzen", "organisieren", "vorstellen", "feiern", "kommunizieren",
        "Meinung", "Entscheidung", "Richtung", "Information", "Erfahrung", "Bildung", "Bedingung", "Position",
        "alt", "modern", "richtig", "genau", "passend", "notwendig", "ursprünglich", "traditionell",
        "akzeptieren", "zustimmen", "erlauben", "erscheinen", "verursachen", "erschaffen", "erwarten", "Kraft",
        "Einfluss", "beobachten", "bevorzugen", "empfangen", "benötigen", "dienen", "teilen", "verbreiten",
    ],
    "fr": [
        "matin", "soir", "famille", "ami", "école", "professeur", "étudiant", "salle",
        "jardin", "fleur", "animal", "eau", "rivière", "montagne", "forêt", "temps",
        "été", "hiver", "printemps", "automne", "vacances", "anniversaire", "petit-déjeuner", "dîner",
        "cuisine", "fenêtre", "porte", "table", "chaise", "image", "couleur", "musique",
        "histoire", "lettre", "nombre", "question", "réponse", "exemple", "exercice", "leçon",
        "pays", "village", "marché", "pont", "gare", "bibliothèque", "hôpital", "musée",
        "voyage", "visite", "arrivée", "retour", "porter", "suivre", "écouter", "rappeler",
        "beau", "important", "différent", "difficile", "merveilleux", "prudent", "ensemble", "entre",
        "toujours", "généralement", "parfois", "vite", "lentement", "soigneusement", "certainement", "déjà",
        "assez", "autre", "plusieurs", "peut-être", "presque", "pendant", "sans", "contre",
        "croire", "préparer", "découvrir", "expliquer", "imaginer", "inclure", "fournir", "supposer",
        "produire", "collecter", "protéger", "connecter", "développer", "améliorer", "augmenter", "considérer",
        "nature", "science", "culture", "avenir", "histoire", "langue", "connaissance", "attention",
        "spécial", "possible", "populaire", "similaire", "simple", "étrange", "utile", "sérieux",
        "décider", "dépendre", "diviser", "entrer", "arriver", "inviter", "remarquer", "promettre",
        "suggérer", "soutenir", "réaliser", "continuer", "organiser", "présenter", "célébrer", "communiquer",
        "opinion", "décision", "direction", "information", "expérience", "éducation", "condition", "position",
        "ancien", "moderne", "correct", "exact", "propre", "nécessaire", "original", "traditionnel",
        "accepter", "accepter", "permettre", "apparaître", "causer", "créer", "espérer", "force",
        "influence", "observer", "préférer", "recevoir", "exiger", "servir", "partager", "répandre",
    ],
    "ja": [
        "朝", "夕方", "家族", "友達", "学校", "先生", "学生", "教室",
        "庭", "花", "動物", "水", "川", "山", "森", "天気",
        "夏", "冬", "春", "秋", "休み", "誕生日", "朝食", "夕食",
        "台所", "窓", "扉", "机", "椅子", "絵", "色", "音楽",
        "物語", "手紙", "数字", "質問", "答え", "例", "練習", "授業",
        "国", "村", "市場", "橋", "駅", "図書館", "病院", "美術館",
        "旅行", "訪問", "到着", "帰り", "持つ", "従う", "聞く", "覚える",
        "美しい", "大切", "違う", "難しい", "素晴らしい", "慎重", "一緒", "間",
        "いつも", "普通", "時々", "速い", "遅い", "丁寧", "確実", "もう",
        "十分", "別の", "いくつか", "たぶん", "ほとんど", "間", "なし", "反対",
        "信じる", "準備", "発見", "説明", "想像", "含む", "提供", "仮定",
        "作る", "集める", "守る", "繋ぐ", "発展", "改善", "増やす", "考える",
        "自然", "科学", "文化", "未来", "歴史", "言葉", "知識", "注意",
        "特別", "可能", "人気", "似ている", "簡単", "変", "役立つ", "真剣",
        "決める", "頼る", "分ける", "入る", "起こる", "招待", "気づく", "約束",
        "提案", "応援", "達成", "続ける", "整理", "紹介", "祝う", "伝える",
        "意見", "決定", "方向", "情報", "経験", "教育", "条件", "位置",
        "古い", "現代", "正しい", "正確", "適切", "必要", "元の", "伝統的",
        "受け入れる", "同意", "許す", "現れる", "原因", "創造", "期待", "力",
        "影響", "観察", "好む", "受け取る", "必要", "仕える", "共有", "広がる",
    ],
    "ko": [
        "아침", "저녁", "가족", "친구", "학교", "선생님", "학생", "교실",
        "정원", "꽃", "동물", "물", "강", "산", "숲", "날씨",
        "여름", "겨울", "봄", "가을", "휴가", "생일", "아침식사", "저녁식사",
        "부엌", "창문", "문", "탁자", "의자", "그림", "색", "음악",
        "이야기", "편지", "숫자", "질문", "대답", "예", "연습", "수업",
        "나라", "마을", "시장", "다리", "역", "도서관", "병원", "박물관",
        "여행", "방문", "도착", "귀환", "가지다", "따르다", "듣다", "기억하다",
        "아름다운", "중요한", "다른", "어려운", "멋진", "조심스러운", "함께", "사이",
        "항상", "보통", "가끔", "빠른", "느린", "주의 깊은", "확실히", "이미",
        "충분한", "다른", "몇몇", "아마", "거의", "동안", "없이", "반대",
        "믿다", "준비하다", "발견하다", "설명하다", "상상하다", "포함하다", "제공하다", "가정하다",
        "생산하다", "수집하다", "보호하다", "연결하다", "발전하다", "개선하다", "증가하다", "고려하다",
        "자연", "과학", "문화", "미래", "역사", "언어", "지식", "주의",
        "특별한", "가능한", "인기 있는", "비슷한", "간단한", "이상한", "유용한", "진지한",
        "결정하다", "의존하다", "나누다", "들어가다", "일어나다", "초대하다", "알아차리다", "약속하다",
        "제안하다", "지지하다", "달성하다", "계속하다", "조직하다", "소개하다", "축하하다", "소통하다",
        "의견", "결정", "방향", "정보", "경험", "교육", "조건", "위치",
        "오래된", "현대", "올바른", "정확한", "적절한", "필요한", "원래의", "전통적인",
        "받아들이다", "동의하다", "허락하다", "나타나다", "원인", "창조하다", "기대하다", "힘",
        "영향", "관찰하다", "선호하다", "받다", "요구하다", "봉사하다", "공유하다", "퍼지다",
    ],
}

BACKUP_VOCAB = BACKUP_VOCAB_BY_LANG["en"]


NO_SPACE_LANGUAGES = frozenset({
    'zh', 'zh-TW', 'yue',
    'ja',
    'th', 'lo', 'km', 'my',
})

def _tokenize_by_space(text: str) -> List[str]:
    return [w for w in text.split() if w.strip()]

def _tokenize_by_char(text: str) -> List[str]:
    import re
    return [c for c in text if c.strip() and not re.match(r'^[^\w]+$', c, re.UNICODE)]


class TextProcessor:
    def __init__(self):
        pass

    def extract_words(self, text: str, language: str) -> List[str]:
        import re
        if language in NO_SPACE_LANGUAGES:
            return _tokenize_by_char(text)
        return _tokenize_by_space(text)

    def extract_words_from_sentences(self, sentences: List[str], language: str) -> List[str]:
        """从句子列表中提取单词并全局去重"""
        all_words = []
        
        # 从每个句子中提取单词
        for sentence in sentences:
            sentence_words = self.extract_words(sentence, language)
            all_words.extend(sentence_words)
        
        # 全局去重
        seen = set()
        unique_words = []
        for word in all_words:
            if word not in seen:
                seen.add(word)
                unique_words.append(word)
        
        return unique_words

    def chunk_words(self, words: List[str], chunk_size: int = 10) -> List[List[str]]:
        chunks = []
        for i in range(0, len(words), chunk_size):
            chunks.append(words[i:i + chunk_size])
        return chunks

    def split_sentences(self, text: str) -> List[str]:
        sentence_endings = {
            '.', '!', '?',
            '。', '！', '？',
            '…', '⋯',
            '।', '॥',
            '။', ' ။',
            '።', '፣',
            '។', '៕',
            'ດ',
            '᪩', '᪪',
            '⳹', '⳾',
            '𐩖', '𐩗',
            '꘎', '꛳',
            ';', '；',
        }
        sentences = []
        current_sentence = ""

        i = 0
        while i < len(text):
            char = text[i]

            if char == '\n':
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
                i += 1
                continue

            current_sentence += char

            if char in sentence_endings:
                j = i + 1
                while j < len(text) and text[j] in sentence_endings:
                    current_sentence += text[j]
                    j += 1
                if j < len(text) and text[j] == ' ':
                    current_sentence += text[j]
                    j += 1
                i = j

                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                current_sentence = ""
            else:
                i += 1

        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        sentences = [s for s in sentences if s.strip()]

        return [s for s in sentences if s.strip()]

    def process_word_variants(self, word_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理单词变体，确保变体前面有类型标注"""
        processed_variants = []
        for variant in word_data:
            if 'type' not in variant and 'word' in variant:
                # 简单的类型推断（实际应用中可能需要更复杂的逻辑）
                variant['type'] = '未知'
            processed_variants.append(variant)
        return processed_variants

    def resolve_phonetic_conflicts(self, phonetics: List[str]) -> str:
        """解决音标冲突，选择出现最多的音标"""
        if not phonetics:
            return ""
        
        # 统计每个音标的出现次数
        phonetic_counts = {}
        for phonetic in phonetics:
            if phonetic:
                phonetic_counts[phonetic] = phonetic_counts.get(phonetic, 0) + 1
        
        # 按出现次数排序
        sorted_phonetics = sorted(phonetic_counts.items(), key=lambda x: x[1], reverse=True)
        
        # 返回出现次数最多的音标，如果次数相同则返回第一个
        return sorted_phonetics[0][0]

    async def process_translation(self, text: str, source_lang: str, target_lang: str, llm_api, context_sentences: dict = None):
        result = await llm_api.process_text_with_dictionary(text, source_lang, target_lang, context_sentences)
        
        # 简单处理，保留LLM生成的自然结果
        if isinstance(result, dict):
            # 保留original字段，因为它可能包含翻译后的文本
            
            # 简单过滤：只过滤掉纯标点符号的token
            if 'translation' in result:
                filtered_translation = []
                for token in result['translation']:
                    if isinstance(token, dict) and 'text' in token:
                        token_text = token['text'].strip()
                        if not token_text or is_punctuation_only(token_text):
                            continue
                        cleaned = strip_edge_punctuation(token_text)
                        if cleaned and cleaned != token_text:
                            token['text'] = cleaned
                        if cleaned:
                            filtered_translation.append(token)
                result['translation'] = filtered_translation
        
        # 返回处理后的结果，保留LLM生成的自然翻译
        return result
    
    def _normalize_text_for_compare(self, text):
        import re
        return re.sub(r'[\s\u3000]+', '', re.sub(r'[^\w\u00C0-\u024F\u0400-\u052F\u0370-\u03FF\u0600-\u06FF\u0900-\u0D7F\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF\u1000-\u109F\u10A0-\u10FF\u1100-\u11FF]', '', text)).lower()

    def validate_and_complete_translation(self, sentence: str, translation_result: dict, source_lang: str) -> dict:
        if not isinstance(translation_result, dict) or 'translation' not in translation_result:
            return translation_result
        
        existing_tokens = []
        if 'translation' in translation_result:
            for token in translation_result['translation']:
                if isinstance(token, dict) and 'text' in token:
                    token_text = token['text']
                    if is_punctuation_only(token_text):
                        continue
                    cleaned = strip_edge_punctuation(token_text)
                    if cleaned != token_text:
                        token['text'] = cleaned
                    if cleaned:
                        existing_tokens.append(token)
        
        if not existing_tokens:
            original_words = self.tokenize_sentence(sentence, language=source_lang)
            cleaned_original = []
            for w in original_words:
                if is_punctuation_only(w):
                    continue
                cw = strip_edge_punctuation(w)
                if cw:
                    cleaned_original.append(cw)
            translation_result['translation'] = [
                {'text': w, 'phonetic': '', 'morphology': '', 'meaning': ''}
                for w in cleaned_original
            ]
            return translation_result
        
        sentence_normalized = self._normalize_text_for_compare(sentence)
        tokens_normalized = self._normalize_text_for_compare(''.join(t['text'] for t in existing_tokens))
        
        if source_lang in NO_SPACE_LANGUAGES:
            if tokens_normalized == sentence_normalized:
                deduped = self._dedup_tokens(existing_tokens, sentence_normalized)
                translation_result['translation'] = deduped
                return translation_result
            
            if tokens_normalized and sentence_normalized.startswith(tokens_normalized):
                remaining = sentence[len(''.join(t['text'] for t in existing_tokens)):]
                remaining = remaining.strip()
                if remaining:
                    import re
                    remaining_clean = re.sub(r'[^\w]+', '', remaining)
                    if remaining_clean:
                        existing_tokens.append({
                            'text': remaining_clean,
                            'phonetic': '',
                            'morphology': '',
                            'meaning': ''
                        })
                translation_result['translation'] = existing_tokens
                return translation_result
            
            if len(tokens_normalized) > len(sentence_normalized):
                deduped = self._dedup_tokens(existing_tokens, sentence_normalized)
                translation_result['translation'] = deduped
                return translation_result
            
            translation_result['translation'] = existing_tokens
            return translation_result
        
        original_words = self.tokenize_sentence(sentence, language=source_lang)
        cleaned_original = []
        for w in original_words:
            if is_punctuation_only(w):
                continue
            cw = strip_edge_punctuation(w)
            if cw:
                cleaned_original.append(cw)
        original_words = cleaned_original
        
        original_word_counts = {}
        for w in original_words:
            key = w.lower()
            original_word_counts[key] = original_word_counts.get(key, 0) + 1
        
        deduped_tokens = []
        token_seen_counts = {}
        for token in existing_tokens:
            key = token['text'].lower()
            allowed = original_word_counts.get(key, 1)
            current = token_seen_counts.get(key, 0)
            if current < allowed:
                token_seen_counts[key] = current + 1
                deduped_tokens.append(token)
            else:
                for prev in deduped_tokens:
                    if prev['text'].lower() == key:
                        for field in ('phonetic', 'morphology', 'meaning'):
                            if not prev.get(field) and token.get(field):
                                prev[field] = token[field]
                        break
        existing_tokens = deduped_tokens
        
        existing_text_joined = ''.join(t['text'] for t in existing_tokens).lower()
        original_joined = ''.join(original_words).lower()
        
        if existing_text_joined == original_joined and len(existing_tokens) == len(original_words):
            translation_result['translation'] = existing_tokens
            return translation_result
        
        if existing_text_joined == original_joined and len(existing_tokens) != len(original_words):
            merged = []
            orig_idx = 0
            tok_idx = 0
            while orig_idx < len(original_words) and tok_idx < len(existing_tokens):
                orig = original_words[orig_idx]
                combined = ''
                combined_tokens = []
                while tok_idx < len(existing_tokens):
                    combined += existing_tokens[tok_idx]['text']
                    combined_tokens.append(existing_tokens[tok_idx])
                    if combined.lower() == orig.lower():
                        if len(combined_tokens) == 1:
                            merged.append(combined_tokens[0])
                        else:
                            merged.append({
                                'text': orig,
                                'phonetic': combined_tokens[0].get('phonetic', ''),
                                'morphology': '；'.join(t.get('morphology', '') for t in combined_tokens if t.get('morphology')),
                                'meaning': '；'.join(t.get('meaning', '') or t.get('context_meaning', '') or t.get('translation', '') for t in combined_tokens if t.get('meaning') or t.get('context_meaning') or t.get('translation')),
                            })
                        tok_idx += 1
                        break
                    tok_idx += 1
                orig_idx += 1
            translation_result['translation'] = merged
            return translation_result
        
        completed_translation = []
        used_existing = set()
        covered_original_indices = set()
        
        # Pre-compute: for multi-word tokens, find which consecutive original words they cover
        token_to_orig_range = {}  # token_index -> (start_orig_idx, end_orig_idx)
        for i, token in enumerate(existing_tokens):
            token_text = token['text']
            token_words = token_text.split()
            if len(token_words) > 1:
                token_lower_words = [w.lower() for w in token_words]
                for start_idx in range(len(original_words)):
                    end_idx = start_idx + len(token_words)
                    if end_idx > len(original_words):
                        break
                    orig_slice = [w.lower() for w in original_words[start_idx:end_idx]]
                    if orig_slice == token_lower_words:
                        token_to_orig_range[i] = (start_idx, end_idx)
                        break
        
        orig_idx = 0
        while orig_idx < len(original_words):
            if orig_idx in covered_original_indices:
                orig_idx += 1
                continue
            
            orig_word = original_words[orig_idx]
            orig_lower = orig_word.lower()
            found = False
            
            # First, try to find a multi-word token that starts at this position
            for i, (start, end) in token_to_orig_range.items():
                if i in used_existing:
                    continue
                if start == orig_idx:
                    completed_translation.append(existing_tokens[i])
                    used_existing.add(i)
                    for j in range(start, end):
                        covered_original_indices.add(j)
                    found = True
                    orig_idx = end
                    break
            
            if found:
                continue
            
            # Then try single-word exact match
            for i, token in enumerate(existing_tokens):
                if i in used_existing:
                    continue
                token_lower = token['text'].lower()
                if token_lower == orig_lower:
                    completed_translation.append(token)
                    used_existing.add(i)
                    found = True
                    break
            if not found:
                for i, token in enumerate(existing_tokens):
                    if i in used_existing:
                        continue
                    token_lower = token['text'].lower()
                    if token_lower == orig_lower.replace('-', ' '):
                        completed_translation.append(token)
                        used_existing.add(i)
                        found = True
                        break
                    if token_lower.replace('-', ' ') == orig_lower:
                        completed_translation.append({**token, 'text': orig_word})
                        used_existing.add(i)
                        found = True
                        break
            if not found:
                completed_translation.append({
                    'text': orig_word,
                    'phonetic': '',
                    'morphology': '',
                    'meaning': ''
                })
            
            orig_idx += 1
        
        translation_result['translation'] = completed_translation
        return translation_result
    
    def _dedup_tokens(self, tokens, sentence_normalized):
        deduped = []
        seen_keys = {}
        for token in tokens:
            key = token['text'].lower()
            if key not in seen_keys:
                seen_keys[key] = token
                deduped.append(token)
            else:
                prev = seen_keys[key]
                for field in ('phonetic', 'morphology', 'meaning'):
                    if not prev.get(field) and token.get(field):
                        prev[field] = token[field]
        
        deduped_normalized = self._normalize_text_for_compare(''.join(t['text'] for t in deduped))
        if deduped_normalized == sentence_normalized:
            return deduped
        
        return tokens

    def tokenize_sentence(self, sentence: str, language: str = "en") -> List[str]:
        if language in NO_SPACE_LANGUAGES:
            return _tokenize_by_char(sentence)
        return _tokenize_by_space(sentence)
    
    def generate_masked_sentence(self, sentence: str, vocab: List[Dict], translation_tokens: List[str] = None, all_sentences: List[Dict] = None, mask_seed: int = None, source_lang: str = "en", mask_version: int = 0, max_distractors: int = 2) -> Dict[str, Any]:
        if translation_tokens:
            words = translation_tokens
        else:
            words = self.tokenize_sentence(sentence, language=source_lang)
        
        word_count = len(words)
        
        num_masks = max(1, word_count // 8)
        
        if num_masks > word_count // 2:
            num_masks = max(1, word_count // 2)
        
        import random
        if mask_seed is not None:
            random.seed(mask_seed)
        else:
            random.seed(hash(sentence))
        
        all_candidates = list(range(word_count))
        random.shuffle(all_candidates)
        
        if translation_tokens:
            token_list = translation_tokens
        else:
            token_list = self.tokenize_sentence(sentence, language=source_lang)
        
        mask_groups = []
        remaining = list(all_candidates)
        
        while remaining and len(mask_groups) < 3:
            group = []
            used = set()
            used_words_in_group = set()
            for idx in remaining:
                if len(group) >= num_masks:
                    break
                too_close = any(abs(idx - e) <= 2 for e in used)
                if too_close:
                    continue
                word_at_idx = token_list[idx].lower()
                for ch in word_at_idx:
                    if ch in PUNCTUATION_CHARS or unicodedata.category(ch).startswith('P'):
                        word_at_idx = word_at_idx.replace(ch, '')
                word_at_idx = word_at_idx.strip() if idx < len(token_list) else ''
                if word_at_idx in used_words_in_group:
                    continue
                group.append(idx)
                used.add(idx)
                if word_at_idx:
                    used_words_in_group.add(word_at_idx)
            if group:
                mask_groups.append(sorted(group))
            remaining = [r for r in remaining if r not in used]
        
        while len(mask_groups) < 3:
            if mask_groups:
                mask_groups.append(mask_groups[len(mask_groups) % len(mask_groups)])
            else:
                mask_groups.append([0])
        
        mask_indices = mask_groups[mask_version % len(mask_groups)]
        
        # 构建蒙版后的句子 - 使用LLM生成的tokens
        masked_tokens = []
        answer_words = []
        
        if translation_tokens:
            for i, token in enumerate(translation_tokens):
                if i in mask_indices:
                    masked_tokens.append("___")
                    answer_words.append(token)
                else:
                    masked_tokens.append(token)
        else:
            import re
            tokens_with_punc = re.findall(r"\b\w+(?:'\w+)?\b|[^\w\s]", sentence)
            current_word_idx = 0
            for token in tokens_with_punc:
                if re.match(r"\b\w+(?:'\w+)?\b", token) and current_word_idx < len(words):
                    if current_word_idx in mask_indices:
                        masked_tokens.append("___")
                        answer_words.append(token)
                    else:
                        masked_tokens.append(token)
                    current_word_idx += 1
                else:
                    masked_tokens.append(token)
        
        # 生成选项：正确答案 + 干扰项
        options = answer_words.copy()
        distractors = []
        answer_lower = [w.lower() for w in answer_words]
        
        current_sentence_words_lower = set()
        if translation_tokens:
            current_sentence_words_lower = {w.lower() for w in translation_tokens}
        else:
            current_sentence_words_lower = {w.lower() for w in self.tokenize_sentence(sentence, language=source_lang)}
        
        exclude_lower = set(answer_lower)
        
        if all_sentences:
            all_distractor_candidates = []
            all_distractor_set = set()
            for sent_data in all_sentences:
                if "sentence" in sent_data and sent_data["sentence"] != sentence:
                    if "translation_result" in sent_data and "translation" in sent_data["translation_result"]:
                        for token in sent_data["translation_result"]["translation"]:
                            if isinstance(token, dict) and "text" in token:
                                token_text = token["text"]
                                if token_text.lower() not in exclude_lower and token_text.lower() not in all_distractor_set:
                                    all_distractor_candidates.append(token_text)
                                    all_distractor_set.add(token_text.lower())
            random.shuffle(all_distractor_candidates)
            distractors = all_distractor_candidates[:max_distractors]
        
        if len(distractors) < max_distractors:
            vocab_words = [v["word"] for v in vocab]
            random.shuffle(vocab_words)
            for vw in vocab_words:
                if vw.lower() not in exclude_lower and vw not in distractors and len(distractors) < max_distractors:
                    distractors.append(vw)
        
        if len(distractors) < max_distractors:
            fallback_needed = max_distractors - len(distractors)
            fallback_distractors = self.get_fallback_distractors(fallback_needed, list(exclude_lower) + distractors, source_lang)
            distractors.extend(fallback_distractors)
        
        random.shuffle(distractors)
        options += distractors[:max_distractors]
        
        # 打乱所有选项
        random.shuffle(options)
        
        # 构建蒙版句子，保留原始句子的标点
        if translation_tokens:
            import re as _re
            token_positions = []
            search_start = 0
            for token in translation_tokens:
                escaped = _re.escape(token)
                m = _re.search(escaped, sentence[search_start:], _re.IGNORECASE)
                if m:
                    token_positions.append((search_start + m.start(), search_start + m.end(), token))
                    search_start = search_start + m.end()
                else:
                    token_positions.append(None)
            
            result_parts = []
            last_end = 0
            for i, pos_info in enumerate(token_positions):
                if pos_info is None:
                    continue
                start, end, token = pos_info
                if start > last_end:
                    result_parts.append(sentence[last_end:start])
                if i in mask_indices:
                    result_parts.append("___")
                else:
                    result_parts.append(token)
                last_end = end
            if last_end < len(sentence):
                result_parts.append(sentence[last_end:])
            masked_sentence = "".join(result_parts)
        else:
            masked_sentence = "".join(
                [
                    " " + token if token not in [".", ",", "!", "?", ":", ";", ")"] and i > 0 else token 
                    for i, token in enumerate(masked_tokens)
                ]
            )
        
        return {
            "original_sentence": sentence,
            "masked_sentence": masked_sentence,
            "answer_words": answer_words,
            "mask_indices": mask_indices,
            "options": options,
            "word_count": word_count
        }

    def generate_multiple_masked_sentences(self, sentence: str, vocab: List[Dict], translation_tokens: List[str] = None, all_sentences: List[Dict] = None, num_versions: int = 3) -> List[Dict[str, Any]]:
        results = []
        base_seed = hash(sentence)
        for i in range(num_versions):
            seed = base_seed + i + 1
            masked = self.generate_masked_sentence(
                sentence, vocab, translation_tokens, all_sentences, mask_seed=seed
            )
            if masked:
                masked["mask_version"] = i
                results.append(masked)
        return results

    def generate_interleaved_exercise_order(self, num_sentences: int, masks_per_sentence: int = 3, seed: int = 42, exercises_per_sentence_list: List[int] = None) -> List[List[int]]:
        import random
        random.seed(seed)
        
        if exercises_per_sentence_list is None:
            exercises_per_sentence_list = [masks_per_sentence + 1] * num_sentences
        
        next_type = [0] * num_sentences
        result = []
        remaining = sum(exercises_per_sentence_list)
        last_sent = -1
        
        while remaining > 0:
            available = [i for i in range(num_sentences) if next_type[i] < exercises_per_sentence_list[i]]
            if len(available) > 1 and last_sent in available:
                preferred = [i for i in available if i != last_sent]
                sent_idx = random.choice(preferred)
            else:
                sent_idx = random.choice(available)
            result.append([sent_idx, next_type[sent_idx]])
            next_type[sent_idx] += 1
            last_sent = sent_idx
            remaining -= 1
        
        return result

    def group_sentences_into_units(self, sentences: List[str], unit_size: int = 8) -> List[List[str]]:
        units = []
        for i in range(0, len(sentences), unit_size):
            units.append(sentences[i:i+unit_size])
        return units

    def get_fallback_distractors(self, count: int, exclude_words: List[str] = None, source_lang: str = "en") -> List[str]:
        if exclude_words is None:
            exclude_words = []
        
        exclude_lower = [w.lower() for w in exclude_words]
        distractors = []
        
        import random
        vocab_list = BACKUP_VOCAB_BY_LANG.get(source_lang, BACKUP_VOCAB_BY_LANG["en"])
        shuffled = list(vocab_list)
        random.shuffle(shuffled)
        
        for word in shuffled:
            if word.lower() not in exclude_lower and len(distractors) < count:
                distractors.append(word)
        
        return distractors


