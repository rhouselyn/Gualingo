import axios from 'axios';

// 配置axios超时时间为10分钟
axios.defaults.timeout = 600000;

// base url
const baseUrl = '';

export const api = {
  baseUrl: baseUrl,
  
  // 处理文本
  processText: async (text, sourceLang, targetLang, mode = 'direct') => {
    const response = await axios.post(`${baseUrl}/api/process-text`, {
      text: text.trim(),
      source_language: sourceLang,
      target_language: targetLang,
      mode: mode,
    });
    return response.data;
  },

  detectLanguage: async (text) => {
    const response = await axios.post(`${baseUrl}/api/detect-language`, {
      text: text.trim(),
    });
    return response.data;
  },

  // 获取处理状态
  getStatus: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/status/${fileId}`);
    return response.data;
  },

  // 获取词汇表
  getVocab: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/vocab/${fileId}`);
    return response.data;
  },

  getFileLanguages: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/file-languages/${fileId}`);
    return response.data;
  },

  // 获取句子
  getSentences: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/sentences/${fileId}`);
    return response.data;
  },

  // 获取随机单词
  getRandomWord: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/random-word`);
    return response.data;
  },

  // 获取下一个单词
  nextWord: async (fileId) => {
    const response = await axios.post(`${baseUrl}/api/learn/${fileId}/next-word`);
    return response.data;
  },

  // 获取单词详情
  getWordDetails: async (fileId, word) => {
    const response = await axios.get(`${baseUrl}/api/word/${fileId}/${word}`);
    return response.data;
  },

  // 获取学习进度和分组信息
  getLearningProgress: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/progress`);
    return response.data;
  },

  // 获取指定单元的单词
  getUnitWords: async (fileId, unitId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/unit/${unitId}`);
    return response.data;
  },

  // 检查已学单词能否组成新句子
  checkCoverage: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/check-coverage`);
    return response.data;
  },

  // 生成句子翻译题
  generateSentenceQuiz: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/sentence-quiz`);
    return response.data;
  },

  // 设置学习进度
  setProgress: async (fileId, index) => {
    const response = await axios.post(`${baseUrl}/api/learn/${fileId}/set-progress`, {
      index: index,
    });
    return response.data;
  },

  // --- 新的学习阶段 API ---
  // 获取所有阶段列表
  getPhases: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/${fileId}/phases`);
    return response.data;
  },
  
  // 获取指定阶段的单元列表
  getPhaseUnits: async (fileId, phaseNumber) => {
    const response = await axios.get(`${baseUrl}/api/${fileId}/phase/${phaseNumber}/units`);
    return response.data;
  },
  
  // 获取指定单元的当前练习
  getPhaseUnitExercise: async (fileId, phaseNumber, unitId) => {
    const response = await axios.get(`${baseUrl}/api/${fileId}/phase/${phaseNumber}/unit/${unitId}`);
    return response.data;
  },
  
  // 进入下一个练习
  nextPhaseExercise: async (fileId, phaseNumber, unitId) => {
    const response = await axios.post(`${baseUrl}/api/${fileId}/phase/${phaseNumber}/unit/${unitId}/next`);
    return response.data;
  },
  
  // 标记单元为完成
  completePhaseUnit: async (fileId, phaseNumber, unitId) => {
    const response = await axios.post(`${baseUrl}/api/${fileId}/phase/${phaseNumber}/unit/${unitId}/complete`);
    return response.data;
  },
  
  // 设置阶段进度
  setPhaseProgress: async (fileId, phaseNumber, unitId = 0, exerciseIndex = 0) => {
    const response = await axios.post(`${baseUrl}/api/${fileId}/phase/${phaseNumber}/set-progress`, {
      unit_id: unitId,
      exercise_index: exerciseIndex,
    });
    return response.data;
  },

  getHistory: async () => {
    const response = await axios.get(`${baseUrl}/api/history`);
    return response.data;
  },

  deleteHistory: async (fileId) => {
    const response = await axios.delete(`${baseUrl}/api/history/${fileId}`);
    return response.data;
  },

  renameHistory: async (fileId, title) => {
    const response = await axios.put(`${baseUrl}/api/history/${fileId}`, { title });
    return response.data;
  },

  getUnitStars: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/unit-stars`);
    return response.data;
  },

  saveUnitStars: async (fileId, stars) => {
    const response = await axios.post(`${baseUrl}/api/learn/${fileId}/unit-stars`, { stars });
    return response.data;
  },

  getWordList: async (sourceLang, targetLang) => {
    const params = {};
    if (sourceLang) params.source_lang = sourceLang;
    if (targetLang) params.target_lang = targetLang;
    const response = await axios.get(`${baseUrl}/api/word-list`, { params });
    return response.data;
  },

  getWordDetail: async (word, sourceLang, targetLang) => {
    const params = { word, source_lang: sourceLang };
    if (targetLang) params.target_lang = targetLang;
    const response = await axios.get(`${baseUrl}/api/word-detail`, { params });
    return response.data;
  },

  getUserPreferences: async () => {
    const response = await axios.get(`${baseUrl}/api/user-preferences`)
    return response.data
  },

  saveUserPreferences: async (prefs) => {
    const response = await axios.post(`${baseUrl}/api/user-preferences`, prefs)
    return response.data
  },

  startWordGen: async (fileId) => {
    await axios.post(`${baseUrl}/api/learn/${fileId}/start-word-gen`)
  },

  getWordGenProgress: async (fileId) => {
    const response = await axios.get(`${baseUrl}/api/learn/${fileId}/word-gen-progress`)
    return response.data
  },

  stopWordGen: async (fileId) => {
    await axios.post(`${baseUrl}/api/learn/${fileId}/stop-word-gen`)
  },

  priorityWordGen: async (fileId, word) => {
    await axios.post(`${baseUrl}/api/learn/${fileId}/priority-word-gen`, { word })
  },

  regenerateWord: async (fileId, word) => {
    await axios.post(`${baseUrl}/api/learn/${fileId}/priority-word-gen`, { word, force: true })
  },

  regenerateWordDetail: async (word, sourceLang, targetLang) => {
    const response = await axios.post(`${baseUrl}/api/word-detail/regenerate`, { word, source_lang: sourceLang, target_lang: targetLang || 'en' })
    return response.data
  },

  regenerateWordDetailByFile: async (fileId, word) => {
    const response = await axios.post(`${baseUrl}/api/word/${fileId}/${word}/regenerate`)
    return response.data
  },

  translateText: async (text, sourceLang, targetLang) => {
    const response = await axios.post(`${baseUrl}/api/translate-text`, {
      text: text.trim(),
      source_language: sourceLang,
      target_language: targetLang,
    });
    return response.data;
  },

  generateText: async (prompt, sourceLang, targetLang) => {
    const response = await axios.post(`${baseUrl}/api/generate-text`, {
      prompt: prompt.trim(),
      source_language: sourceLang,
      target_language: targetLang,
    });
    return response.data;
  },

  // Translate UI strings
  translateUI: async (langCode) => {
    const response = await axios.get(`${baseUrl}/api/translate_ui/${langCode}`);
    return response.data;
  },

  toggleFavorite: async (word, sourceLang) => {
    const response = await axios.post(`${baseUrl}/api/favorites/toggle`, { word, source_lang: sourceLang });
    return response.data;
  },

  getFavorites: async (sourceLang) => {
    const params = {};
    if (sourceLang) params.source_lang = sourceLang;
    const response = await axios.get(`${baseUrl}/api/favorites`, { params });
    return response.data;
  },

  checkFavorite: async (word, sourceLang) => {
    const response = await axios.get(`${baseUrl}/api/favorites/check`, { word, source_lang: sourceLang });
    return response.data;
  },

  checkForUpdates: async () => {
    const response = await axios.get(`${baseUrl}/api/version-check`);
    return response.data;
  },

  triggerAutoUpdate: async () => {
    const response = await axios.post(`${baseUrl}/api/auto-update`);
    return response.data;
  }
};