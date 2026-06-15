import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Settings, X, Key, Globe, Cpu, Check, Loader2, Gauge, Languages, ChevronLeft, ChevronRight, ChevronDown, Plus, Minus, BookOpen, RefreshCw, Download, ToggleLeft, ToggleRight, AlertCircle } from 'lucide-react'
import { api } from '../utils/api'
import { LangIcon, LANGUAGES } from './InputStep'

function NativeLangSelector({ value, onChange, recentLangs = [] }) {
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const containerRef = useRef(null)

  useEffect(() => {
    const handleClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const selectedLang = LANGUAGES.find(l => l.value === value)
  const filtered = LANGUAGES.filter(l => {
    if (!search) return true
    const s = search.toLowerCase()
    return l.native.toLowerCase().includes(s) || l.en.toLowerCase().includes(s) || l.zh.includes(search) || l.value.toLowerCase().includes(s)
  })

  const recentFiltered = recentLangs
    .filter(code => code !== value)
    .map(code => LANGUAGES.find(l => l.value === code))
    .filter(Boolean)
    .filter(l => {
      if (!search) return true
      const s = search.toLowerCase()
      return l.native.toLowerCase().includes(s) || l.en.toLowerCase().includes(s) || l.zh.includes(search)
    })

  const commonLangs = ['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es', 'ru', 'pt', 'it', 'ar', 'hi', 'th', 'vi', 'id']
  const commonFiltered = filtered.filter(l => commonLangs.includes(l.value))
  const otherFiltered = filtered.filter(l => !commonLangs.includes(l.value))

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-sm border-2 border-aged-200 bg-parchment-50 hover:bg-parchment-100 transition-colors text-sm"
      >
        <LangIcon langCode={value} size="sm" />
        <span className="text-ink-800 flex-1 text-left">{selectedLang?.native || value}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-aged-300 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 mt-1 w-full bg-parchment-50 rounded-sm border-2 border-aged-200 shadow-xl overflow-hidden">
          <div className="p-2 border-b border-parchment-100">
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search..."
              className="w-full px-2 py-1.5 rounded-sm bg-parchment-50 border-2 border-parchment-100 text-xs text-ink-700 placeholder-ink-400 focus:outline-none focus:border-amber-300"
              autoFocus
            />
          </div>
          <div className="max-h-48 overflow-y-auto">
            {recentFiltered.length > 0 && (
              <>
                <div className="px-3 py-1 text-[10px] text-ink-400 font-bold uppercase">Recent</div>
                {recentFiltered.map(l => (
                  <button
                    key={l.value}
                    type="button"
                    onClick={() => { onChange(l.value); setOpen(false); setSearch('') }}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-xs transition-colors ${
                      value === l.value ? 'bg-amber-50 text-amber-600' : 'text-ink-600 hover:bg-parchment-50'
                    }`}
                  >
                    <LangIcon langCode={l.value} size="sm" />
                    <span>{l.native}</span>
                  </button>
                ))}
              </>
            )}
            {commonFiltered.length > 0 && (
              <>
                <div className="px-3 py-1 text-[10px] text-ink-400 font-bold uppercase">Common</div>
                {commonFiltered.map(l => (
                  <button
                    key={l.value}
                    type="button"
                    onClick={() => { onChange(l.value); setOpen(false); setSearch('') }}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-xs transition-colors ${
                      value === l.value ? 'bg-amber-50 text-amber-600' : 'text-ink-600 hover:bg-parchment-50'
                    }`}
                  >
                    <LangIcon langCode={l.value} size="sm" />
                    <span>{l.native}</span>
                  </button>
                ))}
              </>
            )}
            {otherFiltered.length > 0 && (
              <>
                <div className="px-3 py-1 text-[10px] text-ink-400 font-bold uppercase border-t border-parchment-100">All Languages</div>
                {otherFiltered.map(l => (
                  <button
                    key={l.value}
                    type="button"
                    onClick={() => { onChange(l.value); setOpen(false); setSearch('') }}
                    className={`w-full flex items-center gap-2 px-3 py-1.5 text-xs transition-colors ${
                      value === l.value ? 'bg-amber-50 text-amber-600' : 'text-ink-600 hover:bg-parchment-50'
                    }`}
                  >
                    <LangIcon langCode={l.value} size="sm" />
                    <span>{l.native}</span>
                  </button>
                ))}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

const SECTIONS = ['api', 'general', 'nativeLang']

function SettingsModal({ isOpen, onClose, uiLang, onUiLangChange, pageSize, onPageSizeChange, t, recentLangs, onRecentLangsChange }) {
  const [configs, setConfigs] = useState([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [direction, setDirection] = useState(0)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(true)
  const [retryInterval, setRetryInterval] = useState(1)
  const [localUiLang, setLocalUiLang] = useState(uiLang || 'zh')
  const [localPageSize, setLocalPageSize] = useState(50)
  const [activeSection, setActiveSection] = useState('api')
  const [saveError, setSaveError] = useState('')

  // Version check state
  const [versionChecking, setVersionChecking] = useState(false)
  const [versionInfo, setVersionInfo] = useState(null)
  const [autoUpdate, setAutoUpdate] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setLoading(true)
      setSaved(false)
      setSaveError('')
      setActiveSection('api')
      Promise.all([
        fetch('/api/settings').then(res => res.json()),
        api.getUserPreferences().catch(() => ({}))
      ]).then(([data, prefs]) => {
        const loaded = (data.configs && data.configs.length > 0)
          ? data.configs.map(c => ({
              api_key: '',
              base_url: c.base_url || '',
              model: c.model || '',
              has_key: c.has_key || false,
              masked_key: c.api_key || '',
            }))
          : [{ api_key: '', base_url: '', model: '', has_key: false, masked_key: '' }]
        setConfigs(loaded)
        setCurrentIndex(data.active_index || 0)
        if (prefs.retry_interval !== undefined) setRetryInterval(prefs.retry_interval)
        if (prefs.ui_lang) setLocalUiLang(prefs.ui_lang)
        else if (prefs.target_lang) setLocalUiLang(prefs.target_lang)
        if (prefs.page_size) setLocalPageSize(prefs.page_size)
        if (prefs.auto_update !== undefined) setAutoUpdate(prefs.auto_update)
        setLoading(false)
      }).catch(() => {
        setConfigs([{ api_key: '', base_url: '', model: '', has_key: false, masked_key: '' }])
        setLoading(false)
      })
    }
  }, [isOpen])

  const updateConfig = useCallback((index, field, value) => {
    setConfigs(prev => {
      const next = [...prev]
      next[index] = { ...next[index], [field]: value }
      return next
    })
  }, [])

  const goNext = useCallback(() => {
    if (currentIndex < configs.length - 1) {
      setDirection(1)
      setCurrentIndex(i => i + 1)
    }
  }, [currentIndex, configs.length])

  const goPrev = useCallback(() => {
    if (currentIndex > 0) {
      setDirection(-1)
      setCurrentIndex(i => i - 1)
    }
  }, [currentIndex])

  const addConfig = useCallback(() => {
    const current = configs[configs.length - 1]
    const newConfig = {
      api_key: '',
      base_url: current?.base_url || '',
      model: current?.model || '',
      has_key: false,
      masked_key: '',
    }
    setDirection(1)
    setConfigs(prev => [...prev, newConfig])
    setCurrentIndex(configs.length)
  }, [configs])

  const removeConfig = useCallback((index) => {
    if (configs.length <= 1) return
    setConfigs(prev => {
      const next = prev.filter((_, i) => i !== index)
      return next
    })
    setCurrentIndex(prev => {
      if (prev >= configs.length - 1) return Math.max(0, configs.length - 2)
      if (prev > index) return prev - 1
      return Math.min(prev, configs.length - 2)
    })
    setDirection(-1)
  }, [configs.length])

  const handleCheckUpdates = async () => {
    setVersionChecking(true)
    setVersionInfo(null)
    try {
      const data = await api.checkForUpdates()
      setVersionInfo(data)
    } catch (e) {
      setVersionInfo({ current_version: '', latest_version: null, has_update: false, error: t.updateCheckFailed || '检查更新失败' })
    } finally {
      setVersionChecking(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    setSaved(false)
    setSaveError('')
    try {
      const payload = {
        configs: configs.map(c => ({
          api_key: c.api_key || '',
          base_url: c.base_url,
          model: c.model,
        })),
        active_index: currentIndex,
      }
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error('API settings save failed')
      const data = await res.json()
      const loaded = (data.configs && data.configs.length > 0)
        ? data.configs.map(c => ({
            api_key: '',
            base_url: c.base_url || '',
            model: c.model || '',
            has_key: c.has_key || false,
            masked_key: c.api_key || '',
          }))
        : configs
      setConfigs(loaded)
      setCurrentIndex(data.active_index ?? currentIndex)

      const updatedRecentLangs = [localUiLang, ...recentLangs.filter(code => code !== localUiLang)].slice(0, 5)
      await api.saveUserPreferences({
        retry_interval: retryInterval,
        target_lang: localUiLang,
        ui_lang: localUiLang,
        page_size: localPageSize,
        recent_languages: updatedRecentLangs,
        auto_update: autoUpdate,
      })

      if (onRecentLangsChange) {
        onRecentLangsChange(updatedRecentLangs)
      }

      if (onUiLangChange && localUiLang !== uiLang) {
        onUiLangChange(localUiLang)
      }

      if (onPageSizeChange && localPageSize !== pageSize) {
        onPageSizeChange(localPageSize)
      }

      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        onClose()
      }, 300)
    } catch (e) {
      console.error('Failed to save settings:', e)
      setSaveError(t.saveFailedDesc || '设置保存失败，请重试')
    } finally {
      setSaving(false)
    }
  }

  if (!isOpen) return null

  const current = configs[currentIndex]
  const isFirst = currentIndex === 0
  const isLast = currentIndex === configs.length - 1

  const sectionLabels = {
    api: t.settingsApi || 'API',
    general: t.settingsGeneral || '通用',
    nativeLang: t.settingsNativeLang || '母语',
  }

  const sectionIcons = {
    api: Key,
    general: Settings,
    nativeLang: Languages,
  }

  const renderApiSection = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-bold text-ink-500">
          {t.apiConfig || 'API 配置'} {currentIndex + 1}/{configs.length}
        </span>
        {configs.length > 1 && (
          <button
            onClick={() => removeConfig(currentIndex)}
            className="flex items-center gap-1 text-[10px] text-ink-400 hover:text-rust-500 transition-colors"
          >
            <Minus className="w-3 h-3" />
            {t.remove || 'Remove'}
          </button>
        )}
      </div>

      <div className="relative">
        <div className="flex items-center gap-1">
          <button
            onClick={goPrev}
            disabled={isFirst}
            className={`flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-sm transition-all ${
              isFirst
                ? 'text-aged-200 cursor-not-allowed'
                : 'text-ink-400 hover:text-ink-600 hover:bg-parchment-100 active:scale-90'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
          </button>

          <div className="flex-1 min-w-0 overflow-hidden rounded-sm border-2 border-aged-200 bg-parchment-50/50">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={currentIndex}
                custom={direction}
                initial={{ x: direction > 0 ? 80 : -80, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: direction > 0 ? -80 : 80, opacity: 0 }}
                transition={{ duration: 0.15, ease: 'easeInOut' }}
                className="p-3 space-y-3"
              >
                <div>
                  <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
                    <Key className="w-3 h-3" />
                    API Key
                    {current?.has_key && <span className="text-[10px] text-olive-500 normal-case tracking-normal">● {t.configured || '已配置'}</span>}
                  </label>
                  <input
                    type="password"
                    value={current?.api_key || ''}
                    onChange={e => updateConfig(currentIndex, 'api_key', e.target.value)}
                    placeholder={current?.masked_key || 'sk-...'}
                    className="input-warm w-full px-3 py-2 text-xs bg-parchment-50 border-2 border-aged-200 rounded-sm focus:outline-none focus:shadow-glow-amber focus:border-amber-300 transition-all placeholder:text-ink-400"
                  />
                  {current?.has_key && !current?.api_key && (
                    <p className="text-[11px] text-ink-400 mt-1">{t.leaveEmptyKeepKey || '留空则保持当前 Key 不变'}</p>
                  )}
                </div>

                <div>
                  <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
                    <Globe className="w-3 h-3" />
                    Base URL
                  </label>
                  <input
                    type="text"
                    value={current?.base_url || ''}
                    onChange={e => updateConfig(currentIndex, 'base_url', e.target.value)}
                    placeholder="https://api.siliconflow.cn/v1"
                    className="input-warm w-full px-3 py-2 text-xs bg-parchment-50 border-2 border-aged-200 rounded-sm focus:outline-none focus:shadow-glow-amber focus:border-amber-300 transition-all placeholder:text-ink-400"
                  />
                </div>

                <div>
                  <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
                    <Cpu className="w-3 h-3" />
                    Model
                  </label>
                  <input
                    type="text"
                    value={current?.model || ''}
                    onChange={e => updateConfig(currentIndex, 'model', e.target.value)}
                    placeholder="Qwen/Qwen3.6-27B"
                    className="input-warm w-full px-3 py-2 text-xs bg-parchment-50 border-2 border-aged-200 rounded-sm focus:outline-none focus:shadow-glow-amber focus:border-amber-300 transition-all placeholder:text-ink-400"
                  />
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {isLast ? (
            <button
              onClick={addConfig}
              className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-sm text-amber-500 hover:text-amber-500 hover:bg-amber-50 transition-all active:scale-90"
            >
              <Plus className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={goNext}
              className="flex-shrink-0 w-7 h-7 flex items-center justify-center rounded-sm text-ink-400 hover:text-ink-600 hover:bg-parchment-100 transition-all active:scale-90"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          )}
        </div>

        {configs.length > 1 && (
          <div className="flex items-center justify-center gap-1.5 mt-2.5">
            {configs.map((_, i) => (
              <button
                key={i}
                onClick={() => {
                  setDirection(i > currentIndex ? 1 : -1)
                  setCurrentIndex(i)
                }}
                className={`rounded-full transition-all duration-200 ${
                  i === currentIndex
                    ? 'w-4 h-1.5 bg-amber-400'
                    : 'w-1.5 h-1.5 bg-aged-300 hover:bg-ink-400'
                }`}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )

  const renderGeneralSection = () => (
    <div className="space-y-5">
      {/* Request Interval */}
      <div>
        <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
          <Gauge className="w-3 h-3" />
          {t.retryInterval || '请求间隔'}
        </label>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-ink-400">{t.retryIntervalDesc || '每次API请求之间的等待时间'}</span>
            <span className="text-[11px] font-bold text-amber-500">{retryInterval.toFixed(1)}s</span>
          </div>
          <div className="relative">
            <input
              type="range"
              min={0.1}
              max={20}
              step={0.1}
              value={retryInterval}
              onChange={e => setRetryInterval(Number(e.target.value))}
              className="w-full h-2 rounded-none appearance-none cursor-pointer bg-parchment-100"
              style={{
                background: `linear-gradient(to right, #C08A3A 0%, #C08A3A ${((retryInterval - 0.1) / (20 - 0.1)) * 100}%, #F5ECD7 ${((retryInterval - 0.1) / (20 - 0.1)) * 100}%, #F5ECD7 100%)`
              }}
            />
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-aged-300">0.1s</span>
              <span className="text-[10px] text-aged-300">20s</span>
            </div>
          </div>
        </div>
      </div>

      {/* Items Per Page */}
      <div>
        <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
          <BookOpen className="w-3 h-3" />
          {t.itemsPerPage || '每页数量'}
        </label>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-ink-400">{t.wordsPerPage || '每页显示单词数'}</span>
            <span className="text-[11px] font-bold text-amber-500">{localPageSize}</span>
          </div>
          <div className="relative">
            <input
              type="range"
              min={10}
              max={200}
              step={10}
              value={localPageSize}
              onChange={e => setLocalPageSize(Number(e.target.value))}
              className="w-full h-2 rounded-none appearance-none cursor-pointer bg-parchment-100"
              style={{
                background: `linear-gradient(to right, #C08A3A 0%, #C08A3A ${((localPageSize - 10) / (200 - 10)) * 100}%, #F5ECD7 ${((localPageSize - 10) / (200 - 10)) * 100}%, #F5ECD7 100%)`
              }}
            />
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-aged-300">10</span>
              <span className="text-[10px] text-aged-300">200</span>
            </div>
          </div>
        </div>
      </div>

      {/* Version Check */}
      <div className="pt-2 border-t border-aged-200/60">
        <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-3">
          <RefreshCw className="w-3 h-3" />
          {t.currentVersion || '当前版本'}
        </label>

        <div className="space-y-3">
          {/* Current version display */}
          {versionInfo?.current_version && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-ink-500">{t.currentVersion || '当前版本'}:</span>
              <span className="text-xs font-bold text-ink-800">v{versionInfo.current_version}</span>
              {versionInfo.has_update && (
                <span className="badge-ochre">{t.updateAvailable || '发现新版本'}</span>
              )}
            </div>
          )}

          {/* Check updates button */}
          <button
            onClick={handleCheckUpdates}
            disabled={versionChecking}
            className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-ink-600 bg-parchment-100 hover:bg-parchment-200 border-2 border-aged-200 rounded-sm transition-colors disabled:opacity-50"
          >
            {versionChecking ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <RefreshCw className="w-3.5 h-3.5" />
            )}
            {versionChecking ? (t.checkingForUpdates || '检查中...') : (t.checkForUpdates || '检查更新')}
          </button>

          {/* Version check result */}
          {versionInfo && !versionChecking && (
            <div className={`text-xs p-2.5 rounded-sm border-2 ${
              versionInfo.has_update
                ? 'bg-amber-50 border-amber-200 text-amber-700'
                : versionInfo.error
                  ? 'bg-rust-50 border-rust-200 text-rust-500'
                  : 'bg-olive-50 border-olive-200 text-olive-600'
            }`}>
              {versionInfo.has_update ? (
                <div className="space-y-1.5">
                  <p className="font-bold">{(t.updateAvailable || '发现新版本 {0}').replace('{0}', `v${versionInfo.latest_version}`)}</p>
                  {versionInfo.release_notes && (
                    <p className="text-[11px] opacity-80 line-clamp-3">{versionInfo.release_notes}</p>
                  )}
                  {versionInfo.download_url && (
                    <a
                      href={versionInfo.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-600 hover:text-amber-700 underline"
                    >
                      <Download className="w-3 h-3" />
                      {t.downloadUpdate || '下载更新'}
                    </a>
                  )}
                </div>
              ) : versionInfo.error ? (
                <p>{t.updateCheckFailed || '检查更新失败'}</p>
              ) : (
                <p>{t.noUpdateAvailable || '已是最新版本'}</p>
              )}
            </div>
          )}

          {/* Auto Update Toggle */}
          <div className="flex items-center justify-between py-1">
            <div>
              <p className="text-xs font-medium text-ink-700">{t.autoUpdate || '自动更新'}</p>
              <p className="text-[10px] text-ink-400">{t.autoUpdateDesc || '有新版本时自动下载并安装'}</p>
            </div>
            <button
              onClick={() => setAutoUpdate(v => !v)}
              className="transition-colors"
            >
              {autoUpdate ? (
                <ToggleRight className="w-8 h-5 text-amber-500" />
              ) : (
                <ToggleLeft className="w-8 h-5 text-aged-300" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )

  const renderNativeLangSection = () => (
    <div className="space-y-4">
      <div>
        <label className="label-warm flex items-center gap-1.5 text-[10px] font-bold text-ink-400 uppercase tracking-widest mb-1.5">
          <Languages className="w-3 h-3" />
          {t.nativeLang || '母语'}
        </label>
        <NativeLangSelector value={localUiLang} onChange={setLocalUiLang} recentLangs={recentLangs} />
        <p className="text-[10px] text-ink-400 mt-1.5">
          {t.retryIntervalDesc ? 'UI language and translation target language' : '界面语言和翻译目标语言'}
        </p>
      </div>
    </div>
  )

  const renderContent = () => {
    switch (activeSection) {
      case 'api': return renderApiSection()
      case 'general': return renderGeneralSection()
      case 'nativeLang': return renderNativeLangSection()
      default: return null
    }
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink-800/40 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          transition={{ duration: 0.15 }}
          className="bg-parchment-50 border-2 border-aged-200 rounded-md shadow-retro-xl w-[580px] max-h-[80vh] overflow-hidden flex flex-col"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-aged-200/80 bg-parchment-50/60 shrink-0">
            <div className="flex items-center gap-2.5">
              <Settings className="w-4 h-4 text-ink-500" />
              <h2 className="font-display text-sm font-bold text-ink-800">{t.settings || '设置'}</h2>
            </div>
            <button
              onClick={onClose}
              className="btn-ghost p-1 text-ink-400 hover:text-ink-600 rounded-md transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body: Sidebar + Content */}
          <div className="flex flex-1 min-h-0">
            {/* Left Sidebar */}
            <div className="w-[130px] shrink-0 border-r border-aged-200/60 bg-parchment-100/40 py-2">
              {SECTIONS.map(key => {
                const Icon = sectionIcons[key]
                const isActive = activeSection === key
                return (
                  <button
                    key={key}
                    onClick={() => setActiveSection(key)}
                    className={`w-full flex items-center gap-2 px-4 py-2.5 text-xs font-medium transition-colors text-left ${
                      isActive
                        ? 'bg-amber-50/80 text-amber-600 border-r-2 border-amber-400'
                        : 'text-ink-500 hover:text-ink-700 hover:bg-parchment-50/60'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    <span>{sectionLabels[key]}</span>
                  </button>
                )
              })}
            </div>

            {/* Right Content */}
            <div className="flex-1 min-w-0 overflow-y-auto p-5">
              {loading ? (
                <div className="py-12 flex justify-center">
                  <Loader2 className="w-5 h-5 animate-spin text-aged-300" />
                </div>
              ) : (
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeSection}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -10 }}
                    transition={{ duration: 0.15 }}
                  >
                    {renderContent()}
                  </motion.div>
                </AnimatePresence>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="shrink-0 border-t border-aged-200/80 bg-parchment-50/60 px-5 py-3">
            {/* Save Error */}
            {saveError && (
              <div className="flex items-center gap-2 mb-2 px-3 py-2 bg-rust-50 border-2 border-rust-200 rounded-sm">
                <AlertCircle className="w-3.5 h-3.5 text-rust-500 shrink-0" />
                <span className="text-[11px] text-rust-500">{saveError}</span>
              </div>
            )}
            <div className="flex items-center justify-end gap-2">
              <button
                onClick={onClose}
                className="btn-ghost px-4 py-2 text-xs"
              >
                {t.cancel || '取消'}
              </button>
              <motion.button
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={handleSave}
                disabled={saving}
                className="btn-primary px-5 py-2 text-xs flex items-center gap-2"
              >
                {saving ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : saved ? (
                  <Check className="w-3.5 h-3.5" />
                ) : null}
                {saving ? (t.saving || '保存中...') : saved ? (t.saved || '已保存') : (t.save || '保存')}
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default SettingsModal
