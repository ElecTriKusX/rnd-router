import {
  ArrowLeft,
  ArrowRight,
  CircleAlert,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
  X,
} from 'lucide-react'
import { FormEvent, useEffect, useState } from 'react'
import type { RequestItem, Subtask } from '../types'

type DecompositionStageProps = {
  request: RequestItem
  loading: boolean
  error: string
  onBack: () => void
  onChange: (subtasks: Subtask[]) => void
  onContinue: () => void
}

type EditState = {
  id: number
  topic: string
  keywords: string[]
}

function nextSubtaskId(subtasks: Subtask[]) {
  return subtasks.reduce((maximum, subtask) => Math.max(maximum, subtask.id), 0) + 1
}

export function DecompositionStage({
  request,
  loading,
  error,
  onBack,
  onChange,
  onContinue,
}: DecompositionStageProps) {
  const [editing, setEditing] = useState<EditState | null>(null)

  useEffect(() => setEditing(null), [request.id])

  const openEditor = (subtask: Subtask) => {
    setEditing({ ...subtask, keywords: [...subtask.keywords] })
  }

  const addSubtask = () => {
    const subtask: Subtask = {
      id: nextSubtaskId(request.subtasks),
      topic: 'Новая подзадача',
      keywords: [],
    }
    onChange([...request.subtasks, subtask])
    openEditor(subtask)
  }

  const saveEdit = () => {
    if (!editing?.topic.trim()) return
    onChange(request.subtasks.map((subtask) => subtask.id === editing.id
      ? {
          ...subtask,
          topic: editing.topic.trim(),
          keywords: editing.keywords.map((keyword) => keyword.trim()).filter(Boolean),
        }
      : subtask))
    setEditing(null)
  }

  const hasResults = request.status !== 'new' && request.status >= 3 && request.results.length > 0

  return <div className="decomposition-stage">
    <aside className="request-context" data-pencil-name="Контекст заявки">
      <div className="request-context__heading">
        <span>ЗАЯВКА {request.id}</span>
        <h2>{request.title}</h2>
        <p>{request.company}</p>
      </div>
      <div className="divider" />
      <strong className="request-context__label">Исходный запрос</strong>
      <p className="request-context__text">{request.description}</p>
      <div className="request-context__spacer" />
      <button
        className="button button--white button--wide"
        data-node-id="dcmyJ"
        type="button"
        onClick={onBack}
      >
        <ArrowLeft size={14} />
        Изменить исходную заявку
      </button>
    </aside>

    <section className="decomposition-editor" data-pencil-name="Редактор декомпозиции">
      <div className="decomposition-editor__heading">
        <div>
          <h1>Декомпозиция на подзадачи</h1>
          <p>Проверьте предложения ИИ и отредактируйте состав работ перед подбором экспертов.</p>
        </div>
        <span className="ai-badge">
          <Sparkles size={14} />
          Черновик ИИ
        </span>
      </div>

      <div className="decomposition-note">
        <CircleAlert size={15} />
        <span>Состав и формулировки подзадач можно менять. В подбор попадут только подтверждённые менеджером записи.</span>
      </div>

      <div className="subtask-list">
        {request.subtasks.map((subtask, index) => (
          <article className="subtask-card" key={subtask.id}>
            <span className="subtask-card__number">{String(index + 1).padStart(2, '0')}</span>
            <div className="subtask-card__content">
              <div className="subtask-card__heading">
                <strong>{subtask.topic}</strong>
                <div className="subtask-card__actions">
                  <button
                    className="subtask-card__edit"
                    data-node-id={index === 0 ? 'zFPmw' : undefined}
                    type="button"
                    onClick={() => openEditor(subtask)}
                  >
                    <Pencil size={12} />
                    Изменить
                  </button>
                  <button className="subtask-card__delete" type="button" aria-label="Удалить подзадачу">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              <div className="subtask-card__keywords">
                {subtask.keywords.map((keyword) => <span key={keyword}>{keyword}</span>)}
                {subtask.keywords.length === 0 && <span>без ключевых слов</span>}
              </div>
            </div>
          </article>
        ))}
        {request.subtasks.length === 0 && <div className="subtask-list__empty">
          Добавьте хотя бы одну подзадачу для подбора экспертов.
        </div>}
      </div>

      <button
        className="add-subtask"
        data-node-id="pqf9E"
        type="button"
        onClick={addSubtask}
      >
        <Plus size={14} />
        Добавить подзадачу
      </button>

      <div className="decomposition-editor__footer">
        <div className="decomposition-editor__status" aria-live="polite">
          {error
            ? <span className="error-message">{error}</span>
            : `${request.subtasks.length} ${request.subtasks.length === 1 ? 'подзадача подготовлена' : 'подзадачи подготовлены'} к подбору.`}
        </div>
        <button
          className="button button--primary"
          data-node-id="a39TC"
          type="button"
          disabled={request.subtasks.length === 0 || loading}
          onClick={onContinue}
        >
          {loading ? 'Идёт подбор…' : hasResults ? 'Далее' : 'Перейти к результатам'}
          {!loading && <ArrowRight size={14} />}
        </button>
      </div>
    </section>

    {editing && <EditSubtaskModal
      value={editing}
      onChange={setEditing}
      onClose={() => setEditing(null)}
      onSave={saveEdit}
    />}
  </div>
}

