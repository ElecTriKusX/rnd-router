import { useMemo, useState } from 'react'
import { createEmailDraft, decompose, findMatches } from './api'
import { DecompositionStage } from './components/DecompositionStage'
import { EmailDraftStage } from './components/EmailDraftStage'
import { buildCandidateFacts, EmailPreparationStage } from './components/EmailPreparationStage'
import { ProgressHeader } from './components/ProgressHeader'
import { RequestEditor } from './components/RequestEditor'
import { RequestList } from './components/RequestList'
import { ResultsStage } from './components/ResultsStage'
import { Sidebar } from './components/Sidebar'
import { initialRequests } from './initialRequests'
import type { EmailDraft, RequestItem, Subtask, WorkflowStage } from './types'

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

function contentChangedSinceSave(request: RequestItem) {
  if (!request.saved) return true
  return request.title !== request.saved.title
    || request.description !== request.saved.description
}

function workflowStagePosition(stage: WorkflowStage) {
  return ({ request: 0, decomposition: 1, results: 2, email: 3, draft: 4 } as const)[stage]
}

export function App() {
  const [requests, setRequests] = useState<RequestItem[]>(initialRequests)
  const [selectedId, setSelectedId] = useState(initialRequests[0].id)
  const [search, setSearch] = useState('')
  const [stage, setStage] = useState<WorkflowStage>('request')
  const [stageDirection, setStageDirection] = useState<'forward' | 'backward'>('forward')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<Record<string, string[]>>({})
  const [activeCandidateId, setActiveCandidateId] = useState<string | null>(null)
  const [activeEmailSubtask, setActiveEmailSubtask] = useState<Subtask | null>(null)
  const [selectedFactIds, setSelectedFactIds] = useState<string[]>([])
  const [emailInstruction, setEmailInstruction] = useState('Упомянуть возможность короткой онлайн-встречи и уточнить удобный формат связи.')
  const [emailDraft, setEmailDraft] = useState<EmailDraft | null>(null)

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

  const navigateToStage = (nextStage: WorkflowStage) => {
    if (nextStage === stage) return
    setStageDirection(workflowStagePosition(nextStage) > workflowStagePosition(stage) ? 'forward' : 'backward')
    setStage(nextStage)
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
    navigateToStage('request')
    setError('')
  }

  const saveRequest = () => {
    const invalidatesSelection = selected
      ? contentChangedSinceSave(selected) && selected.status !== 'new' && selected.status > 1
      : false
    updateSelected((request) => {
      const invalidatesLaterStages = contentChangedSinceSave(request) && request.status !== 'new' && request.status > 1
      return {
        ...request,
        status: request.status === 'new' || invalidatesLaterStages ? 1 : request.status,
        saved: snapshot(request),
        subtasks: invalidatesLaterStages ? [] : request.subtasks,
        results: invalidatesLaterStages ? [] : request.results,
      }
    })
    if (invalidatesSelection) {
      setSelectedCandidateIds((selection) => ({ ...selection, [selectedId]: [] }))
      setActiveCandidateId(null)
      setActiveEmailSubtask(null)
      setEmailDraft(null)
    }
    navigateToStage('request')
    setError('')
  }

  const continueFromRequest = async () => {
    if (!selected) return
    if (selected.status !== 'new' && selected.status >= 2 && selected.subtasks.length > 0) {
      navigateToStage('decomposition')
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
      navigateToStage('decomposition')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось выполнить декомпозицию')
    } finally {
      setLoading(false)
    }
  }

  const changeSubtasks = (subtasks: RequestItem['subtasks']) => {
    updateSelected((request) => ({
      ...request,
      status: 2,
      subtasks,
      results: [],
    }))
    setSelectedCandidateIds((selection) => ({ ...selection, [selectedId]: [] }))
    setActiveCandidateId(null)
    setActiveEmailSubtask(null)
    setEmailDraft(null)
    setError('')
  }

  const continueFromDecomposition = async () => {
    if (!selected) return
    if (selected.status !== 'new' && selected.status >= 3 && selected.results.length > 0) {
      navigateToStage('results')
      return
    }

    setLoading(true)
    setError('')
    try {
      const response = await findMatches({
        title: selected.title,
        description: selected.description,
      }, selected.subtasks)
      updateSelected((request) => ({
        ...request,
        status: 3,
        results: response.results,
      }))
      setSelectedCandidateIds((selection) => ({
        ...selection,
        [selectedId]: [],
      }))
      navigateToStage('results')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось подобрать экспертов')
    } finally {
      setLoading(false)
    }
  }

  const availableStatus = selected?.status === 'new' ? 1 : selected?.status ?? 1
  const activeCandidate = selected?.results
    .flatMap((result) => result.candidates)
    .find((candidate) => candidate.profile.id === activeCandidateId)
  const activeFacts = activeCandidate ? buildCandidateFacts(activeCandidate) : []

  const generateEmailDraft = async (facts: ReturnType<typeof buildCandidateFacts>) => {
    if (!selected || !activeCandidate) return
    setLoading(true)
    setError('')
    try {
      const draft = await createEmailDraft(
        { title: selected.title, description: selected.description },
        activeCandidate,
        facts.map((fact) => fact.title),
        emailInstruction,
      )
      setEmailDraft(draft)
      navigateToStage('draft')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Не удалось создать черновик письма')
    } finally {
      setLoading(false)
    }
  }

  return <main className="app-shell">
    <Sidebar />
    <div className="workspace">
      <ProgressHeader
        stage={stage}
        availableStatus={availableStatus}
        onNavigate={navigateToStage}
      />
      <div key={stage} className={`stage-transition stage-transition--${stageDirection}`}>
      {selected && stage === 'request' && <div className="request-stage">
        <RequestList
          requests={visibleRequests}
          selectedId={selectedId}
          search={search}
          onSearch={setSearch}
          onSelect={(id) => {
            setSelectedId(id)
            navigateToStage('request')
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
      {selected && stage === 'decomposition' && <DecompositionStage
        request={selected}
        loading={loading}
        error={error}
        onBack={() => {
          navigateToStage('request')
          setError('')
        }}
        onChange={changeSubtasks}
        onContinue={continueFromDecomposition}
      />}
      {selected && stage === 'results' && <ResultsStage
        request={selected}
        selectedCandidateIds={selectedCandidateIds[selected.id] ?? []}
        onToggleCandidate={(candidateId) => setSelectedCandidateIds((selection) => {
          const current = selection[selected.id] ?? []
          return {
            ...selection,
            [selected.id]: current.includes(candidateId)
              ? current.filter((id) => id !== candidateId)
              : [...current, candidateId],
          }
        })}
        onBack={() => {
          navigateToStage('decomposition')
          setError('')
        }}
        onPrepareEmail={(candidate, subtask) => {
          setActiveCandidateId(candidate.profile.id)
          setActiveEmailSubtask(subtask)
          setSelectedFactIds([])
          setEmailDraft(null)
          setError('')
          navigateToStage('email')
        }}
      />}
      {selected && stage === 'email' && activeCandidate && activeEmailSubtask && <EmailPreparationStage
        request={selected}
        candidate={activeCandidate}
        subtask={activeEmailSubtask}
        selectedFactIds={selectedFactIds}
        instruction={emailInstruction}
        loading={loading}
        error={error}
        onSelectFacts={setSelectedFactIds}
        onInstruction={setEmailInstruction}
        onBack={() => {
          navigateToStage('results')
          setError('')
        }}
        onCreateDraft={generateEmailDraft}
      />}
      {selected && stage === 'draft' && activeCandidate && activeEmailSubtask && emailDraft && <EmailDraftStage
        candidate={activeCandidate}
        subtask={activeEmailSubtask}
        facts={activeFacts.filter((fact) => selectedFactIds.includes(fact.id))}
        instruction={emailInstruction}
        draft={emailDraft}
        onBackToResults={() => navigateToStage('results')}
        onBackToFacts={() => navigateToStage('email')}
      />}
      </div>
    </div>
  </main>
}
