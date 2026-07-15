export type Subtask = { id: number; topic: string; keywords: string[] }

export type Candidate = {
  profile: {
    id: string
    full_name: string
    unit: string
    position?: string | null
    degree?: string | null
    email?: string | null
    publications?: { title: string; year?: number | null }[]
    grants?: { title: string; years?: string | null }[]
  }
  score: number
  reasons: string[]
}

export type MatchResult = { subtask: Subtask; candidates: Candidate[] }
export type EmailDraft = { to?: string | null; subject: string; body: string }

type RequestPayload = { title: string; description: string }

async function post<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Ошибка API: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function decompose(request: RequestPayload) {
  return post<{ subtasks: Subtask[] }>('/api/v1/decompose', { request })
}

export function findMatches(request: RequestPayload, subtasks: Subtask[]) {
  return post<{ results: MatchResult[] }>('/api/v1/matches', {
    request,
    decompose: { subtasks },
  })
}

export function createEmailDraft(request: RequestPayload, candidate: Candidate, facts: string[], instruction: string) {
  return post<EmailDraft>('/api/v1/email-drafts', { request, candidate, facts, instruction })
}
