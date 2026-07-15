import { FormEvent, ReactNode, useMemo, useState } from 'react'
import {
  ArrowLeft, ArrowRight, Check, ChevronRight, CircleHelp, Clock3, FileText, Files,
  LoaderCircle, Mail, PanelLeftClose, PanelLeftOpen, Pencil, Plus, Search,
  Settings2, SlidersHorizontal, Sparkles, UsersRound, X,
} from 'lucide-react'
import { Candidate, createEmailDraft, decompose, EmailDraft, findMatches, MatchResult, Subtask } from './api'

type Screen = 'request' | 'decomposition' | 'results' | 'compose' | 'draft'
type RequestItem = {
  id: string
  title: string
  company: string
  tags: string[]
  description: string
  stage: 0 | 1 | 2 | 3
  subtasks?: Subtask[]
  matches?: MatchResult[]
  emailDraft?: EmailDraft
}

const initialRequests: RequestItem[] = [
  {
    id: 'CRM-04871', title: 'Каталитические системы для пилотного процесса', company: 'ООО «ТехКатализ»',
    tags: ['гетерогенный катализ', 'пилотный процесс', 'кинетика'], stage: 1,
    description: 'Заказчик рассматривает запуск пилотного процесса получения функциональных материалов. Требуется оценить применимость каталитических систем, подходы к кинетическому моделированию и ограничения при масштабировании.\n\nНужна консультация специалистов по гетерогенному катализу и селективному окислению. Ожидаемый результат — предложение по составу экспертной группы и первичная оценка направлений НИОКР.',
  },
  { id: 'CRM-04858', title: 'Материалы для полимерного производства', company: 'АО «Полимер»', tags: ['полимеры', 'материалы'], stage: 1, description: 'Требуется экспертная оценка материалов для производства.' },
  { id: 'CRM-04843', title: 'Биотехнологическое сопровождение анализа', company: 'БиоЛаб', tags: ['биотехнологии', 'анализ'], stage: 1, description: 'Запрос на биотехнологическое сопровождение.' },
  { id: 'CRM-04831', title: 'Мониторинг экологического воздействия', company: 'ЭкоСфера', tags: ['экология', 'мониторинг'], stage: 1, description: 'Нужна консультация по мониторингу воздействия.' },
]

const factsFor = (candidate?: Candidate) => {
  if (!candidate) return []
  const publications = candidate.profile.publications?.slice(0, 2).map((item) => `Публикация: ${item.title}`) ?? []
  const grants = candidate.profile.grants?.slice(0, 2).map((item) => `Грант: ${item.title}`) ?? []
  return [...candidate.reasons, `${candidate.profile.unit}${candidate.profile.position ? ` · ${candidate.profile.position}` : ''}`, ...publications, ...grants]
}

const stageText = (stage: number) => stage === 0 ? 'Новая' : `${stage}/3`

function requestPayload(item: RequestItem) {
  return { title: item.title.trim(), description: item.description.trim() }
}

