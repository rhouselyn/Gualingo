import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, ArrowLeft, Settings, Loader2 } from 'lucide-react'
import { api } from './utils/api'
import { translations } from './utils/translations'
import { warmupSpeech } from './utils/speech'
import ConfirmDialog from './components/ConfirmDialog'
import AlertDialog from './components/AlertDialog'

import InputStep from './components/InputStep'
import DictionaryStep from './components/DictionaryStep'
import LearningStep from './components/LearningStep'
import ProgressStep from './components/ProgressStep'
import SentenceQuizStep from './components/SentenceQuizStep'
import ListeningQuizStep from './components/ListeningQuizStep'
import PhaseSelectorStep from './components/PhaseSelectorStep'
import PhaseProgressStep from './components/PhaseProgressStep'
import MaskedSentenceExerciseStep from './components/MaskedSentenceExerciseStep'
import TranslationReconstructionStep from './components/TranslationReconstructionStep'
import AllUnitsStep from './components/AllUnitsStep'
import UnitCompleteStep from './components/UnitCompleteStep'
import VocabListStep from './components/VocabListStep'
import HistorySidebar from './components/HistorySidebar'
import WordListPanel from './components/WordListPanel'
import SettingsModal from './components/SettingsModal'

function FrogLogo({ size = 40 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <ellipse cx="50" cy="58" rx="38" ry="32" fill="#B5AE8E" />
      <ellipse cx="50" cy="55" rx="34" ry="28" fill="#D8D4BF" />
      <circle cx="34" cy="38" r="16" fill="#B5AE8E" />
      <circle cx="66" cy="38" r="16" fill="#B5AE8E" />
      <circle cx="34" cy="38" r="13" fill="#fff" />
      <circle cx="66" cy="38" r="13" fill="#fff" />
      <circle cx="36" cy="37" r="6" fill="#524D3C" />
      <circle cx="68" cy="37" r="6" fill="#524D3C" />
      <circle cx="38" cy="35" r="2" fill="#fff" />
      <circle cx="70" cy="35" r="2" fill="#fff" />
      <ellipse cx="50" cy="62" rx="18" ry="8" fill="#E8C985" />
      <path d="M38 60 Q50 70 62 60" stroke="#524D3C" strokeWidth="2" fill="none" strokeLinecap="round" />
    </svg>
  )
}

