import { useState, useMemo, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, X, BookOpen, Volume2, Loader2, Brain, ChevronLeft, ChevronRight } from 'lucide-react'
import { api } from '../utils/api'
import { speakText } from '../utils/speech'
import { groupVocab } from '../utils/vocab'
import WordDetail from './WordDetail'

function VocabListStep({ vocab, onClose, loading, t, currentFileId, sourceLang, pageSize = 50 }) {
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedWord, setExpandedWord] = useState(null)
  const [enrichedWords, setEnrichedWords] = useState({})
  const [loadingWord, setLoadingWord] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const listRef = useRef(null)
  const wordRefs = useRef({})

  // 切换页数时滚动条置顶
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = 0
  }, [currentPage])

  const scrollToWord = useCallback((wordKey) => {
    requestAnimationFrame(() => {
      const el = wordRefs.current[wordKey]
      if (el && listRef.current) {
        const container = listRef.current
        const containerRect = container.getBoundingClientRect()
        const elRect = el.getBoundingClientRect()
        const scrollOffset = elRect.top - containerRect.top + container.scrollTop - 32
        container.scrollTo({ top: Math.max(0, scrollOffset), behavior: 'instant' })
      }
    })
  }, [])

  const handleWordClick = useCallback(async (word) => {
    const wordKey = word.word
    if (expandedWord === wordKey) {
      setExpandedWord(null)
      return
    }
    speakText(word.word, sourceLang)
    scrollToWord(wordKey)
    setTimeout(() => setExpandedWord(wordKey), 50)

    if (currentFileId && !enrichedWords[wordKey]) {
      setLoadingWord(wordKey)
      try {
        const details = await api.getWordDetails(currentFileId, wordKey)
        setEnrichedWords(prev => ({ ...prev, [wordKey]: details }))
      } catch (e) {
        console.error('Failed to fetch word details:', e)
      } finally {
        setLoadingWord(null)
      }
    }
  }, [expandedWord, scrollToWord, currentFileId, enrichedWords])

  const filteredVocab = useMemo(() => {
    if (!searchQuery.trim()) return vocab
    const q = searchQuery.toLowerCase()
    return vocab.filter(w =>
      w.word.toLowerCase().includes(q) ||
      (w.meaning && w.meaning.toLowerCase().includes(q)) ||
      (w.context_meaning && w.context_meaning.toLowerCase().includes(q)) ||
      (w.enriched_meaning && w.enriched_meaning.toLowerCase().includes(q))
    )
  }, [vocab, searchQuery])

  const totalPages = useMemo(() => Math.max(1, Math.ceil(filteredVocab.length / pageSize)), [filteredVocab, pageSize])

  const pagedVocab = useMemo(() => {
    const start = (currentPage - 1) * pageSize
    return filteredVocab.slice(start, start + pageSize)
  }, [filteredVocab, currentPage, pageSize])

  // 完全照搬 DictionaryStep 的分组逻辑
  const groupedVocab = useMemo(() => {
    return groupVocab(pagedVocab)
  }, [pagedVocab])

  const letterIndex = useMemo(() => {
    return groupedVocab.map(([letter]) => letter)
  }, [groupedVocab])

  const allLetterIndex = useMemo(() => {
    return groupVocab(filteredVocab).map(([letter]) => letter)
  }, [filteredVocab])

  const speakWord = useCallback((text, e) => {
    if (e) e.stopPropagation()
    speakText(text, sourceLang)
  }, [sourceLang])

  const pendingLetterRef = useRef(null)

  const scrollToLetter = useCallback((letter) => {
    const el = document.getElementById(`vocab-group-${letter}`)
    if (el && listRef.current) {
      const container = listRef.current
      const containerRect = container.getBoundingClientRect()
      const elRect = el.getBoundingClientRect()
      const scrollOffset = elRect.top - containerRect.top + container.scrollTop - 32
      container.scrollTo({ top: Math.max(0, scrollOffset), behavior: 'smooth' })
    } else {
      const letterLower = letter.toLowerCase()
      const wordIdx = filteredVocab.findIndex(w => {
        const key = (w.word || '')[0]?.normalize('NFD')[0]?.toUpperCase() || '#'
        return key === letter || key.toLowerCase() === letterLower
      })
      if (wordIdx >= 0) {
        const targetPage = Math.floor(wordIdx / pageSize) + 1
        if (targetPage !== currentPage) {
          pendingLetterRef.current = letter
          setCurrentPage(targetPage)
        }
      }
    }
  }, [filteredVocab, currentPage, pageSize])

  useEffect(() => {
    if (pendingLetterRef.current) {
      const letter = pendingLetterRef.current
      pendingLetterRef.current = null
      setTimeout(() => {
        const el = document.getElementById(`vocab-group-${letter}`)
        if (el && listRef.current) {
          const container = listRef.current
          const containerRect = container.getBoundingClientRect()
          const elRect = el.getBoundingClientRect()
          const scrollOffset = elRect.top - containerRect.top + container.scrollTop - 32
          container.scrollTo({ top: Math.max(0, scrollOffset), behavior: 'smooth' })
        }
      }, 200)
    }
  }, [currentPage])

  const getEnriched = (word) => enrichedWords[word] || {}

  const renderPagination = () => {
    if (totalPages <= 1) return null
    const pages = Array.from({ length: totalPages }, (_, i) => i + 1).filter(p => {
      if (totalPages <= 7) return true
      if (p === 1 || p === totalPages) return true
      if (Math.abs(p - currentPage) <= 1) return true
      return false
    }).reduce((acc, p, i, arr) => {
      if (i > 0 && p - arr[i - 1] > 1) acc.push('...')
      acc.push(p)
      return acc
    }, [])

    return (
      <div className="flex items-center justify-center gap-0.5 py-1.5 border-t border-aged-200/60 bg-parchment-50/40 shrink-0">
        <button
          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
          disabled={currentPage <= 1}
          className={`p-1 rounded transition-colors ${currentPage <= 1 ? 'text-aged-200 cursor-not-allowed' : 'text-ink-400 hover:text-ink-600 hover:bg-parchment-100'}`}
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
        {pages.map((p, i) =>
          p === '...' ? (
            <span key={`dots-${i}`} className="text-[10px] text-aged-300 px-0.5">…</span>
          ) : (
            <button
              key={p}
              onClick={() => setCurrentPage(p)}
              className={`min-w-[22px] h-[22px] flex items-center justify-center text-[10px] rounded transition-colors ${
                currentPage === p
                  ? 'bg-amber-100 text-amber-500 font-bold'
                  : 'text-ink-400 hover:text-ink-600 hover:bg-parchment-100'
              }`}
            >
              {p}
            </button>
          )
        )}
        <button
          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
          disabled={currentPage >= totalPages}
          className={`p-1 rounded transition-colors ${currentPage >= totalPages ? 'text-aged-200 cursor-not-allowed' : 'text-ink-400 hover:text-ink-600 hover:bg-parchment-100'}`}
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40">
      <div className="bg-parchment-50 border-2 border-aged-200/80 rounded-md shadow-retro-sm overflow-hidden flex flex-col max-w-2xl max-h-[85vh] w-full">
        <div className="px-5 py-3.5 border-b border-aged-200/80 bg-parchment-50/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-amber-500" />
              <h2 className="text-sm font-bold font-display text-ink-700">{t.vocabList || '单词表'}</h2>
              <span className="badge-ochre ml-1">
                {vocab.length}
              </span>
              {searchQuery && filteredVocab.length !== vocab.length && (
                <span className="text-xs text-ink-400">· {t.matched || '匹配'} {filteredVocab.length}</span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-ink-400 hover:text-ink-700 hover:bg-parchment-100 rounded-sm transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="px-4 py-2 border-b border-parchment-100">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-aged-300" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => { setSearchQuery(e.target.value); setCurrentPage(1) }}
              placeholder={t.searchWordOrMeaning || '搜索单词或释义...'}
              className="input-warm w-full pl-9 pr-3 py-1.5 bg-parchment-50 border-2 border-aged-200/80 rounded-sm text-[13px] text-ink-700 placeholder:text-aged-300 focus:outline-none focus:ring-2 focus:ring-amber-200/60 focus:border-amber-300/60 transition-all"
            />
          </div>
        </div>

        <div className="flex-1 flex min-h-0">
          {loading ? (
            <div className="flex-1 py-16 text-center">
              <Loader2 className="w-8 h-8 mx-auto mb-3 animate-spin text-amber-400" />
              <p className="text-ink-400 text-sm">{t.loading}</p>
            </div>
          ) : filteredVocab.length === 0 ? (
            <div className="flex-1 py-16 text-center">
              <BookOpen className="w-10 h-10 mx-auto mb-3 text-aged-200" />
              <p className="text-ink-400 text-sm">
                {searchQuery ? (t.noMatchFound || '没有找到匹配的单词') : (t.noWordsYet || '暂无单词')}
              </p>
            </div>
          ) : (
            <>
              {allLetterIndex.length > 1 && !searchQuery && (
                <div className="flex flex-col items-center gap-px py-1 border-r border-aged-200/60 bg-parchment-50/40 w-5 shrink-0 overflow-y-auto">
                  {allLetterIndex.map(letter => {
                    const onCurrentPage = letterIndex.includes(letter)
                    return (
                      <button
                        key={letter}
                        onClick={() => scrollToLetter(letter)}
                        className={`w-4 h-4 flex items-center justify-center text-[8px] font-bold rounded transition-colors shrink-0 ${
                          onCurrentPage
                            ? 'text-ink-600 hover:text-amber-500 hover:bg-amber-50'
                            : 'text-aged-300/60 hover:text-amber-500 hover:bg-amber-50/50'
                        }`}
                      >
                        {letter}
                      </button>
                    )
                  })}
                </div>
              )}
              <div className="flex-1 min-w-0 flex flex-col">
                <div className="flex-1 overflow-y-scroll min-h-0" ref={listRef} style={{ scrollbarGutter: 'stable' }}>
                  <div className="space-y-3">
                    {groupedVocab.map(([letter, words], groupIdx) => (
                      <div key={`group-${groupIdx}-${letter}`} id={`vocab-group-${letter}`}>
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: groupIdx * 0.04 }}
                          className="sticky top-0 z-10 backdrop-blur-sm bg-parchment-50/80 px-4 py-1.5 border-b border-aged-200/40 mb-1"
                        >
                          <span className="text-xs font-bold text-amber-500/80 tracking-widest">{letter}</span>
                        </motion.div>
                        <div className="space-y-px">
                          {words.map((word, wordIdx) => {
                            const isExpanded = expandedWord === word.word
                            const enriched = getEnriched(word.word)
                            const displayMeaning = word.enriched_meaning || word.meaning || word.context_meaning
                            return (
                              <motion.div
                                key={`${word.word}-${wordIdx}`}
                                ref={el => { wordRefs.current[word.word] = el }}
                                initial={{ opacity: 0, y: 6 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-parchment-50"
                              >
                                <button
                                  onClick={() => handleWordClick(word)}
                                  className="w-full text-left px-4 py-2.5 flex items-center gap-2 hover:bg-amber-50/40 transition-colors group"
                                >
                                  <div className="flex-1 min-w-0 flex items-center gap-2 flex-wrap select-text">
                                    <span className="text-[14px] font-bold text-ink-800 tracking-tight shrink-0">
                                      {word.word}
                                    </span>
                                    {(enriched.ipa || word.ipa) && (
                                      <span className="text-[11px] text-ink-400 ipa-font shrink-0">
                                        {(enriched.ipa || word.ipa).startsWith('/') ? (enriched.ipa || word.ipa) : `/${enriched.ipa || word.ipa}/`}
                                      </span>
                                    )}
                                    {(enriched.morphology || word.morphology) && (
                                      <span className="text-[10px] px-1.5 py-0.5 bg-parchment-100 text-ink-500 rounded font-bold tracking-wide shrink-0">
                                        {enriched.morphology || word.morphology}
                                      </span>
                                    )}
                                    <span className="text-[12px] text-ink-500 truncate">
                                      {displayMeaning}
                                    </span>
                                  </div>
                                  <Volume2
                                    className="w-3.5 h-3.5 text-aged-300 hover:text-amber-500 shrink-0 transition-colors"
                                    onClick={(e) => speakWord(word.word, e)}
                                  />
                                </button>

                                <AnimatePresence>
                                  {isExpanded && (
                                    <motion.div
                                      initial={{ height: 0, opacity: 0 }}
                                      animate={{ height: 'auto', opacity: 1 }}
                                      exit={{ height: 0, opacity: 0 }}
                                      transition={{ duration: 0.2 }}
                                      className="overflow-hidden"
                                    >
                                      <div className="px-4 pb-3.5 border-t border-parchment-100/80">
                                        {loadingWord === word.word ? (
                                          <div className="pt-4 flex flex-col items-center justify-center gap-3">
                                            <Loader2 className="w-5 h-5 animate-spin text-amber-500" />
                                            <p className="text-[12px] text-ink-400">{t.loadingWordDetails || '正在加载单词详情...'}</p>
                                          </div>
                                        ) : (() => {
                                          const mergedWord = { ...word, ...enriched }
                                          const hasDetail = mergedWord.enriched_meaning || mergedWord.meaning || mergedWord.variants_detail || mergedWord.examples || mergedWord.memory_hint || mergedWord.context_sentences
                                          return hasDetail ? (
                                            <div className="pt-3">
                                              <div className="mb-2">
                                                <h3 className="label-warm mb-0.5 flex items-center gap-1">
                                                  <Brain className="w-3 h-3 text-amber-500" />
                                                  {t.definition || '释义'}
                                                </h3>
                                                <p className="text-[13px] text-ink-700 leading-relaxed">
                                                  {mergedWord.enriched_meaning || mergedWord.meaning || mergedWord.context_meaning}
                                                </p>
                                              </div>
                                              <WordDetail word={mergedWord} t={t} sourceLang={sourceLang} hideDefinition disableContextSentenceClick />
                                            </div>
                                          ) : (
                                            <div className="pt-3 text-center text-ink-400 text-[12px]">{t.noDetails || '暂无详情'}</div>
                                          )
                                        })()}
                                      </div>
                                    </motion.div>
                                  )}
                                </AnimatePresence>
                              </motion.div>
                            )
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                {renderPagination()}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default VocabListStep
