export type WorkflowStage = 'request' | 'decomposition' | 'results' | 'email' | 'draft'

export type WorkflowStatus = 'new' | 1 | 2 | 3

export type RequestSnapshot = {
  title: string
  description: string
  tags: string[]
}

export type Subtask = {
  id: number
  topic: string
  keywords: string[]
}

export type Publication = {
  title: string
  year?: number | null
  annotation?: string | null
  journal?: string | null
  link?: string | null
}

export type Grant = {
  number: string
  years?: string | null
  role?: string | null
  title: string
  annotation?: string | null
  link?: string | null
}

export type Candidate = {
  profile: {
    id: string
    full_name: string
    unit: string
    position?: string | null
    degree?: string | null
    email?: string | null
    publications: Publication[]
    grants: Grant[]
    links?: Record<string, string>
  }
  score: number
  reasons: string[]
}

export type MatchResult = {
  subtask: Subtask
  candidates: Candidate[]
}

export type EmailDraft = {
  to?: string | null
  subject: string
  body: string
}

export type RequestItem = {
  id: string
  title: string
  company: string
  tags: string[]
  description: string
  status: WorkflowStatus
  saved: RequestSnapshot | null
  subtasks: Subtask[]
  results: MatchResult[]
}
