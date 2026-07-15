import type { Candidate, EmailDraft, MatchResult, Subtask } from './types'

type RequestPayload = {
  title: string
  description: string
}

async function post<T>(path: string, payload: unknown): Promise<T> {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const body = await response.text()
    let message = body
    try {
      const parsed = JSON.parse(body) as { detail?: string | Array<{ msg?: string }> }
      message = typeof parsed.detail === 'string'
        ? parsed.detail
        : parsed.detail?.map((item) => item.msg).filter(Boolean).join(', ') || body
    } catch {
      // The plain response body is already the most useful error message.
    }
    throw new Error(message || `Ошибка API: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function decompose(request: RequestPayload) {
  return post<{ subtasks: Subtask[] }>('/api/v1/decompose', { request })
}

export function findMatches(request: RequestPayload, subtasks: Subtask[]) {
  return post<{ request: RequestPayload; results: MatchResult[] }>('/api/v1/matches', {
    request,
    decompose: { subtasks },
  })
}

export function createEmailDraft(
  request: RequestPayload,
  candidate: Candidate,
  facts: string[],
  instruction: string,
) {
  return post<EmailDraft>('/api/v1/email-drafts', {
    request,
    candidate,
    facts,
    instruction,
  })
}
