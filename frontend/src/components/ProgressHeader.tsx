import type { WorkflowStage } from '../types'

type ProgressHeaderProps = {
  stage: WorkflowStage
  availableStatus: number
  onNavigate: (stage: WorkflowStage) => void
}

const steps: Array<{
  stage: WorkflowStage
  title: string
  subtitle: string
  position: number
}> = [
  { stage: 'request', title: 'Новая заявка', subtitle: 'Редактирование', position: 1 },
  { stage: 'decomposition', title: 'Декомпозиция', subtitle: 'Проверка задач', position: 2 },
  { stage: 'results', title: 'Результаты', subtitle: 'Экспертные досье', position: 3 },
]

function stagePosition(stage: WorkflowStage) {
  if (stage === 'request') return 1
  if (stage === 'decomposition') return 2
  return 3
}

export function ProgressHeader({ stage, availableStatus, onNavigate }: ProgressHeaderProps) {
  const current = stagePosition(stage)

  return <header className="progress" data-pencil-name="Этапы обработки">
    <div className="progress__inner">
      {steps.map((step, index) => {
        const isCurrent = step.position === current
        const isAvailable = step.position <= availableStatus
        const isCompleted = isAvailable && !isCurrent
        const canNavigate = isAvailable && step.stage !== stage

        return <div className="progress__group" key={step.stage}>
          {index > 0 && <span className={`progress__line${isAvailable ? ' is-completed' : ''}`} />}
          <button
            className={`progress__step${isCurrent ? ' is-current' : ''}${isCompleted ? ' is-completed' : ''}`}
            type="button"
            disabled={!canNavigate}
            onClick={() => canNavigate && onNavigate(step.stage)}
          >
            <span className="progress__dot" aria-hidden="true" />
            <span className="progress__copy">
              <strong>{step.title}</strong>
              <small>{step.subtitle}</small>
            </span>
          </button>
        </div>
      })}
    </div>
  </header>
}