export function App() {
  const [items, setItems] = useState(initialRequests)
  const [selectedId, setSelectedId] = useState(initialRequests[0].id)
  const [screen, setScreen] = useState<Screen>('request')
  const [collapsed, setCollapsed] = useState(false)
  const [query, setQuery] = useState('')
  const [saving, setSaving] = useState(false)
  const [loading, setLoading] = useState<'decompose' | 'matches' | 'draft' | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [newTag, setNewTag] = useState('')
  const [tagMode, setTagMode] = useState(false)
  const [editSubtask, setEditSubtask] = useState<Subtask | null>(null)
  const [selectedSubtask, setSelectedSubtask] = useState(0)
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)
  const [selectedFacts, setSelectedFacts] = useState<string[]>([])
  const [instruction, setInstruction] = useState('Упомянуть возможность короткой онлайн-встречи и уточнить удобный формат связи.')

  const selected = items.find((item) => item.id === selectedId) ?? items[0]
  const filtered = useMemo(() => items.filter((item) => item.title.toLocaleLowerCase().includes(query.toLocaleLowerCase())), [items, query])
  const currentMatches = selected.matches?.[selectedSubtask] ?? selected.matches?.[0]
  const activeCandidate = selectedCandidate ?? currentMatches?.candidates[0]
  const facts = factsFor(activeCandidate)

  const updateSelected = (updater: (item: RequestItem) => RequestItem) => {
    setItems((previous) => previous.map((item) => item.id === selected.id ? updater(item) : item))
  }

  const invalidateFromRequest = () => updateSelected((item) => ({ ...item, stage: 1, subtasks: undefined, matches: undefined, emailDraft: undefined }))

  const createRequest = () => {
    const id = `CRM-${String(Math.floor(10000 + Math.random() * 90000))}`
    const item: RequestItem = { id, title: 'Новая заявка', company: 'Не указан', tags: [], description: '', stage: 0 }
    setItems((previous) => [item, ...previous])
    setSelectedId(id)
    setScreen('request')
    setError(null)
  }

  const saveRequest = () => {
    setSaving(true)
    setTimeout(() => {
      updateSelected((item) => ({ ...item, stage: 1, subtasks: undefined, matches: undefined, emailDraft: undefined }))
      setSaving(false)
    }, 300)
  }

  const addTag = (event: FormEvent) => {
    event.preventDefault()
    const tag = newTag.trim()
    if (!tag || selected.tags.includes(tag)) return
    updateSelected((item) => ({ ...item, tags: [...item.tags, tag] }))
    setNewTag('')
    setTagMode(false)
    invalidateFromRequest()
  }

  const runDecompose = async () => {
    if (!selected.title.trim() || !selected.description.trim()) {
      setError('Заполните краткое название и текст заявки перед декомпозицией.')
      return
    }
    if (selected.stage >= 2 && selected.subtasks) {
      setScreen('decomposition')
      return
    }
    setLoading('decompose'); setError(null)
    try {
      const response = await decompose(requestPayload(selected))
      updateSelected((item) => ({ ...item, stage: 2, subtasks: response.subtasks, matches: undefined, emailDraft: undefined }))
      setSelectedSubtask(0)
      setScreen('decomposition')
    } catch (cause) {
      setError(`Не удалось получить декомпозицию. ${cause instanceof Error ? cause.message : ''}`)
    } finally { setLoading(null) }
  }

  const changeSubtasks = (subtasks: Subtask[]) => {
    updateSelected((item) => ({ ...item, stage: 2, subtasks, matches: undefined, emailDraft: undefined }))
  }

  const saveSubtask = (event: FormEvent) => {
    event.preventDefault()
    if (!editSubtask) return
    const subtasks = (selected.subtasks ?? []).map((item) => item.id === editSubtask.id ? editSubtask : item)
    changeSubtasks(subtasks)
    setEditSubtask(null)
  }

  const addSubtask = () => {
    const subtasks = selected.subtasks ?? []
    const created = { id: Math.max(0, ...subtasks.map((item) => item.id)) + 1, topic: 'Новая подзадача', keywords: ['ключевое слово'] }
    changeSubtasks([...subtasks, created])
    setEditSubtask(created)
  }

  const runMatches = async () => {
    if (selected.stage === 3 && selected.matches) { setScreen('results'); return }
    if (!selected.subtasks?.length) return
    setLoading('matches'); setError(null)
    try {
      const response = await findMatches(requestPayload(selected), selected.subtasks)
      updateSelected((item) => ({ ...item, stage: 3, matches: response.results, emailDraft: undefined }))
      setSelectedSubtask(0); setSelectedCandidate(response.results[0]?.candidates[0] ?? null); setScreen('results')
    } catch (cause) {
      setError(`Не удалось получить результаты подбора. ${cause instanceof Error ? cause.message : ''}`)
    } finally { setLoading(null) }
  }

  const openCompose = () => {
    const candidate = activeCandidate
    if (!candidate) return
    setSelectedCandidate(candidate)
    setSelectedFacts(factsFor(candidate).slice(0, 3))
    setScreen('compose')
  }

  const runDraft = async () => {
    if (!activeCandidate) return
    setLoading('draft'); setError(null)
    try {
      const response = await createEmailDraft(requestPayload(selected), activeCandidate)
      updateSelected((item) => ({ ...item, emailDraft: response }))
      setScreen('draft')
    } catch (cause) {
      setError(`Не удалось создать черновик. ${cause instanceof Error ? cause.message : ''}`)
    } finally { setLoading(null) }
  }

  return <div className="app-shell">
    <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />
    <main className="workspace">
      <Progress active={screen === 'request' ? 1 : screen === 'decomposition' ? 2 : 3} completed={selected.stage} />
      {error && <div className="alert"><CircleHelp size={17} /> <span>{error}</span><button aria-label="Закрыть" onClick={() => setError(null)}><X size={16} /></button></div>}
      {screen === 'request' && <RequestScreen {...{ selected, filtered, query, setQuery, setSelectedId, createRequest, updateSelected, saveRequest, saving, tagMode, setTagMode, newTag, setNewTag, addTag, runDecompose, loading }} />}
      {screen === 'decomposition' && <DecompositionScreen {...{ selected, changeSubtasks, setEditSubtask, addSubtask, runMatches, loading, goBack: () => setScreen('request') }} />}
      {screen === 'results' && <ResultsScreen {...{ selected, selectedSubtask, setSelectedSubtask, selectedCandidate: activeCandidate, setSelectedCandidate, openCompose, goBack: () => setScreen('decomposition') }} />}
      {screen === 'compose' && <ComposeScreen {...{ selected, candidate: activeCandidate, facts, selectedFacts, setSelectedFacts, instruction, setInstruction, runDraft, loading, goBack: () => setScreen('results') }} />}
      {screen === 'draft' && <DraftScreen draft={selected.emailDraft} candidate={activeCandidate} facts={selectedFacts} instruction={instruction} goFacts={() => setScreen('compose')} goResults={() => setScreen('results')} />}
    </main>
    {editSubtask && <SubtaskModal subtask={editSubtask} onChange={setEditSubtask} onClose={() => setEditSubtask(null)} onSave={saveSubtask} />}
  </div>
}

