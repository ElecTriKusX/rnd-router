import { Building2, ListFilter, Plus, Search } from 'lucide-react'
import type { RequestItem } from '../types'

type RequestListProps = {
  requests: RequestItem[]
  selectedId: string
  search: string
  onSearch: (value: string) => void
  onSelect: (id: string) => void
  onAdd: () => void
}

function statusLabel(request: RequestItem) {
  return request.status === 'new' ? 'Новая заявка' : `${request.status}/3`
}

export function RequestList({
  requests,
  selectedId,
  search,
  onSearch,
  onSelect,
  onAdd,
}: RequestListProps) {
  return <section className="request-list" data-node-id="FfvmN" data-pencil-name="Заявки CRM">
    <div className="request-list__heading">
      <div>
        <h2>Заявки CRM</h2>
        <p>Входящие обращения</p>
      </div>
      <button
        className="icon-button icon-button--brand"
        data-node-id="Fh1Xm"
        type="button"
        aria-label="Добавить заявку"
        onClick={onAdd}
      >
        <Plus size={16} />
      </button>
    </div>

    <label className="request-search" data-node-id="uyLHn">
      <Search size={14} />
      <input
        value={search}
        onChange={(event) => onSearch(event.target.value)}
        placeholder="Найти заявку"
        aria-label="Найти заявку по названию"
      />
      <span className="request-search__filter" aria-hidden="true">
        <ListFilter size={14} />
      </span>
    </label>

    <div className="request-list__cards">
      {requests.map((request) => {
        const selected = request.id === selectedId
        return <button
          className={`request-card${selected ? ' is-selected' : ''}`}
          type="button"
          onClick={() => onSelect(request.id)}
          key={request.id}
        >
          <span className="request-card__meta">
            <span className="request-card__id">{request.id}</span>
            <span className="request-card__status" data-node-id={selected ? 'vXJen' : undefined}>
              {statusLabel(request)}
            </span>
          </span>
          <strong className="request-card__title">{request.title || 'Без названия'}</strong>
          <span className="request-card__company">
            <Building2 size={12} />
            {request.company}
          </span>
          <span className="request-card__tags">
            {request.tags.slice(0, 3).map((tag) => <span key={tag}>{tag}</span>)}
          </span>
        </button>
      })}
      {requests.length === 0 && <p className="request-list__empty">Заявки не найдены</p>}
    </div>
  </section>
}
