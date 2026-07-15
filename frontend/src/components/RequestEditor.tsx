import { ArrowRight, Check, Database, Info, LoaderCircle, Plus, X } from 'lucide-react'
import { FormEvent, useEffect, useRef, useState } from 'react'
import type { RequestItem } from '../types'

type RequestEditorProps = {
  request: RequestItem
  loading: boolean
  error: string
  onChange: (updates: Partial<Pick<RequestItem, 'title' | 'description' | 'tags'>>) => void
  onSave: () => void
  onContinue: () => void
}

export function RequestEditor({
  request,
  loading,
  error,
  onChange,
  onSave,
  onContinue,
}: RequestEditorProps) {
  const [addingTag, setAddingTag] = useState(false)
  const [tag, setTag] = useState('')
  const tagInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (addingTag) tagInput.current?.focus()
  }, [addingTag])

  useEffect(() => {
    setAddingTag(false)
    setTag('')
  }, [request.id])

  const addTag = (event: FormEvent) => {
    event.preventDefault()
    const nextTag = tag.trim()
    if (nextTag && !request.tags.some((item) => item.toLocaleLowerCase() === nextTag.toLocaleLowerCase())) {
      onChange({ tags: [...request.tags, nextTag] })
    }
    setTag('')
    setAddingTag(false)
  }

  const cancelAddingTag = () => {
    setTag('')
    setAddingTag(false)
  }

  const canContinue = request.title.trim().length > 0 && request.description.trim().length > 0
  const hasDecomposition = request.status !== 'new' && request.status >= 2 && request.subtasks.length > 0

  return <section className="request-editor" data-pencil-name="Редактор заявки">
    <div className="request-editor__heading">
      <div>
        <h1>{request.status === 'new' ? 'Новая заявка' : 'Новая заявка'}</h1>
        <p>Проверьте и уточните данные перед переходом к декомпозиции.</p>
      </div>
      <div className="request-editor__source-actions">
        <span className="source-badge">
          <Database size={14} />
          CRM · {request.id}
        </span>
        <button className="secondary-compact" type="button">
          <Info size={13} />
          Подробнее
        </button>
      </div>
    </div>

    <label className="field">
      <span>Краткое название</span>
      <input
        value={request.title}
        onChange={(event) => onChange({ title: event.target.value })}
        placeholder="Введите название заявки"
      />
    </label>

    <label className="field field--grow">
      <span>Текст заявки</span>
      <textarea
        value={request.description}
        onChange={(event) => onChange({ description: event.target.value })}
        placeholder="Опишите задачу заказчика"
      />
    </label>

    <div className="request-tags">
      <div className="request-tags__heading">
        <strong>Метки для фильтрации</strong>
        <span>для быстрого поиска заявки</span>
      </div>
      <div className="request-tags__list">
        {request.tags.map((item) => (
          <span className="tag" key={item}>
            {item}
            <button
              type="button"
              aria-label={`Удалить тег ${item}`}
              onClick={() => onChange({ tags: request.tags.filter((value) => value !== item) })}
            >
              <X size={11} />
            </button>
          </span>
        ))}
        {addingTag ? <form className="tag-input" onSubmit={addTag}>
          <input
            ref={tagInput}
            value={tag}
            onChange={(event) => setTag(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Escape') cancelAddingTag()
            }}
            placeholder="Новый тег"
            aria-label="Новый тег"
          />
          <button className="tag-input__confirm" type="submit" aria-label="Добавить тег" title="Добавить тег">
            <Check size={13} />
          </button>
          <button
            className="tag-input__cancel"
            type="button"
            aria-label="Отменить добавление тега"
            title="Отменить"
            onClick={cancelAddingTag}
          >
            <X size={13} />
          </button>
        </form> : <button
          className="add-tag"
          data-node-id="sUt8m"
          type="button"
          onClick={() => setAddingTag(true)}
        >
          <Plus size={12} />
          Создать тег
        </button>}
      </div>
    </div>

    <div className="request-editor__footer">
      <div className="request-editor__message" aria-live="polite">
        {error ? <span className="error-message">{error}</span> : 'Изменения сохраняются в карточке CRM.'}
      </div>
      <div className="request-editor__buttons">
        <button
          className="button button--secondary"
          data-node-id="S7XbV"
          type="button"
          onClick={onSave}
        >
          Сохранить изменения
        </button>
        <button
          className="button button--primary"
          data-node-id="XRdSY"
          type="button"
          disabled={!canContinue || loading}
          onClick={onContinue}
        >
          {loading && <LoaderCircle className="button__spinner" size={14} />}
          {loading ? 'Обработка…' : hasDecomposition ? 'Далее' : 'Перейти к декомпозиции'}
          {!loading && <ArrowRight size={14} />}
        </button>
      </div>
    </div>
  </section>
}