function Sidebar({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) {
  const navigation = [[Sparkles, 'Подбор экспертов'], [Files, 'Все заявки'], [Clock3, 'История заявок'], [UsersRound, 'Эксперты'], [Settings2, 'Настройки']] as const
  return <aside className={`sidebar ${collapsed ? 'sidebar--collapsed' : ''}`}>
    <div className="brand-mark">ТюмГУ</div>
    {!collapsed && <div className="brand-copy"><span>НИОКР · ТЮМГУ</span><strong>Маршрутизатор<br />НИОКР</strong></div>}
    <nav>{navigation.map(([Icon, label], index) => <button className={index === 0 ? 'nav-item nav-item--active' : 'nav-item'} key={label} title={label}><Icon size={18} /><span>{label}</span></button>)}</nav>
    <div className="sidebar-bottom">
      <div className="profile"><b>ВП</b>{!collapsed && <span><strong>Валерия Петрова</strong><small>Менеджер НИОКР</small></span>}</div>
      <button className="collapse" onClick={onToggle}>{collapsed ? <PanelLeftOpen size={15} /> : <><PanelLeftClose size={15} /><span>Свернуть</span></>}</button>
    </div>
  </aside>
}

function Progress({ active, completed }: { active: number; completed: number }) {
  const steps = [['Новая заявка', 'Редактирование'], ['Декомпозиция', 'Проверка задач'], ['Результаты', 'Экспертные досье']]
  return <header className="progress">{steps.map(([name, caption], index) => <div className="progress-group" key={name}>
    <div className={`progress-step ${active === index + 1 ? 'progress-step--active' : ''} ${completed >= index + 1 ? 'progress-step--done' : ''}`}><span>{completed > index + 1 ? <Check size={15} /> : index + 1}</span><div><strong>{name}</strong><small>{caption}</small></div></div>{index < 2 && <i />}
  </div>)}</header>
}

function RequestScreen(props: any) {
  const { selected, filtered, query, setQuery, setSelectedId, createRequest, updateSelected, saveRequest, saving, tagMode, setTagMode, newTag, setNewTag, addTag, runDecompose, loading } = props
  return <section className="stage-content request-layout">
    <aside className="request-list panel"><div className="panel-heading"><div><h2>Заявки CRM</h2><p>Входящие обращения</p></div><button className="icon-button icon-button--primary" title="Добавить новую заявку" onClick={createRequest}><Plus size={17} /></button></div>
      <label className="search"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Найти заявку" /></label>
      <div className="request-cards">{filtered.map((item: RequestItem) => <button key={item.id} className={`request-card ${item.id === selected.id ? 'request-card--selected' : ''}`} onClick={() => setSelectedId(item.id)}><div><code>{item.id}</code><Status stage={item.stage} /></div><strong>{item.title}</strong><p>{item.company}</p><span>{item.tags.slice(0, 2).map((tag) => <em key={tag}>{tag}</em>)}</span></button>)}</div>
    </aside>
    <section className="panel request-editor"><div className="editor-heading"><div><h1>{selected.stage === 0 ? 'Новая заявка' : selected.title}</h1><p>Проверьте и уточните данные перед переходом к декомпозиции.</p></div><span className="crm-badge">Источник CRM</span></div>
      <Field label="Краткое название"><input value={selected.title} onChange={(event) => updateSelected((item: RequestItem) => ({ ...item, title: event.target.value }))} /></Field>
      <Field label="Текст заявки"><textarea value={selected.description} onChange={(event) => updateSelected((item: RequestItem) => ({ ...item, description: event.target.value }))} /></Field>
      <div className="tags-section"><div><strong>Метки для фильтрации</strong><small>для быстрого поиска заявки</small></div><div className="tags">{selected.tags.map((tag: string) => <button key={tag} className="tag" onClick={() => { updateSelected((item: RequestItem) => ({ ...item, tags: item.tags.filter((value) => value !== tag) })); }}>{tag}<X size={12} /></button>)}
        {tagMode ? <form className="tag-form" onSubmit={addTag}><input autoFocus value={newTag} onChange={(event) => setNewTag(event.target.value)} placeholder="Новый тег" /><button>Добавить</button></form> : <button className="tag tag--new" onClick={() => setTagMode(true)}><Plus size={13} />Создать тег</button>}</div></div>
      <div className="actions"><small>Изменения сохраняются только в текущем окне браузера.</small><div><button className="button button--secondary" onClick={saveRequest} disabled={saving}>{saving ? 'Сохранение…' : 'Сохранить изменения'}</button><button className="button button--primary" onClick={runDecompose} disabled={loading === 'decompose'}>{loading === 'decompose' ? <LoaderCircle className="spin" size={15} /> : null}{selected.stage >= 2 ? 'Далее' : 'Перейти к декомпозиции'}<ArrowRight size={15} /></button></div></div>
    </section>
  </section>
}

function DecompositionScreen({ selected, setEditSubtask, addSubtask, runMatches, loading, goBack }: any) {
  const subtasks: Subtask[] = selected.subtasks ?? []
  return <section className="stage-content split-layout"><RequestContext selected={selected} onBack={goBack} label="Изменить исходную заявку" />
    <section className="panel decomposition"><div className="editor-heading"><div><h1>Декомпозиция на подзадачи</h1><p>Проверьте предложения ИИ и отредактируйте состав работ перед подбором экспертов.</p></div><span className="ai-badge"><Sparkles size={14} />Черновик ИИ</span></div>
      <div className="hint"><CircleHelp size={16} />Состав и формулировки подзадач можно менять. В подбор попадут только подтверждённые менеджером записи.</div>
      <div className="subtask-list">{subtasks.map((subtask) => <article className="subtask-card" key={subtask.id}><b>{String(subtask.id).padStart(2, '0')}</b><div><h3>{subtask.topic}</h3><span>{subtask.keywords.map((word) => <em key={word}>{word}</em>)}</span></div><button className="text-button" onClick={() => setEditSubtask(subtask)}><Pencil size={13} />Изменить</button></article>)}</div>
      <button className="add-row" onClick={addSubtask}><Plus size={16} />Добавить подзадачу</button>
      <div className="actions"><small>{subtasks.length} {subtasks.length === 1 ? 'подзадача подготовлена' : 'подзадачи подготовлены'} к подбору.</small><button className="button button--primary" onClick={runMatches} disabled={loading === 'matches'}>{loading === 'matches' ? <LoaderCircle className="spin" size={15} /> : null}{selected.stage === 3 ? 'Далее' : 'Перейти к результатам'}<ArrowRight size={15} /></button></div>
    </section>
  </section>
}

function ResultsScreen({ selected, selectedSubtask, setSelectedSubtask, selectedCandidate, setSelectedCandidate, openCompose, goBack }: any) {
  const matches: MatchResult[] = selected.matches ?? []
  const current = matches[selectedSubtask] ?? matches[0]
  return <section className="stage-content split-layout"><aside className="subtask-nav panel"><h2>Подзадачи</h2>{matches.map((item, index) => <button key={item.subtask.id} className={index === selectedSubtask ? 'subtask-nav__item subtask-nav__item--active' : 'subtask-nav__item'} onClick={() => { setSelectedSubtask(index); setSelectedCandidate(item.candidates[0] ?? null) }}><code>{String(index + 1).padStart(2, '0')}</code><span>{item.subtask.topic}</span></button>)}<div className="subtask-nav__bottom"><Status stage={selected.stage} /><button className="button button--secondary" onClick={goBack}><ArrowLeft size={15} />Изменить декомпозицию задач</button></div></aside>
    <section className="panel results"><div className="editor-heading"><div><h1>{current?.subtask.topic ?? 'Результаты подбора'}</h1><p>Кандидаты, релевантные выбранной подзадаче.</p></div><span className="selected-count">{current?.candidates.length ?? 0} найдено</span></div>{current && <div className="keyword-strip"><strong>Ключевые слова подзадачи:</strong>{current.subtask.keywords.map((word) => <em key={word}>{word}</em>)}</div>}
      <div className="candidate-list">{current?.candidates.map((candidate) => <CandidateCard candidate={candidate} key={candidate.profile.id} selected={selectedCandidate?.profile.id === candidate.profile.id} onSelect={() => setSelectedCandidate(candidate)} />)}</div>
      <div className="actions"><small>Выберите сотрудника, чтобы подготовить персональное письмо.</small><button className="button button--primary" onClick={openCompose} disabled={!selectedCandidate}>Подготовить письмо<Mail size={15} /></button></div>
    </section></section>
}

function ComposeScreen({ candidate, facts, selectedFacts, setSelectedFacts, instruction, setInstruction, runDraft, loading, goBack }: any) {
  const toggle = (fact: string) => setSelectedFacts((current: string[]) => current.includes(fact) ? current.filter((item) => item !== fact) : [...current, fact])
  return <section className="stage-content split-layout"><aside className="reason-panel panel"><h2>Обоснование рекомендации</h2>{candidate && <><div className="context-card"><code>РЕЛЕВАНТНОСТЬ</code><strong>{candidate.score.toFixed(2)}</strong><p>{candidate.profile.full_name}</p></div><ol>{candidate.reasons.map((reason: string) => <li key={reason}>{reason}</li>)}</ol></>}<button className="button button--secondary" onClick={goBack}><ArrowLeft size={15} />Вернуться к результатам</button></aside>
    <section className="panel compose"><div className="editor-heading"><div><h1>Факты для письма</h1><p>{candidate?.profile.full_name ?? 'Выберите кандидата'} · отметьте информацию, которую нужно использовать.</p></div><span className="selected-count">{selectedFacts.length} выбрано</span></div><p className="eyebrow">ВЫБЕРИТЕ ФАКТЫ ДЛЯ ГЕНЕРАЦИИ ПИСЬМА КАНДИДАТУ</p><div className="fact-list">{facts.map((fact: string) => <label key={fact} className={selectedFacts.includes(fact) ? 'fact fact--selected' : 'fact'}><input type="checkbox" checked={selectedFacts.includes(fact)} onChange={() => toggle(fact)} /><span>{fact}</span></label>)}</div>
      <Field label="Дополнительная инструкция для письма"><textarea className="instruction" value={instruction} onChange={(event) => setInstruction(event.target.value)} /></Field><div className="actions"><small>Факты и инструкция подготовлены для сценария генерации.</small><button className="button button--primary" onClick={runDraft} disabled={loading === 'draft' || !candidate}>{loading === 'draft' ? <LoaderCircle className="spin" size={15} /> : <Sparkles size={15} />}Создать черновик письма</button></div>
    </section></section>
}

function DraftScreen({ draft, candidate, facts, instruction, goFacts, goResults }: any) {
  return <section className="stage-content split-layout"><aside className="draft-context panel"><h2>Факты, использованные в черновике</h2><strong>{candidate?.profile.full_name}</strong><ul>{facts.map((fact: string) => <li key={fact}>{fact}</li>)}</ul><div className="context-card"><small>ИНСТРУКЦИЯ</small><p>{instruction}</p></div><button className="button button--secondary" onClick={goFacts}><SlidersHorizontal size={15} />Изменить факты</button><button className="button button--secondary" onClick={goResults}><ArrowLeft size={15} />Вернуться к результатам</button></aside>
    <section className="panel email"><div className="email-heading"><div><h1>Черновик письма</h1><p>Сформировано на основе выбранных фактов</p></div><span className="ai-badge"><Sparkles size={14} />ИИ-черновик</span></div><div className="email-field"><small>КОМУ</small><strong>{draft?.to ?? candidate?.profile.email ?? 'Не указан'}</strong></div><div className="email-field"><small>ТЕМА</small><strong>{draft?.subject ?? 'Черновик письма'}</strong></div><article className="email-body">{draft?.body ?? 'Черновик не был сформирован.'}</article><div className="actions"><small>Отправка писем не входит в демонстрационный сценарий.</small><button className="button button--secondary" onClick={() => navigator.clipboard?.writeText(draft?.body ?? '')}>Скопировать текст</button></div></section>
  </section>
}

function CandidateCard({ candidate, selected, onSelect }: { candidate: Candidate; selected: boolean; onSelect: () => void }) {
  const initials = candidate.profile.full_name.split(' ').map((part) => part[0]).slice(0, 2).join('')
  return <button className={selected ? 'candidate candidate--selected' : 'candidate'} onClick={onSelect}><span className="checkmark">{selected && <Check size={14} />}</span><span className="avatar">{initials}</span><span className="candidate-copy"><strong>{candidate.profile.full_name}</strong><small>{[candidate.profile.degree, candidate.profile.unit].filter(Boolean).join(' · ')}</small><small>{candidate.reasons.length} подтверждённых основания</small></span><span className="score"><b>{candidate.score.toFixed(2)}</b><small>релевантность</small></span><ChevronRight size={17} /></button>
}

function RequestContext({ selected, onBack, label }: { selected: RequestItem; onBack: () => void; label: string }) {
  return <aside className="request-context panel"><code>ЗАЯВКА {selected.id}</code><h2>{selected.title}</h2><p>{selected.company}</p><hr /><strong>Исходный запрос</strong><p>{selected.description}</p><button className="button button--secondary" onClick={onBack}><ArrowLeft size={15} />{label}</button></aside>
}

function SubtaskModal({ subtask, onChange, onClose, onSave }: { subtask: Subtask; onChange: (item: Subtask) => void; onClose: () => void; onSave: (event: FormEvent) => void }) {
  return <div className="modal-backdrop"><form className="modal" onSubmit={onSave}><div><h2>Редактировать подзадачу</h2><button type="button" className="plain-button" onClick={onClose}><X /></button></div><Field label="Название"><input autoFocus value={subtask.topic} onChange={(event) => onChange({ ...subtask, topic: event.target.value })} /></Field><Field label="Ключевые слова через запятую"><input value={subtask.keywords.join(', ')} onChange={(event) => onChange({ ...subtask, keywords: event.target.value.split(',').map((word) => word.trim()).filter(Boolean) })} /></Field><div className="modal-actions"><button type="button" className="button button--secondary" onClick={onClose}>Отмена</button><button className="button button--primary">Сохранить</button></div></form></div>
}

function Field({ label, children }: { label: string; children: ReactNode }) { return <label className="field"><strong>{label}</strong>{children}</label> }
function Status({ stage }: { stage: number }) { return <span className={`status status--${stage}`}>{stageText(stage)}</span> }
