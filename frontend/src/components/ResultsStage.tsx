import {
  ArrowLeft,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  Info,
  Mail,
  Plus,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import type { Candidate, RequestItem, Subtask } from '../types'

type ResultsStageProps = {
  request: RequestItem
  selectedCandidateIds: string[]
  onToggleCandidate: (id: string) => void
  onBack: () => void
  onPrepareEmail: (candidate: Candidate, subtask: Subtask) => void
}

function sourceCount(candidate: Candidate) {
  return candidate.profile.publications.length + candidate.profile.grants.length
}

function role(candidate: Candidate) {
  const qualification = candidate.profile.degree || candidate.profile.position || 'Исследователь'
  return `${qualification} · ${candidate.profile.unit || 'ТюмГУ'}`
}

export function ResultsStage({
  request,
  selectedCandidateIds,
  onToggleCandidate,
  onBack,
  onPrepareEmail,
}: ResultsStageProps) {
  const defaultResult = request.results[1] ?? request.results[0]
  const [activeSubtaskId, setActiveSubtaskId] = useState(defaultResult?.subtask.id ?? 0)
  const [expandedCandidateId, setExpandedCandidateId] = useState<string | null>(null)

  useEffect(() => {
    const next = request.results[1] ?? request.results[0]
    setActiveSubtaskId(next?.subtask.id ?? 0)
    setExpandedCandidateId(null)
  }, [request.id, request.results])

  const activeResult = request.results.find((result) => result.subtask.id === activeSubtaskId)
    ?? request.results[0]
  const selectedCandidates = useMemo(() => activeResult?.candidates.filter(
    (candidate) => selectedCandidateIds.includes(candidate.profile.id),
  ) ?? [], [activeResult, selectedCandidateIds])

  if (!activeResult) {
    return <div className="results-stage results-stage--empty">
      <p>Результаты подбора пока не сформированы.</p>
      <button className="button button--secondary" type="button" onClick={onBack}>Вернуться к декомпозиции</button>
    </div>
  }

  return <div className="results-stage">
    <aside className="results-tasks" data-pencil-name="Подзадачи">
      <div className="results-tasks__heading">
        <h2>Подзадачи</h2>
        <p>Выберите задачу для просмотра кандидатов</p>
      </div>
      <div className="results-tasks__list">
        {request.results.map((result, index) => {
          const active = result.subtask.id === activeResult.subtask.id
          return <button
            className={`results-task${active ? ' is-active' : ''}`}
            type="button"
            onClick={() => {
              setActiveSubtaskId(result.subtask.id)
              setExpandedCandidateId(null)
            }}
            key={result.subtask.id}
          >
            <span className="results-task__meta">
              <span>{String(index + 1).padStart(2, '0')}</span>
              <small>{result.candidates.length} {result.candidates.length === 1 ? 'кандидат' : 'кандидатов'}</small>
            </span>
            <strong>{result.subtask.topic}</strong>
          </button>
        })}
      </div>
      <div className="results-tasks__spacer" />
      <div className="results-tasks__status">
        <span>ПОДЗАДАЧА {String(request.results.indexOf(activeResult) + 1).padStart(2, '0')}</span>
        <strong>Не назначена в работу</strong>
      </div>
      <button
        className="button button--white button--wide"
        data-node-id="C791O"
        type="button"
        onClick={onBack}
      >
        <ArrowLeft size={14} />
        Изменить декомпозицию задач
      </button>
    </aside>

    <section className="results-editor" data-pencil-name="Результаты по подзадаче">
      <div className="results-editor__heading">
        <div>
          <h1>{activeResult.subtask.topic}</h1>
          <p>Кандидаты ранжированы по соответствию задаче и данным их исследовательских профилей.</p>
        </div>
        <div className="results-editor__selection-summary">
          <strong>{selectedCandidates.length} из {activeResult.candidates.length} выбрано</strong>
          <span>состав экспертной группы</span>
        </div>
      </div>

      <div className="results-keywords">
        <strong>Ключевые слова подзадачи:</strong>
        {activeResult.subtask.keywords.map((keyword) => <span key={keyword}>{keyword}</span>)}
      </div>

      <div className="candidate-list">
        {activeResult.candidates.map((candidate) => {
          const selected = selectedCandidateIds.includes(candidate.profile.id)
          const expanded = expandedCandidateId === candidate.profile.id
          const sources = sourceCount(candidate)
          return <article className={`candidate-card${selected ? ' is-selected' : ''}`} key={candidate.profile.id}>
            <div className="candidate-card__row">
              <button
                className={`candidate-card__checkbox${selected ? ' is-selected' : ''}`}
                type="button"
                aria-label={selected ? 'Убрать кандидата из выбора' : 'Выбрать кандидата'}
                onClick={() => onToggleCandidate(candidate.profile.id)}
              >
                {selected && <Check size={14} />}
              </button>
              <span className="candidate-card__avatar" />
              <div className="candidate-card__person">
                <strong>{candidate.profile.full_name}</strong>
                <span>{role(candidate)}</span>
                <small>{sources || candidate.reasons.length} подтверждённых источника</small>
              </div>
              <div className="candidate-card__score">
                <strong>{candidate.score.toFixed(2)}</strong>
                <span>релевантность</span>
              </div>

              <button
                className="candidate-card__info"
                type="button"
                aria-label="Показать обоснование рекомендации"
                title="Обоснование рекомендации"
                aria-expanded={expanded}
                onClick={() => setExpandedCandidateId(expanded ? null : candidate.profile.id)}
              >
                <Info size={15} />
              </button>

              <button
                className="candidate-card__open"
                type="button"
                aria-label="Открыть карточку кандидата"
                title="Открыть карточку кандидата"
                onClick={() => onPrepareEmail(candidate, activeResult.subtask)}
              >
                <ChevronRight size={15} />
              </button>

            </div>
            {expanded && <div className="candidate-card__reasons">
              {candidate.reasons.map((reason, index) => <p key={`${candidate.profile.id}-${index}`}>
                <span>{String(index + 1).padStart(2, '0')}</span>
                {reason}
              </p>)}
            </div>}
          </article>
        })}
      </div>

      <button className="add-candidate" type="button">
        <Plus size={14} />
        Добавить сотрудника
      </button>

      <div className="results-editor__footer">
        <button className="button button--secondary" type="button">
          <BriefcaseBusiness size={14} />
          В работу
        </button>
        <button
          className="button button--primary"
          type="button"
          disabled={selectedCandidates.length === 0}
          onClick={() => {
            const firstSelectedCandidate = selectedCandidates[0]
            if (firstSelectedCandidate) onPrepareEmail(firstSelectedCandidate, activeResult.subtask)
          }}
        >
          Разослать письма · {selectedCandidates.length}
          <Mail size={14} />
        </button>
      </div>
    </section>
  </div>
}