type EditSubtaskModalProps = {
  value: EditState
  onChange: (value: EditState) => void
  onClose: () => void
  onSave: () => void
}

function EditSubtaskModal({ value, onChange, onClose, onSave }: EditSubtaskModalProps) {
  const [keyword, setKeyword] = useState('')

  const addKeyword = (event: FormEvent) => {
    event.preventDefault()
    const next = keyword.trim()
    if (next && !value.keywords.some((item) => item.toLocaleLowerCase() === next.toLocaleLowerCase())) {
      onChange({ ...value, keywords: [...value.keywords, next] })
    }
    setKeyword('')
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <section
      className="subtask-modal"
      role="dialog"
      aria-modal="true"
      aria-labelledby="edit-subtask-title"
      onMouseDown={(event) => event.stopPropagation()}
    >
      <div className="subtask-modal__heading">
        <div>
          <span>РЕДАКТИРОВАНИЕ ПОДЗАДАЧИ</span>
          <h2 id="edit-subtask-title">Уточнить формулировку</h2>
        </div>
        <button type="button" aria-label="Закрыть" onClick={onClose}>
          <X size={17} />
        </button>
      </div>
      <label className="field">
        <span>Название подзадачи</span>
        <textarea
          className="subtask-modal__topic"
          value={value.topic}
          onChange={(event) => onChange({ ...value, topic: event.target.value })}
          autoFocus
        />
      </label>
      <div className="modal-keywords">
        <strong>Ключевые слова</strong>
        <div className="modal-keywords__items">
          {value.keywords.map((item) => <span className="tag" key={item}>
            {item}
            <button
              type="button"
              aria-label={`Удалить ключевое слово ${item}`}
              onClick={() => onChange({ ...value, keywords: value.keywords.filter((keyword) => keyword !== item) })}
            >
              <X size={11} />
            </button>
          </span>)}
        </div>
        <form className="modal-keywords__form" onSubmit={addKeyword}>
          <input
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="Добавить ключевое слово"
          />
          <button type="submit" aria-label="Добавить ключевое слово">
            <Plus size={14} />
          </button>
        </form>
      </div>
      <div className="subtask-modal__footer">
        <button className="button button--secondary" type="button" onClick={onClose}>Отмена</button>
        <button className="button button--primary" type="button" disabled={!value.topic.trim()} onClick={onSave}>
          Сохранить подзадачу
        </button>
      </div>
    </section>
  </div>
}