function App() {
  const [step, setStep] = useState('input')
  const [text, setText] = useState('')
  const [sourceLang, setSourceLang] = useState('auto')
  const [targetLang, setTargetLang] = useState('zh')
  const [uiLang, setUiLang] = useState('zh')
  const [customTranslations, setCustomTranslations] = useState({})
  const [translatingUI, setTranslatingUI] = useState(false)
  const [loadedLangs, setLoadedLangs] = useState(new Set())
  const [pageSize, setPageSize] = useState(50)
  const [loading, setLoading] = useState(false)
  const [fileId, setFileId] = useState(null)
  const [originalText, setOriginalText] = useState('')
  const [vocab, setVocab] = useState([])
  const [displayVocab, setDisplayVocab] = useState([])
  const [sortOrder, setSortOrder] = useState('asc') // 'asc' 或 'desc'
  const [sentenceTranslations, setSentenceTranslations] = useState([])
  const [selectedWord, setSelectedWord] = useState(null)
  const [selectedSentence, setSelectedSentence] = useState(null)
  const [progress, setProgress] = useState(0)
  const [processingInfo, setProcessingInfo] = useState(null)
  const [currentFileId, setCurrentFileId] = useState(null)
  const [skipPolling, setSkipPolling] = useState(false)
  const [learningData, setLearningData] = useState(null)
  const [showWordCard, setShowWordCard] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [selectedOption, setSelectedOption] = useState(null)
  const [isCorrect, setIsCorrect] = useState(null)
  const [units, setUnits] = useState([])
  const [currentUnit, setCurrentUnit] = useState(0)
  const [totalUnits, setTotalUnits] = useState(0)
  const [allUnitsCompleted, setAllUnitsCompleted] = useState(false)
  const [quizData, setQuizData] = useState(null)
  const [listeningQuizData, setListeningQuizData] = useState(null)
  const [learningMode, setLearningMode] = useState('word')
  const [unitErrorCount, setUnitErrorCount] = useState(0)
  const [wrongItems, setWrongItems] = useState([])
  const [reviewMode, setReviewMode] = useState(false)
  const [reviewIndex, setReviewIndex] = useState(0)
  const [reviewRound, setReviewRound] = useState(0)
  
  // New states for phases
  const [phases, setPhases] = useState([])
  const [currentPhase, setCurrentPhase] = useState(null)
  const [phaseUnits, setPhaseUnits] = useState([])
  const [currentPhaseUnit, setCurrentPhaseUnit] = useState(0)
  const [currentExerciseData, setCurrentExerciseData] = useState(null)
  const [exerciseType, setExerciseType] = useState(null)
  // New state for all units
  const [phase1Units, setPhase1Units] = useState([])
  const [phase2Units, setPhase2Units] = useState([])
  const [currentPhase1Unit, setCurrentPhase1Unit] = useState(0)
  const [currentPhase2Unit, setCurrentPhase2Unit] = useState(0)
  const [unitEndIndex, setUnitEndIndex] = useState(null)
  const [completedUnitId, setCompletedUnitId] = useState(null)
  const [completedPhase, setCompletedPhase] = useState(1)
  const [unitStarCounts, setUnitStarCounts] = useState({})
  const unitErrorCountRef = useRef(0)
  const isFetchingNextRef = useRef(false)
  const [skipListening, setSkipListening] = useState(false)
  const [historyRefresh, setHistoryRefresh] = useState(0)
  const [onlyNewWords, setOnlyNewWords] = useState(false)
  const [generatingUnits, setGeneratingUnits] = useState(new Set())
  const [lastActiveTab, setLastActiveTab] = useState(0)
  const [recentLanguages, setRecentLanguages] = useState([])
  const [wordListLang, setWordListLang] = useState(null)
  const [favoriteLang, setFavoriteLang] = useState(null)
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false, onConfirm: null })
  const [alertDialog, setAlertDialog] = useState({ open: false, title: '', message: '' })

  const showAlert = useCallback((message, title) => {
    setAlertDialog({ open: true, title: title || '', message })
  }, [])
  const [inputMode, setInputMode] = useState('direct')
  const [preprocessStatus, setPreprocessStatus] = useState(null)
  const [showVocabList, setShowVocabList] = useState(false)
  const [fileTitle, setFileTitle] = useState('')
  const [detectedLang, setDetectedLang] = useState(null)
  const learningContainerRef = useRef(null)
  const dictStateRef = useRef({ vocabPage: 1, sentencePage: 1, globalVocabPage: 1, vocabScrollPos: 0, sentenceTranslationScrollPos: 0, sentenceOriginalScrollPos: 0, globalVocabScrollPos: 0, vocabDisplayMode: 0, sentenceDisplayMode: 0, showOriginal: false, showGlobalVocab: false, vocabSearch: '', sentenceSearch: '' })
  const wrongItemsRef = useRef([])
  const reviewIndexRef = useRef(0)

  const learningSteps = ['dictionary', 'all-units', 'learning', 'sentence-quiz', 'listening-quiz', 'progress', 'phase-progress', 'phase-exercise', 'unit-complete']

  useEffect(() => {
    warmupSpeech()
    api.getUserPreferences().then(prefs => {
      if (prefs.target_lang) setTargetLang(prefs.target_lang)
      if (prefs.ui_lang) setUiLang(prefs.ui_lang)
      else if (prefs.target_lang) setUiLang(prefs.target_lang)
      if (prefs.skip_listening !== undefined) setSkipListening(prefs.skip_listening)
      if (prefs.only_new_words !== undefined) setOnlyNewWords(prefs.only_new_words)
      if (prefs.recent_languages) setRecentLanguages(prefs.recent_languages)
      if (prefs.page_size) setPageSize(prefs.page_size)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!currentFileId) return
    if (learningSteps.includes(step)) {
      api.startWordGen(currentFileId).catch(() => {})
    } else if (step === 'input') {
      api.stopWordGen(currentFileId).catch(() => {})
    }
  }, [step, currentFileId])

  useEffect(() => {
    if (learningContainerRef.current) {
      learningContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [step, currentExerciseData, learningData, quizData, listeningQuizData])
  
  const updateUnitStars = (key, starCount) => {
    setUnitStarCounts(prev => {
      const updated = { ...prev, [key]: starCount }
      if (currentFileId) {
        api.saveUnitStars(currentFileId, { [key]: updated[key] }).catch(err => {
          console.error('Failed to save stars:', err)
        })
      }
      return updated
    })
  }
  
  // 获取当前语言的翻译 - 保持上一个语言作为过渡，不回退到中文
  const lastValidTRef = useRef(translations.zh)

  const zhBase = customTranslations.zh || translations.zh
  // ponytail: 内置语言直接用，不走LLM翻译
  const builtinT = translations[uiLang]
  let t
  if (customTranslations[uiLang]) {
    t = { ...zhBase, ...customTranslations[uiLang] }
    lastValidTRef.current = t
  } else if (builtinT) {
    t = { ...zhBase, ...builtinT }
    lastValidTRef.current = t
  } else {
    // 新语言还没加载完，保持上一个已加载的语言
    t = lastValidTRef.current
  }

  // Fetch translations when uiLang changes (all languages go through API for consistency)
  useEffect(() => {
    // ponytail: 内置语言不需要LLM翻译
    if (translations[uiLang]) return
    if (loadedLangs.has(uiLang)) return
    
    setLoadedLangs(prev => new Set([...prev, uiLang]))
    setTranslatingUI(true)
    
    // Poll for translations (backend may return pending status while LLM is generating)
    const pollTranslation = async () => {
      try {
        const data = await api.translateUI(uiLang)
        
        if (data._status === 'pending') {
          // LLM still generating, poll again in 2 seconds
          setTimeout(pollTranslation, 2000)
          return
        }
        
        if (data._error || data._lang_code === null) {
          // Translation failed, allow retry
          setLoadedLangs(prev => { const next = new Set(prev); next.delete(uiLang); return next })
          setTranslatingUI(false)
          return
        }
        
        // Translation succeeded
        setCustomTranslations(prev => ({ ...prev, [uiLang]: data }))
        setTranslatingUI(false)
      } catch (err) {
        console.error('[i18n] Failed to fetch translations for:', uiLang, err)
        setLoadedLangs(prev => { const next = new Set(prev); next.delete(uiLang); return next })
        setTranslatingUI(false)
      }
    }
    
    pollTranslation()
  }, [uiLang])

  useEffect(() => {
    if (vocab.length > 0) {
      sortVocab()
    }
  }, [vocab, sortOrder])

  useEffect(() => {
    if (generatingUnits.size === 0 || !currentFileId) return

    const interval = setInterval(async () => {
      try {
        const phase1UnitsData = await api.getPhaseUnits(currentFileId, 1)
        const newGenUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) newGenUnits.add(i) })
        setGeneratingUnits(newGenUnits)
        if (newGenUnits.size === 0) {
          setPhase1Units(phase1UnitsData.units)
          setCurrentPhase1Unit(phase1UnitsData.current_unit)
        }
      } catch (e) {}
    }, 3000)

    return () => clearInterval(interval)
  }, [generatingUnits, currentFileId])

  // Keep refs in sync with state for use in goToNextReviewItem
  useEffect(() => {
    wrongItemsRef.current = wrongItems
  }, [wrongItems])

  useEffect(() => {
    reviewIndexRef.current = reviewIndex
  }, [reviewIndex])

  // 轮询处理状态
  useEffect(() => {
    if (!currentFileId || skipPolling) return

    console.log('开始轮询，文件ID:', currentFileId)

    let pollCount = 0
    const maxPolls = 300 // 10分钟
    let pollingInterval = null

    const pollStatus = async () => {
      pollCount++
      console.log(`第${pollCount}次轮询，文件ID: ${currentFileId}`)

      try {
        const status = await api.getStatus(currentFileId)
        console.log('状态响应:', status)

        // 强制更新词汇表和句子翻译，确保实时显示
        if (status.vocab) {
          console.log('更新词汇表，长度:', status.vocab.length)
          setVocab([...status.vocab]) // 使用展开运算符强制更新
        }

        if (status.sentence_translations) {
          console.log('更新句子翻译，数量:', status.sentence_translations.length)
          setSentenceTranslations([...status.sentence_translations]) // 使用展开运算符强制更新
        }

        // 更新进度
        if (status.progress !== undefined) {
          setProgress(status.progress)
        }

        // 更新预处理状态
        if (status.preprocess === 'translating') {
          setPreprocessStatus('translating')
        } else if (status.preprocess === 'generating') {
          setPreprocessStatus('generating')
        } else if (status.preprocess === 'detecting') {
          setPreprocessStatus('detecting')
        } else {
          setPreprocessStatus(null)
        }

        // 更新检测到的语言（auto 模式下从轮询结果获取，避免显示默认值 'en'）
        if (status.source_lang && status.source_lang !== 'auto') {
          setDetectedLang(status.source_lang)
        }

        // 更新标题（后台任务生成后）
        if (status.title) {
          setFileTitle(status.title)
        }

        // 更新完整原文（LLM翻译/生成后的文本）
        if (status.original_text) {
          setOriginalText(status.original_text)
        }

        // 更新处理信息
        if (status.current_sentence !== undefined && status.total_sentences !== undefined) {
          setProcessingInfo({
            current: status.current_sentence,
            total: status.total_sentences
          })
        }

        if (status.status === 'completed') {
          console.log('处理完成，词汇表长度:', status.vocab.length)
          setVocab([...status.vocab])
          setSentenceTranslations([...status.sentence_translations])
          setProgress(100)
          setProcessingInfo(null)
          setLoading(false)
          setSkipPolling(true)
          setHistoryRefresh(v => v + 1)
          // 停止轮询
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
        } else if (status.status === 'error') {
          console.error('处理错误:', status.error)
          setLoading(false)
          setSkipPolling(true)
          setPreprocessStatus(null)
          setStep('input')
          // 停止轮询
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
          // 如果是 API Key 相关错误，打开设置
          const errMsg = status.error || ''
          if (errMsg.includes('API Key') || errMsg.includes('Key')) {
            showAlert(t.apiKeyInvalid || 'API Key 无效或已过期，请检查设置中的 API Key', t.apiKeyError || 'API Key 错误')
            setShowSettings(true)
          } else {
            showAlert(t.processFailed || '处理失败，请重试')
          }
        } else if (pollCount >= maxPolls) {
          console.error('轮询超时')
          showAlert(t.processTimeout || '处理超时，请重试')
          setLoading(false)
          setSkipPolling(true)
          // 停止轮询
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
        }
      } catch (error) {
        console.error('轮询错误:', error)
        if (error.response && error.response.status === 404) {
          // 后端重启或状态丢失，立即停止轮询
          console.log('状态丢失(404)，停止轮询')
          setLoading(false)
          setSkipPolling(true)
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
        } else if (error.response && (error.response.status === 504 || error.response.status === 502 || error.response.status === 503)) {
          console.log('后端繁忙，继续轮询...')
        } else if (pollCount >= maxPolls) {
          showAlert(t.networkError || '网络错误，请重试')
          setLoading(false)
          setSkipPolling(true)
          if (pollingInterval) {
            clearInterval(pollingInterval)
          }
        }
      }
    }

    // 立即执行一次轮询
    pollStatus()
    // 设置轮询间隔为2秒，减少服务器负担
    pollingInterval = setInterval(pollStatus, 1000)

    // 清理函数
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval)
      }
    }
  }, [currentFileId, skipPolling])

  const sortVocab = () => {
    const sorted = [...vocab].sort((a, b) => {
      const wordA = a.word.toLowerCase()
      const wordB = b.word.toLowerCase()
      return sortOrder === 'asc' ? wordA.localeCompare(wordB) : wordB.localeCompare(wordA)
    })
    setDisplayVocab(sorted)
  }

  const toggleSortOrder = () => {
    setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')
  }

  const handleSentenceClick = (index) => {
    setSelectedSentence(prev => prev === index ? null : index)
  }

  const handleCloseSentenceDetail = () => {
    setSelectedSentence(null)
  }

  const handleProcess = async () => {
    if (!text.trim()) return

    setSkipPolling(false)
    setLoading(true)
    setProgress(0)
    setProcessingInfo(null)
    setVocab([])
    setDisplayVocab([])
    setSentenceTranslations([])
    setSelectedWord(null)
    setSelectedSentence(null)
    setSelectedOption(null)
    setIsCorrect(null)
    setCurrentFileId(null)
    setFileId(null)
    setFileTitle('')
    setOriginalText('')
    setDetectedLang(null)
    // 重置字典状态，避免显示上一个条目的残留
    dictStateRef.current = { vocabPage: 1, sentencePage: 1, globalVocabPage: 1, vocabScrollPos: 0, sentenceTranslationScrollPos: 0, sentenceOriginalScrollPos: 0, globalVocabScrollPos: 0, vocabDisplayMode: 0, sentenceDisplayMode: 0, showOriginal: false, showGlobalVocab: false, vocabSearch: '', sentenceSearch: '' }

    // 先检查 API Key 是否已配置
    try {
      const settingsResp = await fetch('/api/settings')
      const settingsData = await settingsResp.json()
      const activeIdx = settingsData.active_index || 0
      const activeConfig = (settingsData.configs || [])[activeIdx]
      if (!activeConfig || !activeConfig.has_key) {
        setLoading(false)
        showAlert(t.noApiKey || '请先在设置中填写 API Key', t.apiKeyError || 'API Key 错误')
        setShowSettings(true)
        return
      }
    } catch (e) {
      // 检查失败则继续，让后端报错
    }

    if (inputMode === 'translate') {
      setPreprocessStatus('translating')
    } else if (inputMode === 'generate') {
      setPreprocessStatus('generating')
    } else if (sourceLang === 'auto') {
      setPreprocessStatus('detecting')
    } else {
      setPreprocessStatus(null)
    }
    
    setStep('dictionary')
    
    try {
      // 所有模式统一调用 processText，翻译/生成/语言检测在后台执行，不会超时
      const response = await api.processText(text.trim(), sourceLang, targetLang, inputMode)
      
      if (response && response.file_id) {
        const fileId = response.file_id
        setFileId(fileId)
        setCurrentFileId(fileId)
        if (response.title) setFileTitle(response.title)
        // 直接输入模式：原文就是用户输入的文本，立即设置
        if (inputMode === 'direct') {
          setOriginalText(text.trim())
        }
        // 处理开始后立即刷新历史记录列表，用户能立即看到新条目
        setHistoryRefresh(v => v + 1)
        api.getUserPreferences().then(prefs => {
          if (prefs.recent_languages) setRecentLanguages(prefs.recent_languages)
        }).catch(() => {})
      } else {
        throw new Error('无效的API响应')
      }
    } catch (error) {
      console.error('处理文本错误:', error)
      setPreprocessStatus(null)
      setStep('input')
      if (error.response && error.response.status === 400) {
        const detail = error.response.data?.detail || ''
        if (detail.includes('API Key')) {
          showAlert(t.apiKeyInvalid || 'API Key 无效或已过期，请检查设置中的 API Key', t.apiKeyError || 'API Key 错误')
          setShowSettings(true)
        } else {
          showAlert(t.badRequest || '请求参数错误')
        }
      } else if (error.response && error.response.status === 504) {
        showAlert(t.networkTimeout || '网络连接超时，请检查网络连接后重试')
      } else if (error.message && error.message.includes('timeout')) {
        showAlert(t.processTimeout || '处理超时，请稍后重试')
      } else {
        showAlert(t.processFailed || '处理失败，请重试')
      }
      setLoading(false)
    }
  }

  const startLearning = async () => {
    if (!currentFileId) return
    
    setLoading(true)
    try {
      // 获取学习进度和分组信息
      const progressData = await api.getLearningProgress(currentFileId)
      setUnits(progressData.units)
      setCurrentUnit(progressData.current_unit)
      setTotalUnits(progressData.total_units)
      setAllUnitsCompleted(progressData.all_units_completed)
      setStep('progress')
    } catch (error) {
      console.error('开始学习错误:', error)
      showAlert(t.cannotStartLearning || '无法开始学习，请重试')
    } finally {
      setLoading(false)
    }
  }

  const startLearningPhases = async () => {
    if (!currentFileId) return
    
    setLoading(true)
    try {
      const [phase1UnitsData, phase2UnitsData, starsData] = await Promise.all([
        api.getPhaseUnits(currentFileId, 1),
        api.getPhaseUnits(currentFileId, 2),
        api.getUnitStars(currentFileId)
      ])
      
      setPhase1Units(phase1UnitsData.units)
      setPhase2Units(phase2UnitsData.units)
      setCurrentPhase1Unit(phase1UnitsData.current_unit)
      setCurrentPhase2Unit(phase2UnitsData.current_unit)
      setUnitStarCounts(starsData.stars || {})
      const genUnits = new Set()
      phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
      setGeneratingUnits(genUnits)
      setStep('all-units')
    } catch (error) {
      console.error('获取单元错误:', error)
      showAlert(t.cannotGetUnits || '无法获取学习单元，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePhaseSelect = async (phaseNumber) => {
    if (!currentFileId) return
    
    setLoading(true)
    try {
      setCurrentPhase(phaseNumber)
      if (phaseNumber === 1) {
        // Phase1 is original word learning
        const progressData = await api.getLearningProgress(currentFileId)
        setUnits(progressData.units)
        setCurrentUnit(progressData.current_unit)
        setTotalUnits(progressData.total_units)
        setAllUnitsCompleted(progressData.all_units_completed)
        setStep('progress')
      } else {
        const phaseUnitsData = await api.getPhaseUnits(currentFileId, phaseNumber)
        setPhaseUnits(phaseUnitsData.units)
        setCurrentPhaseUnit(phaseUnitsData.current_unit)
        setStep('phase-progress')
      }
    } catch (error) {
      console.error('选择阶段错误:', error)
      showAlert(t.cannotSelectPhase || '无法选择阶段，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePhase1UnitClick = async (unitId) => {
    if (!currentFileId) return
    
    setUnitErrorCount(0)
    unitErrorCountRef.current = 0
    setWrongItems([])
    setReviewMode(false)
    setReviewIndex(0)
    setReviewRound(0)

    setLoading(true)
    try {
      const unit = phase1Units[unitId]
      const startIndex = unit?.start_index ?? unitId * 10
      await api.setProgress(currentFileId, startIndex)
      const response = await api.getRandomWord(currentFileId)
      if (response.type === 'sentence_quiz') {
        setQuizData(response)
        setUnitEndIndex(response.unit_end_index)
        setLearningMode('sentence')
        setStep('sentence-quiz')
      } else if (response.type === 'listening_quiz') {
        if (skipListening) {
          setLoading(false)
          return getNextWord(0)
        }
        setListeningQuizData(response)
        setUnitEndIndex(response.unit_end_index)
        setLearningMode('listening')
        setStep('listening-quiz')
      } else if (response.type === 'unit_complete' || response.type === 'all_complete') {
        const [phase1UnitsData, phase2UnitsData] = await Promise.all([
          api.getPhaseUnits(currentFileId, 1),
          api.getPhaseUnits(currentFileId, 2)
        ])
        setPhase1Units(phase1UnitsData.units)
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        setCompletedUnitId(unitId)
        setCompletedPhase(1)
        const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
        updateUnitStars(`1-${unitId}`, starCount)
        setStep('unit-complete')
      } else {
        setLearningData(response)
        setUnitEndIndex(response.unit_end_index)
        setShowWordCard(false)
        setSelectedOption(null)
        setIsCorrect(null)
        setLearningMode('word')
        setStep('learning')
      }
    } catch (error) {
      console.error('获取单元单词错误:', error)
      showAlert(t.cannotGetWords || '无法获取单元单词，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePhase2UnitClick = async (unitId) => {
    if (!currentFileId) return
    
    setUnitErrorCount(0)
    unitErrorCountRef.current = 0
    setWrongItems([])
    setReviewMode(false)
    setReviewIndex(0)
    setReviewRound(0)

    setLoading(true)
    try {
      setCurrentPhase(2)
      setCurrentPhaseUnit(unitId)
      await api.setPhaseProgress(currentFileId, 2, unitId, unitId * 10)
      const exerciseData = await api.getPhaseUnitExercise(currentFileId, 2, unitId)
      if (exerciseData.unit_complete) {
        const [phase1UnitsData, phase2UnitsData] = await Promise.all([
          api.getPhaseUnits(currentFileId, 1),
          api.getPhaseUnits(currentFileId, 2)
        ])
        setPhase1Units(phase1UnitsData.units)
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        setCompletedUnitId(unitId)
        setCompletedPhase(2)
        const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
        updateUnitStars(`2-${unitId}`, starCount)
        setStep('unit-complete')
      } else {
        setExerciseType(exerciseData.exercise_type)
        setCurrentExerciseData({
          ...exerciseData.data,
          mask_version: exerciseData.mask_version,
          total_masks: exerciseData.total_masks,
          exercise_type_index: exerciseData.exercise_type_index,
          exercise_index_in_unit: exerciseData.exercise_index_in_unit,
          total_exercises_in_unit: exerciseData.total_exercises_in_unit,
          sentence_preview: exerciseData.sentence_preview
        })
        setStep('phase-exercise')
      }
    } catch (error) {
      console.error('获取单元练习错误:', error)
      showAlert(t.cannotGetExercise || '无法获取练习，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handlePhaseUnitClick = async (unitId) => {
    if (!currentFileId || !currentPhase) return
    
    setLoading(true)
    try {
      setCurrentPhaseUnit(unitId)
      const exerciseData = await api.getPhaseUnitExercise(currentFileId, currentPhase, unitId)
      if (exerciseData.unit_complete) {
        setStep('phase-progress')
      } else if (exerciseData.redirect_to_phase1) {
        setStep('progress')
      } else {
        setExerciseType(exerciseData.exercise_type)
        setCurrentExerciseData({
          ...exerciseData.data,
          mask_version: exerciseData.mask_version,
          total_masks: exerciseData.total_masks,
          exercise_type_index: exerciseData.exercise_type_index,
          exercise_index_in_unit: exerciseData.exercise_index_in_unit,
          total_exercises_in_unit: exerciseData.total_exercises_in_unit,
          sentence_preview: exerciseData.sentence_preview
        })
        setStep('phase-exercise')
      }
    } catch (error) {
      console.error('获取单元练习错误:', error)
      showAlert(t.cannotGetExercise || '无法获取练习，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleNextPhaseExercise = async () => {
    if (!currentFileId || !currentPhase) return

    if (reviewMode) {
      goToNextReviewItem()
      setLoading(false)
      return
    }

    setLoading(true)
    try {
      const nextRes = await api.nextPhaseExercise(currentFileId, currentPhase, currentPhaseUnit)
      
      if (nextRes.unit_complete || nextRes.all_complete) {
        const [phase1UnitsData, phase2UnitsData] = await Promise.all([
          api.getPhaseUnits(currentFileId, 1),
          api.getPhaseUnits(currentFileId, 2)
        ])
        setPhase1Units(phase1UnitsData.units)
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        setCompletedUnitId(currentPhaseUnit)
        setCompletedPhase(currentPhase)
        const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
        updateUnitStars(`${currentPhase}-${currentPhaseUnit}`, starCount)
        setStep('unit-complete')
      } else if (nextRes.exercise_type) {
        setExerciseType(nextRes.exercise_type)
        setCurrentExerciseData({
          ...nextRes.data,
          mask_version: nextRes.mask_version,
          total_masks: nextRes.total_masks,
          exercise_type_index: nextRes.exercise_type_index,
          exercise_index_in_unit: nextRes.exercise_index_in_unit,
          total_exercises_in_unit: nextRes.total_exercises_in_unit,
          sentence_preview: nextRes.sentence_preview
        })
      }
    } catch (error) {
      console.error('下一个练习错误:', error)
      showAlert(t.cannotGetNextExercise || '无法获取下一个练习，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleUnitClick = async (unitIndex) => {
    setLoading(true)
    try {
      // 计算该单元的起始学习索引
      const startIndex = unitIndex * 10
      // 设置学习进度到该单元的起始位置
      await api.setProgress(currentFileId, startIndex)
      // 获取第一个单词
      const response = await api.getRandomWord(currentFileId)
      setLearningData(response)
      setShowWordCard(false)
      setSelectedOption(null)
      setIsCorrect(null)
      setLearningMode('word')
      setStep('learning')
    } catch (error) {
      console.error('获取单元单词错误:', error)
      showAlert(t.cannotGetWords || '无法获取单元单词，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleOptionSelect = (index) => {
    if (selectedOption !== null) {
      if (isCorrect) return
      setSelectedOption(index)
      const isCorrectAnswer = index === learningData.correct_index
      setIsCorrect(isCorrectAnswer)
      if (isCorrectAnswer) {
        setShowWordCard(true)
        if (reviewMode) {
          // After a wrong answer, the item was moved to the end of wrongItems,
          // so reviewIndex may point to a different item now.
          // Find the current item by its data to remove the correct one.
          setWrongItems(prev => {
            const idx = prev.findIndex(item => item.type === 'word' && item.data === learningData)
            if (idx !== -1) {
              return prev.filter((_, i) => i !== idx)
            }
            return prev.filter((_, i) => i !== reviewIndex)
          })
          setReviewIndex(prev => prev)
        }
      }
      return
    }
    setSelectedOption(index)
    const isCorrectAnswer = index === learningData.correct_index
    setIsCorrect(isCorrectAnswer)
    if (isCorrectAnswer) {
      setShowWordCard(true)
      if (reviewMode) {
        setWrongItems(prev => prev.filter((_, i) => i !== reviewIndex))
        setReviewIndex(prev => prev)
      }
    } else {
      if (!reviewMode) {
        setUnitErrorCount(prev => {
          const newCount = prev + 1
          unitErrorCountRef.current = newCount
          return newCount
        })
      }
      if (reviewMode) {
        const currentItem = wrongItems[reviewIndex]
        if (currentItem) {
          setWrongItems(prev => [...prev.filter((_, i) => i !== reviewIndex), currentItem])
          setReviewIndex(prev => prev)
        }
      } else {
        setWrongItems(prev => [...prev, { type: 'word', data: learningData }])
      }
    }
  }

  const handleSentenceQuizAnswer = (isCorrect) => {
    if (!isCorrect) {
      if (!reviewMode) {
        setUnitErrorCount(prev => {
          const newCount = prev + 1
          unitErrorCountRef.current = newCount
          return newCount
        })
      }
      if (reviewMode) {
        const currentItem = wrongItems[reviewIndex]
        if (currentItem) {
          setWrongItems(prev => [...prev.filter((_, i) => i !== reviewIndex), currentItem])
          setReviewIndex(prev => prev)
        }
      } else {
        setWrongItems(prev => [...prev, { type: 'sentence_quiz', data: quizData }])
      }
    } else {
      if (reviewMode) {
        setWrongItems(prev => prev.filter((_, i) => i !== reviewIndex))
        setReviewIndex(prev => prev)
      }
    }
  }

  const handleListeningQuizAnswer = (isCorrect) => {
    if (!isCorrect) {
      if (!reviewMode) {
        setUnitErrorCount(prev => {
          const newCount = prev + 1
          unitErrorCountRef.current = newCount
          return newCount
        })
      }
      if (reviewMode) {
        const currentItem = wrongItems[reviewIndex]
        if (currentItem) {
          setWrongItems(prev => [...prev.filter((_, i) => i !== reviewIndex), currentItem])
          setReviewIndex(prev => prev)
        }
      } else {
        setWrongItems(prev => [...prev, { type: 'listening_quiz', data: listeningQuizData }])
      }
    } else {
      if (reviewMode) {
        setWrongItems(prev => prev.filter((_, i) => i !== reviewIndex))
        setReviewIndex(prev => prev)
      }
    }
  }

  const handlePhase2Answer = (isCorrect) => {
    if (!isCorrect) {
      if (!reviewMode) {
        setUnitErrorCount(prev => {
          const newCount = prev + 1
          unitErrorCountRef.current = newCount
          return newCount
        })
      }
      if (reviewMode) {
        const currentItem = wrongItems[reviewIndex]
        if (currentItem) {
          setWrongItems(prev => [...prev.filter((_, i) => i !== reviewIndex), currentItem])
          setReviewIndex(prev => prev)
        }
      } else {
        setWrongItems(prev => [...prev, { type: exerciseType, data: currentExerciseData }])
      }
    } else {
      if (reviewMode) {
        setWrongItems(prev => prev.filter((_, i) => i !== reviewIndex))
        setReviewIndex(prev => prev)
      }
    }
  }

  const goToNextReviewItem = () => {
    // Use refs to avoid stale closure values when this function is called
    // after state updates that haven't been committed yet
    const currentWrongItems = wrongItemsRef.current
    const currentReviewIndex = reviewIndexRef.current

    if (currentWrongItems.length === 0) {
      setReviewMode(false)
      setReviewIndex(0)
      setReviewRound(0)
      setStep('unit-complete')
      return
    }
    const nextIdx = Math.min(currentReviewIndex, currentWrongItems.length - 1)
    setReviewIndex(nextIdx)
    setReviewRound(prev => prev + 1)
    const nextItem = currentWrongItems[nextIdx]
    if (nextItem?.type === 'word') {
      setLearningData(nextItem.data)
      setShowWordCard(false)
      setSelectedOption(null)
      setIsCorrect(null)
      setStep('learning')
    } else if (nextItem?.type === 'sentence_quiz') {
      setQuizData(nextItem.data)
      setStep('sentence-quiz')
    } else if (nextItem?.type === 'listening_quiz') {
      setListeningQuizData(nextItem.data)
      setStep('listening-quiz')
    } else if (nextItem?.type === 'masked_sentence' || nextItem?.type === 'translation_reconstruction') {
      setExerciseType(nextItem.type)
      setCurrentExerciseData(nextItem.data)
      setStep('phase-exercise')
    }
  }

  const getNextWord = async (retryCount = 0) => {
    if (!currentFileId) return
    if (isFetchingNextRef.current) return
    isFetchingNextRef.current = true
    
    setLoading(true)
    try {
      const nextWordResponse = await api.nextWord(currentFileId)
      const newIndex = nextWordResponse.new_index
      
      if (nextWordResponse.type === 'unit_complete') {
        const [phase1UnitsData, phase2UnitsData] = await Promise.all([
          api.getPhaseUnits(currentFileId, 1),
          api.getPhaseUnits(currentFileId, 2)
        ])
        setPhase1Units(phase1UnitsData.units)
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        const completedUnit = nextWordResponse.completed_unit_id ?? phase1UnitsData.current_unit
        setCompletedUnitId(completedUnit)
        setCompletedPhase(1)
        const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
        updateUnitStars(`1-${completedUnit}`, starCount)
        setStep('unit-complete')
        return
      }
      
      if (nextWordResponse.sentence_quiz) {
        const endIdx = nextWordResponse.unit_end_index || unitEndIndex
        setQuizData(nextWordResponse.sentence_quiz)
        setUnitEndIndex(endIdx)
        setLearningMode('sentence')
        setStep('sentence-quiz')
        return
      }
      
      if (nextWordResponse.listening_quiz) {
        if (skipListening) {
          isFetchingNextRef.current = false
          return getNextWord(retryCount)
        }
        const endIdx = nextWordResponse.unit_end_index || unitEndIndex
        setListeningQuizData(nextWordResponse.listening_quiz)
        setUnitEndIndex(endIdx)
        setLearningMode('listening')
        setStep('listening-quiz')
        return
      }
      
      const response = await api.getRandomWord(currentFileId)
      if (response.type === 'sentence_quiz') {
        setQuizData(response)
        setUnitEndIndex(response.unit_end_index)
        setLearningMode('sentence')
        setStep('sentence-quiz')
      } else if (response.type === 'listening_quiz') {
        if (skipListening) {
          isFetchingNextRef.current = false
          return getNextWord(retryCount)
        }
        setListeningQuizData(response)
        setUnitEndIndex(response.unit_end_index)
        setLearningMode('listening')
        setStep('listening-quiz')
      } else if (response.type === 'unit_complete' || response.type === 'all_complete') {
        const [phase1UnitsData, phase2UnitsData] = await Promise.all([
          api.getPhaseUnits(currentFileId, 1),
          api.getPhaseUnits(currentFileId, 2)
        ])
        setPhase1Units(phase1UnitsData.units)
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        const completedUnit = nextWordResponse?.completed_unit_id ?? phase1UnitsData.current_unit
        setCompletedUnitId(completedUnit)
        setCompletedPhase(1)
        const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
        updateUnitStars(`1-${completedUnit}`, starCount)
        setStep('unit-complete')
      } else {
        setLearningData(response)
        setUnitEndIndex(response.unit_end_index)
        setShowWordCard(false)
        setSelectedOption(null)
        setIsCorrect(null)
        setLearningMode('word')
        setStep('learning')
      }
    } catch (error) {
      console.error('获取下一个单词错误:', error)
      if (error.response && error.response.status === 401 && retryCount < 2) {
        isFetchingNextRef.current = false
        setTimeout(() => getNextWord(retryCount + 1), 1000)
        return
      }
      if (error.response && (error.response.status === 401 || error.response.status === 502 || error.response.status === 503 || error.response.status === 504)) {
        isFetchingNextRef.current = false
        setTimeout(() => getNextWord(retryCount + 1), 2000)
        return
      }
    } finally {
      isFetchingNextRef.current = false
      setLoading(false)
    }
  }

  const getWordDetails = async (word) => {
    if (!currentFileId) return
    
    // 如果点击的是当前选中的单词，则取消选中
    if (selectedWord && selectedWord.word === word) {
      setSelectedWord(null)
      return
    }
    
    try {
      const response = await api.getWordDetails(currentFileId, word)
      setSelectedWord(response)
    } catch (error) {
      console.error('获取单词详情错误:', error)
    }
  }

  const handleStudyWord = (wordData) => {
    setLearningData(wordData)
    setShowWordCard(false)
    setSelectedOption(null)
    setIsCorrect(null)
    setStep('learning')
  }

  const handleOpenVocabList = () => {
    setShowVocabList(true)
  }

  const handleConfirmBack = (targetStep) => {
    setConfirmDialog({
      isOpen: true,
      onConfirm: () => {
        setConfirmDialog({ isOpen: false, onConfirm: null })
        if (typeof targetStep === 'function') {
          targetStep()
        } else {
          setStep(targetStep || 'all-units')
        }
      }
    })
  }

  const handleNavigateToRecord = async (fileId, srcLang, tgtLang, title) => {
    setLoading(true)
    // 先清空上一个条目的数据，避免显示旧内容
    setVocab([])
    setDisplayVocab([])
    setSentenceTranslations([])
    setSelectedSentence(null)
    setSelectedWord(null)
    setProgress(0)
    setProcessingInfo(null)
    setOriginalText('')
    setDetectedLang(null)
    try {
      setCurrentFileId(fileId)
      setFileId(fileId)
      if (title) setFileTitle(title)
      const vocabData = await api.getVocab(fileId)
      const vocabList = vocabData.vocab || []
      setVocab(vocabList)
      const sentencesData = await api.getSentences(fileId)
      const sentenceList = sentencesData.sentences || []
      setSentenceTranslations(Array.isArray(sentenceList) ? sentenceList : [])
      // 从后端获取持久化的原文
      try {
        const infoResp = await fetch(`/api/file/${fileId}/info`)
        const infoData = await infoResp.json()
        if (infoData.original_text) {
          setOriginalText(infoData.original_text)
        } else if (Array.isArray(sentenceList) && sentenceList.length > 0) {
          setOriginalText(sentenceList.map(s => s.sentence || '').filter(Boolean).join('\n'))
        }
      } catch (e) {
        // fallback: 从句子拼接
        if (Array.isArray(sentenceList) && sentenceList.length > 0) {
          setOriginalText(sentenceList.map(s => s.sentence || '').filter(Boolean).join('\n'))
        }
      }
      try {
        const [phase1UnitsData, phase2UnitsData, starsData] = await Promise.all([
          api.getPhaseUnits(fileId, 1),
          api.getPhaseUnits(fileId, 2),
          api.getUnitStars(fileId)
        ])
        setPhase1Units(phase1UnitsData.units)
        setPhase2Units(phase2UnitsData.units)
        setCurrentPhase1Unit(phase1UnitsData.current_unit)
        setCurrentPhase2Unit(phase2UnitsData.current_unit)
        setUnitStarCounts(starsData.stars || {})
        const genUnits = new Set()
        phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
        setGeneratingUnits(genUnits)
      } catch (e) {
        console.error('Failed to load phase units:', e)
      }

      // 检查该条目是否仍在生成中，如果是则启用轮询实时更新
      try {
        const status = await api.getStatus(fileId)
        if (status.status === 'processing') {
          setSkipPolling(false)
          setProgress(status.progress || 0)
          if (status.current_sentence !== undefined && status.total_sentences !== undefined) {
            setProcessingInfo({ current: status.current_sentence, total: status.total_sentences })
          }
        } else {
          setSkipPolling(true)
          setProgress(100)
          setProcessingInfo(null)
        }
      } catch (e) {
        // 如果状态检查失败，默认跳过轮询
        setSkipPolling(true)
        setProgress(100)
        setProcessingInfo(null)
      }

      api.startWordGen(fileId).catch(() => {})
      setStep('dictionary')
    } catch (error) {
      console.error('Failed to load record:', error)
      showAlert(t.cannotLoadHistory || '无法加载学习记录，请重试')
    } finally {
      setLoading(false)
    }
  }

  const handleSkipListeningChange = (value) => {
    setSkipListening(value)
    api.saveUserPreferences({ skip_listening: value }).catch(() => {})
  }

  const handleOnlyNewWordsChange = (value) => {
    setOnlyNewWords(value)
    api.saveUserPreferences({ only_new_words: value }).catch(() => {})
  }

  const handleOpenWordList = (lang) => {
    setFavoriteLang(null)
    setWordListLang(prev => prev === lang ? null : lang)
  }

  const handleOpenFavorites = (lang) => {
    setWordListLang(null)
    setFavoriteLang(prev => prev === lang ? null : lang)
  }

  const handleNextSentenceQuiz = async () => {
    if (reviewMode) {
      goToNextReviewItem()
      setLoading(false)
      return
    }
    setLoading(true)
    try {
      await getNextWord()
    } catch (error) {
      console.error('获取下一个句子翻译题错误:', error)
      const response = await api.getRandomWord(currentFileId)
      setLearningData(response)
      setShowWordCard(false)
      setSelectedOption(null)
      setIsCorrect(null)
      setLearningMode('word')
      setStep('learning')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-screen overflow-hidden bg-parchment-50 bg-paper-grain">
      <main className="h-full">
        {step === 'input' ? (
          <div className="flex h-full">
            <HistorySidebar onNavigateToRecord={handleNavigateToRecord} t={t} onOpenWordList={handleOpenWordList} activeWordListLang={wordListLang} onOpenFavorites={handleOpenFavorites} activeFavoriteLang={favoriteLang} refreshTrigger={historyRefresh} />
            <div className="flex-1 min-w-0 relative h-full px-4 sm:px-6 lg:px-8 py-4">
              {wordListLang ? (
                <WordListPanel
                  sourceLang={wordListLang}
                  t={t}
                  onBack={() => setWordListLang(null)}
                  pageSize={pageSize}
                />
              ) : favoriteLang ? (
                <WordListPanel
                  sourceLang={favoriteLang}
                  t={t}
                  onBack={() => setFavoriteLang(null)}
                  pageSize={pageSize}
                  favoritesMode={true}
                />
              ) : (
                <>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowSettings(true)}
                    className="absolute top-3 right-4 p-2 text-ink-400 hover:text-ink-600 hover:bg-parchment-200/60 rounded-sm transition-colors z-10"
                  >
                    <Settings className="w-5 h-5" />
                  </motion.button>
                  {translatingUI && (
                    <div className="absolute inset-0 bg-parchment-50/80 backdrop-blur-sm z-20 flex items-center justify-center">
                      <div className="flex items-center gap-3 bg-parchment-50 border-2 border-aged-200 rounded-sm px-6 py-4 shadow-retro">
                        <Loader2 className="w-5 h-5 animate-spin text-amber-500" />
                        <span className="text-sm text-ink-600">{
                          (customTranslations[uiLang]?.translatingUI)
                          || (customTranslations[Array.from(loadedLangs).filter(l => l !== uiLang).pop()]?.translatingUI)
                          || t.translatingUI
                          || '正在切换界面语言...'
                        }</span>
                      </div>
                    </div>
                  )}
                  <AnimatePresence mode="wait">
                    <InputStep
                      key="input"
                      text={text}
                      setText={setText}
                      sourceLang={sourceLang}
                      setSourceLang={setSourceLang}
                      uiLang={uiLang}
                      loading={loading}
                      onProcess={handleProcess}
                      t={t}
                      inputMode={inputMode}
                      setInputMode={setInputMode}
                      recentLanguages={recentLanguages}
                    />
                  </AnimatePresence>
                </>
              )}
            </div>
          </div>
        ) : (
          <div ref={learningContainerRef} className="h-full overflow-y-auto px-4 sm:px-6 lg:px-8 py-4">
            <AnimatePresence mode="wait">
          {step === 'dictionary' && (
            <DictionaryStep
              key="dictionary"
              vocab={displayVocab}
              onToggleSort={toggleSortOrder}
              sortOrder={sortOrder}
              progress={progress}
              processingInfo={processingInfo}
              sentenceTranslations={sentenceTranslations}
              selectedSentence={selectedSentence}
              selectedWord={selectedWord}
              onSentenceClick={handleSentenceClick}
              onCloseSentenceDetail={handleCloseSentenceDetail}
              onWordClick={getWordDetails}
              onStartLearning={startLearningPhases}
              loading={loading}
              t={t}
              currentFileId={currentFileId}
              sourceLang={sourceLang}
              detectedLang={detectedLang}
              preprocessStatus={preprocessStatus}
              onBack={() => { dictStateRef.current = { vocabPage: 1, sentencePage: 1, globalVocabPage: 1, vocabScrollPos: 0, sentenceTranslationScrollPos: 0, sentenceOriginalScrollPos: 0, globalVocabScrollPos: 0, vocabDisplayMode: 0, sentenceDisplayMode: 0, showOriginal: false, showGlobalVocab: false, vocabSearch: '', sentenceSearch: '' }; setStep('input') }}
              fileTitle={fileTitle}
              onTitleChange={(newTitle) => setFileTitle(newTitle)}
              pageSize={pageSize}
              dictStateRef={dictStateRef}
              originalText={originalText}
            />
          )}
          
          {step === 'progress' && (
            <ProgressStep
              key="progress"
              units={units}
              currentUnit={currentUnit}
              onUnitClick={handleUnitClick}
              onBack={() => setStep('dictionary')}
              loading={loading}
              t={t}
              allUnitsCompleted={allUnitsCompleted}
            />
          )}
          
          {step === 'learning' && (
            <LearningStep
              key={`learning-${reviewMode ? reviewRound : 0}`}
              learningData={learningData}
              showWordCard={showWordCard}
              selectedOption={selectedOption}
              isCorrect={isCorrect}
              onOptionSelect={handleOptionSelect}
              onNextWord={reviewMode ? goToNextReviewItem : getNextWord}
              onBack={() => handleConfirmBack('all-units')}
              onOpenVocabList={handleOpenVocabList}
              loading={loading}
              t={t}
              sourceLang={sourceLang}
              skipListening={skipListening}
              reviewMode={reviewMode}
              reviewIndex={reviewIndex}
              wrongItemsCount={wrongItems.length}
            />
          )}

          {step === 'sentence-quiz' && (
            <SentenceQuizStep
              key={`sentence-quiz-${quizData?.flat_index ?? quizData?.original_sentence}-${reviewMode ? reviewRound : 0}`}
              quizData={quizData}
              onNextQuestion={handleNextSentenceQuiz}
              onBack={() => handleConfirmBack('all-units')}
              onComplete={async () => {
                if (currentFileId && currentPhase) {
                  const phase1UnitsData = await api.getPhaseUnits(currentFileId, 1)
                  const nextUnit = phase1UnitsData.current_unit + 1
                  await api.setPhaseProgress(currentFileId, 1, nextUnit, 0)
                }
                setCompletedUnitId(currentPhase1Unit)
                setCompletedPhase(1)
                setStep('unit-complete')
              }}
              loading={loading}
              t={t}
              onOpenVocabList={handleOpenVocabList}
              sourceLang={sourceLang}
              onAnswer={handleSentenceQuizAnswer}
              skipListening={skipListening}
              reviewMode={reviewMode}
              reviewIndex={reviewIndex}
              wrongItemsCount={wrongItems.length}
            />
          )}

          {step === 'listening-quiz' && (
            <ListeningQuizStep
              key={`listening-quiz-${listeningQuizData?.flat_index ?? listeningQuizData?.original_sentence}-${reviewMode ? reviewRound : 0}`}
              quizData={listeningQuizData}
              onNextQuestion={handleNextSentenceQuiz}
              onBack={() => handleConfirmBack('all-units')}
              loading={loading}
              t={t}
              onOpenVocabList={handleOpenVocabList}
              sourceLang={sourceLang}
              onAnswer={handleListeningQuizAnswer}
              skipListening={skipListening}
              onSkipListeningChange={handleSkipListeningChange}
              reviewMode={reviewMode}
              reviewIndex={reviewIndex}
              wrongItemsCount={wrongItems.length}
            />
          )}

          {step === 'unit-complete' && (
            <UnitCompleteStep
              key="unit-complete"
              unitNumber={completedUnitId || 0}
              totalUnits={completedPhase === 2 ? (phase2Units.length || 1) : (phase1Units.length || 1)}
              phase={completedPhase}
              onContinue={() => {
                setUnitErrorCount(0)
                unitErrorCountRef.current = 0
                setWrongItems([])
                setReviewMode(false)
                setReviewIndex(0)
                setReviewRound(0)
                setStep('all-units')
              }}
              onReview={() => {
                setReviewMode(true)
                setReviewIndex(0)
                setReviewRound(0)
                const firstWrong = wrongItems[0]
                if (firstWrong?.type === 'word') {
                  setLearningData(firstWrong.data)
                  setShowWordCard(false)
                  setSelectedOption(null)
                  setIsCorrect(null)
                  setStep('learning')
                } else if (firstWrong?.type === 'sentence_quiz') {
                  setQuizData(firstWrong.data)
                  setStep('sentence-quiz')
                } else if (firstWrong?.type === 'listening_quiz') {
                  setListeningQuizData(firstWrong.data)
                  setStep('listening-quiz')
                } else if (firstWrong?.type === 'masked_sentence' || firstWrong?.type === 'translation_reconstruction') {
                  setExerciseType(firstWrong.type)
                  setCurrentExerciseData(firstWrong.data)
                  setStep('phase-exercise')
                }
              }}
              errorCount={unitErrorCount}
              hasWrongItems={wrongItems.length > 0}
              wrongItemsCount={wrongItems.length}
              t={t}
              onSkipReview={() => {
                setReviewMode(false)
                setReviewIndex(0)
                setReviewRound(0)
                setWrongItems([])
                setUnitErrorCount(0)
                unitErrorCountRef.current = 0
                setStep('all-units')
              }}
            />
          )}
          
          {step === 'all-units' && (
            <AllUnitsStep
              key="all-units"
              phase1Units={phase1Units}
              phase2Units={phase2Units}
              currentPhase1Unit={currentPhase1Unit}
              currentPhase2Unit={currentPhase2Unit}
              onPhase1UnitClick={handlePhase1UnitClick}
              onPhase2UnitClick={handlePhase2UnitClick}
              onBack={() => setStep('dictionary')}
              onHome={() => setStep('input')}
              loading={loading}
              t={t}
              unitStarCounts={unitStarCounts}
              skipListening={skipListening}
              onSkipListeningChange={handleSkipListeningChange}
              onlyNewWords={onlyNewWords}
              onOnlyNewWordsChange={handleOnlyNewWordsChange}
              generatingUnits={generatingUnits}
              fileTitle={fileTitle}
              currentFileId={currentFileId}
              lastActiveTab={lastActiveTab}
              onTabChange={setLastActiveTab}
            />
          )}
          
          {step === 'phase-selector' && (
            <PhaseSelectorStep
              key="phase-selector"
              phases={phases}
              currentFileId={currentFileId}
              onPhaseSelect={handlePhaseSelect}
              onBack={() => setStep('dictionary')}
              loading={loading}
              t={t}
            />
          )}
          
          {step === 'phase-progress' && (
            <PhaseProgressStep
              key="phase-progress"
              units={phaseUnits}
              currentUnit={currentPhaseUnit}
              phaseNumber={currentPhase}
              onUnitClick={handlePhaseUnitClick}
              onBack={() => setStep('all-units')}
              loading={loading}
              t={t}
            />
          )}
          
          {step === 'phase-exercise' && exerciseType === 'masked_sentence' && (
            <MaskedSentenceExerciseStep
              key={`masked-exercise-${currentExerciseData?.exercise_index_in_unit}-${currentExerciseData?.mask_version}-${reviewMode ? reviewRound : 0}`}
              data={currentExerciseData}
              onNext={handleNextPhaseExercise}
              onBack={() => handleConfirmBack('all-units')}
              onComplete={async () => {
                const [phase1UnitsData, phase2UnitsData] = await Promise.all([
                  api.getPhaseUnits(currentFileId, 1),
                  api.getPhaseUnits(currentFileId, 2)
                ])
                setPhase1Units(phase1UnitsData.units)
                const genUnits = new Set()
                phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
                setGeneratingUnits(genUnits)
                setPhase2Units(phase2UnitsData.units)
                setCurrentPhase1Unit(phase1UnitsData.current_unit)
                setCurrentPhase2Unit(phase2UnitsData.current_unit)
                setCompletedUnitId(currentPhaseUnit)
                setCompletedPhase(currentPhase)
                const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
                updateUnitStars(`${currentPhase}-${currentPhaseUnit}`, starCount)
                setStep('unit-complete')
              }}
              loading={loading}
              t={t}
              onOpenVocabList={handleOpenVocabList}
              maskVersion={currentExerciseData?.mask_version}
              totalMasks={currentExerciseData?.total_masks}
              exerciseIndexInUnit={currentExerciseData?.exercise_index_in_unit}
              totalExercisesInUnit={currentExerciseData?.total_exercises_in_unit}
              sentencePreview={currentExerciseData?.sentence_preview}
              sourceLang={sourceLang}
              onAnswer={handlePhase2Answer}
              reviewMode={reviewMode}
              reviewIndex={reviewIndex}
              wrongItemsCount={wrongItems.length}
            />
          )}

          {step === 'phase-exercise' && exerciseType === 'translation_reconstruction' && (
            <TranslationReconstructionStep
              key={`reconstruction-exercise-${currentExerciseData?.exercise_index_in_unit}-${reviewMode ? reviewRound : 0}`}
              data={currentExerciseData}
              onNext={handleNextPhaseExercise}
              onBack={() => handleConfirmBack('all-units')}
              onComplete={async () => {
                const [phase1UnitsData, phase2UnitsData] = await Promise.all([
                  api.getPhaseUnits(currentFileId, 1),
                  api.getPhaseUnits(currentFileId, 2)
                ])
                setPhase1Units(phase1UnitsData.units)
                const genUnits = new Set()
                phase1UnitsData.units.forEach((u, i) => { if (u.generating) genUnits.add(i) })
                setGeneratingUnits(genUnits)
                setPhase2Units(phase2UnitsData.units)
                setCurrentPhase1Unit(phase1UnitsData.current_unit)
                setCurrentPhase2Unit(phase2UnitsData.current_unit)
                setCompletedUnitId(currentPhaseUnit)
                setCompletedPhase(currentPhase)
                const starCount = Math.max(0, 3 - Math.floor(unitErrorCountRef.current / 3))
                updateUnitStars(`${currentPhase}-${currentPhaseUnit}`, starCount)
                setStep('unit-complete')
              }}
              loading={loading}
              t={t}
              onOpenVocabList={handleOpenVocabList}
              exerciseIndexInUnit={currentExerciseData?.exercise_index_in_unit}
              totalExercisesInUnit={currentExerciseData?.total_exercises_in_unit}
              sentencePreview={currentExerciseData?.sentence_preview}
              sourceLang={sourceLang}
              onAnswer={handlePhase2Answer}
              reviewMode={reviewMode}
              reviewIndex={reviewIndex}
              wrongItemsCount={wrongItems.length}
            />
          )}
        </AnimatePresence>
          </div>
        )}
      </main>
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} uiLang={uiLang} onUiLangChange={setUiLang} pageSize={pageSize} onPageSizeChange={setPageSize} t={t} recentLangs={recentLanguages} onRecentLangsChange={setRecentLanguages} />
      {showVocabList && <VocabListStep onClose={() => setShowVocabList(false)} vocab={vocab} loading={loading} t={t} currentFileId={currentFileId} sourceLang={sourceLang} pageSize={pageSize} />}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        title={t.confirmExit || '确认退出'}
        message={t.exitMessage || '你确定要退出当前练习吗？退出后进度将不会保存。'}
        confirmText={t.exitAction || '退出'}
        cancelText={t.continueLearning || '继续练习'}
        onConfirm={confirmDialog.onConfirm}
        onCancel={() => setConfirmDialog({ isOpen: false, onConfirm: null })}
      />
      <AlertDialog
        open={alertDialog.open}
        title={alertDialog.title}
        message={alertDialog.message}
        onClose={() => setAlertDialog({ open: false, title: '', message: '' })}
        t={t}
      />
    </div>
  )
}

export default App