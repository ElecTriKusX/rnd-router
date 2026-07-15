import { ArrowLeft, Check, Info, LoaderCircle, WandSparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { Candidate, RequestItem, Subtask } from '../types'

export type CandidateFact = {
  id: string
  category: 'Гранты' | 'Исследования' | 'Статьи'
  meta: string
  title: string
}

export function buildCandidateFacts(candidate: Candidate): CandidateFact[] {
  const grants: CandidateFact[] = candidate.profile.grants.map((grant, index) => ({
    id: `grant-${index}`,
    category: 'Гранты',
    meta: `Грант${grant.years ? ` · ${grant.years}` : ''}`,
    title: grant.title,
  }))
  const research: CandidateFact[] = candidate.reasons.map((reason, index) => ({
    id: `reason-${index}`,
    category: 'Исследования',
    meta: 'Обоснование рекомендации',
    title: reason,
  }))
  const publications: CandidateFact[] = candidate.profile.publications.map((publication, index) => ({
    id: `publication-${index}`,
    category: 'Статьи',
    meta: `Статья${publication.year ? ` · ${publication.year}` : ''}`,
    title: publication.title,
  }))
  return [...grants, ...research, ...publications]
}

type EmailPreparationStageProps = {
  request: RequestItem
  candidate: Candidate
  subtask: Subtask
  selectedFactIds: string[]
  instruction: string
  loading: boolean
  error: string
  onSelectFacts: (ids: string[]) => void
  onInstruction: (value: string) => void
  onBack: () => void
  onCreateDraft: (facts: CandidateFact[]) => void
}

const categories = ['Все', 'Гранты', 'Исследования', 'Статьи'] as const

export function EmailPreparationStage({
  request,
  candidate,
  subtask,
  selectedFactIds,
  instruction,
  loading,
  error,
  onSelectFacts,
  onInstruction,
  onBack,
  onCreateDraft,
}: EmailPreparationStageProps) {
  const [category, setCategory] = useState<(typeof categories)[number]>('Все')
  const facts = useMemo(() => buildCandidateFacts(candidate), [candidate])
  const visibleFacts = category === 'Все' ? facts : facts.filter((fact) => fact.category === category)
  const subtaskIndex = request.subtasks.findIndex((item) => item.id === subtask.id)

  const toggleFact = (id: string) => {
    onSelectFacts(selectedFactIds.includes(id)
      ? selectedFactIds.filter((factId) => factId !== id)
      : [...selectedFactIds, id])
  }

  return <div className="email-preparation-stage">
    <aside className="recommendation-panel" data-pencil-name="Обоснование рекомендации">
      <div className="recommendation-panel__heading">
        <h2>Обоснование рекомендации</h2>
        <p>Сформировано ИИ на основе заявки и профиля кандидата</p>
      </div>
      <div className="recommendation-context">
        <span>ПОДЗАДАЧА {String(Math.max(0, subtaskIndex) + 1).padStart(2, '0')}</span>
        <strong>{subtask.topic}</strong>
        <div className="recommendation-context__score">
          <span>РЕЛЕВАНТНОСТЬ <Info size={13} /></span>
          <strong>{candidate.score.toFixed(2)}</strong>
        </div>
      </div>
      <div className="recommendation-factors">
        {candidate.reasons.map((reason, index) => <div className="recommendation-factor" key={`${candidate.profile.id}-${index}`}>
          <span>{String(index + 1).padStart(2, '0')}</span>
          <p>{reason}</p>
        </div>)}
      </div>
      <div className="recommendation-panel__spacer" />
      <button className="button button--white button--wide" type="button" onClick={onBack}>
        <ArrowLeft size={14} />
        Вернуться к результатам подбора
      </button>
    </aside>

    <section className="facts-editor" data-pencil-name="Факты кандидата и инструкция">
      <div className="facts-editor__heading">
        <div>
          <h1>{candidate.profile.full_name}</h1>
          <p>Факты для индивидуального письма</p>
        </div>
        <div className="facts-editor__heading-actions">
          <span>Выбрано: {selectedFactIds.length}</span>
          <button type="button"><Info size={13} />Подробнее</button>
        </div>
      </div>

      <div className="fact-categories">
        {categories.map((item) => {
          const count = item === 'Все' ? facts.length : facts.filter((fact) => fact.category === item).length
          return <button
            className={category === item ? 'is-active' : ''}
            type="button"
            onClick={() => setCategory(item)}
            key={item}
          >
            {item} · {count}
          </button>
        })}
      </div>

      <span className="facts-editor__label">ВЫБЕРИТЕ ФАКТЫ ДЛЯ ГЕНЕРАЦИИ ПИСЬМА КАНДИДАТУ</span>
      <div className="facts-catalog">
        {visibleFacts.map((fact, index) => {
          const selected = selectedFactIds.includes(fact.id)
          const showHeading = index === 0 || visibleFacts[index - 1]?.category !== fact.category
          const categoryCount = facts.filter((item) => item.category === fact.category).length
          return <div className="fact-group-item" key={fact.id}>
            {showHeading && <div className="fact-group-item__heading">
              <strong>{fact.category.toLocaleUpperCase('ru')}</strong>
              <span>{categoryCount} {categoryCount === 1 ? 'запись' : 'записи'}</span>
            </div>}
            <button
              className={`fact-card${selected ? ' is-selected' : ''}`}
              type="button"
              onClick={() => toggleFact(fact.id)}
            >
              <span className={`fact-card__checkbox${selected ? ' is-selected' : ''}`}>
                {selected && <Check size={13} />}
              </span>
              <span className="fact-card__copy">
                <small>{fact.meta}</small>
                <strong>{fact.title}</strong>
              </span>
              <span className="fact-card__source">↗</span>
            </button>
          </div>
        })}
        {visibleFacts.length === 0 && <p className="facts-catalog__empty">В этой категории пока нет фактов.</p>}
      </div>

      <label className="email-instruction" data-node-id="ieArj">
        <span>Дополнительная инструкция для письма</span>
        <textarea
          value={instruction}
          onChange={(event) => onInstruction(event.target.value)}
          placeholder="Например: предложить короткую онлайн-встречу"
        />
      </label>

      {error && <div className="email-preparation-error" role="alert">{error}</div>}
      <div className="email-preparation-actions">
        <div className="project-participant">
          <span>Участник входит в проект</span>
          <span className="toggle-on"><span /></span>
        </div>
        <button
          className="button button--primary email-preparation-actions__create"
          type="button"
          disabled={selectedFactIds.length === 0 || loading}
          onClick={() => onCreateDraft(facts.filter((fact) => selectedFactIds.includes(fact.id)))}
        >
          {loading && <LoaderCircle className="button__spinner" size={14} />}
          <WandSparkles size={14} />
          {loading ? 'Создаём черновик…' : 'Создать черновик письма'}
        </button>
      </div>
    </section>
  </div>
}
