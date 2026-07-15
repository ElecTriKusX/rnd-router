import { useMemo, useState } from 'react'
import { decompose } from './api'
import { ProgressHeader } from './components/ProgressHeader'
import { RequestEditor } from './components/RequestEditor'
import { RequestList } from './components/RequestList'
import { Sidebar } from './components/Sidebar'
import { initialRequests } from './initialRequests'
import type { RequestItem, WorkflowStage } from './types'

function createRequestId(existing: RequestItem[]) {
  const ids = new Set(existing.map((request) => request.id))
  let id = ''
  do {
    const value = Math.floor(10000 + Math.random() * 90000)
    id = `CRM-${value}`
  } while (ids.has(id))
  return id
}

function snapshot(request: RequestItem) {
  return {
    title: request.title,
    description: request.description,
    tags: [...request.tags],
  }
}

function changedSinceSave(request: RequestItem) {
  if (!request.saved) return true
  return request.title !== request.saved.title
    || request.description !== request.saved.description
    || request.tags.join('\u0000') !== request.saved.tags.join('\u0000')
}

export function App() {
  const [requests, setRequests] = useState<RequestItem[]>(initialRequests)
  const [selectedId, setSelectedId] = useState(initialRequests[0].id)
  const [search, setSearch] = useState('')
  const [stage, setStage] = useState<WorkflowStage>('request')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const selected = requests.find((request) => request.id === selectedId) ?? requests[0]
  const visibleRequests = useMemo(() => {
    const query = search.trim().toLocaleLowerCase('ru')
    return query
      ? requests.filter((request) => request.title.toLocaleLowerCase('ru').includes(query))
      : requests
  }, [requests, search])

  const updateSelected = (updater: (request: RequestItem) => RequestItem) => {
    setRequests((items) => items.map((request) => request.id === selectedId ? updater(request) : request))
  }

  const addRequest = () => {
    const id = createRequestId(requests)
    const next: RequestItem = {
      id,
      title: 'Новая заявка',
      company: 'Заказчик не указан',
      tags: [],
      description: '',
      status: 'new',
      saved: null,
      subtasks: [],
      results: [],
    }
    setRequests((items) => [next, ...items])
    setSelectedId(id)
    setSearch('')
    setStage('request')
    setError('')
  }

  const saveRequest = () => {
    updateSelected((request) => {
      const invalidatesLaterStages = changedSinceSave(request) && request.status !== 'new' && request.status > 1
      return {
        ...request,
        status: 1,
        saved: snapshot(request),
        subtasks: invalidatesLaterStages ? [] : request.subtasks,
        results: invalidatesLaterStages ? [] : request.results,
      }
    })
    setStage('request')
    setError('')
  }

  const continueFromRequest = async () => {
    if (!selected) return
    if (selected.status !== 'new' && selected.status >= 2 && selected.subtasks.length > 0) {
      setStage('decomposition')
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await decompose({
        title: selected.title.trim(),
        description: selected.description.trim(),
      })
      updateSelected((request) => ({
        ...request,
        title: request.title.trim(),
        description: request.description.trim(),
        status: 2,
        saved: {
          title: request.title.trim(),
          description: request.description.trim(),
          tags: [...request.tags],
        },
        subtasks: response.subtasks,
        results: [],
      }))
      setStage('decomposition')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось выполнить декомпозицию')
    } finally {
      setLoading(false)
    }
  }

  const availableStatus = selected?.status === 'new' ? 1 : selected?.status ?? 1

  return <main className="app-shell">
    <Sidebar />
    <div className="workspace">
      <ProgressHeader
        stage={stage}
        availableStatus={availableStatus}
        onNavigate={setStage}
      />
      {selected && <div className="request-stage">
        <RequestList
          requests={visibleRequests}
          selectedId={selectedId}
          search={search}
          onSearch={setSearch}
          onSelect={(id) => {
            setSelectedId(id)
            setStage('request')
            setError('')
          }}
          onAdd={addRequest}
        />
        <RequestEditor
          request={selected}
          loading={loading}
          error={error}
          onChange={(updates) => updateSelected((request) => ({ ...request, ...updates }))}
          onSave={saveRequest}
          onContinue={continueFromRequest}
        />
      </div>}
    </div>
  </main>
}
