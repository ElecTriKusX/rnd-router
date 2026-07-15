import { ArrowLeft, Copy, Pencil, Send, SlidersHorizontal } from 'lucide-react'
import type { Candidate, EmailDraft, Subtask } from '../types'
import type { CandidateFact } from './EmailPreparationStage'

type EmailDraftStageProps = {
  candidate: Candidate
  subtask: Subtask
  facts: CandidateFact[]
  instruction: string
  draft: EmailDraft
  onBackToResults: () => void
  onBackToFacts: () => void
}

export function EmailDraftStage({
  candidate,
  facts,
  instruction,
  draft,
  onBackToResults,
  onBackToFacts,
}: EmailDraftStageProps) {
  return <div className="email-draft-stage">
    <aside className="draft-context" data-pencil-name="Основания письма">
      <h2>Факты, использованные в черновике</h2>
      <strong className="draft-context__candidate">{candidate.profile.full_name}</strong>
      <div className="draft-context__facts">
        {facts.map((fact) => <div className="draft-fact" key={fact.id}>
          <div><span>{fact.meta}</span><span>↗</span></div>
          <strong>{fact.title}</strong>
        </div>)}
      </div>
      <div className="draft-context__instruction">
        <span>ДОПОЛНИТЕЛЬНАЯ ИНСТРУКЦИЯ</span>
        <p>{instruction || 'Дополнительная инструкция не задана.'}</p>
      </div>
      <button
        className="button button--white button--wide"
        data-node-id="IeJ0G"
        type="button"
        onClick={onBackToFacts}
      >
        <SlidersHorizontal size={13} />
        Изменить факты
      </button>
      <div className="draft-context__spacer" />
      <button
        className="button button--white button--wide"
        data-node-id="i6P7h"
        type="button"
        onClick={onBackToResults}
      >
        <ArrowLeft size={14} />
        Вернуться к результатам подбора
      </button>
    </aside>

    <section className="draft-letter" data-pencil-name="Черновик письма">
      <div className="draft-letter__heading">
        <div>
          <h1>Черновик для {candidate.profile.full_name}</h1>
          <p>создан на основе {facts.length} выбранных фактов</p>
        </div>
        <button type="button"><Pencil size={13} />Редактировать</button>
      </div>
      <div className="draft-letter__fields">
        <div><span>Кому</span><strong>{candidate.profile.full_name} &lt;{draft.to || candidate.profile.email || 'email не указан'}&gt;</strong></div>
        <div><span>Тема</span><strong>{draft.subject}</strong></div>
      </div>
      <div className="draft-letter__body">{draft.body}</div>
      <div className="draft-letter__footer">
        <p>Письмо будет отправлено только этому участнику.</p>
        <div>
          <button className="button button--secondary" type="button"><Copy size={14} />Скопировать</button>
          <button className="button button--primary" type="button"><Send size={14} />Отправить письмо</button>
        </div>
      </div>
    </section>
  </div>
}
