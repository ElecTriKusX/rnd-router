import { MouseEvent, useEffect, useRef, useState } from 'react'
import utmnLogo from './assets/utmn-logo-rus.png'

type Stage = 1 | 2 | 3 | 4 | 5

function extractBody(document: string) {
  return document.match(/<body[^>]*>([\s\S]*)<\/body>/i)?.[1] ?? document
}

function readStage(): Stage {
  const value = Number(window.location.hash.replace('#stage-', ''))
  return value >= 1 && value <= 5 ? value as Stage : 1
}

export function App() {
  const [stage, setStage] = useState<Stage>(readStage)
  const [markup, setMarkup] = useState('')
  const pageRef = useRef<HTMLDivElement>(null)

  const navigate = (nextStage: Stage) => {
    if (nextStage === stage) return
    window.location.hash = `stage-${nextStage}`
    setStage(nextStage)
  }

  useEffect(() => {
    const onHashChange = () => setStage(readStage())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    setMarkup('')
    fetch(`${import.meta.env.BASE_URL}pencil/RND${stage}.html`, { signal: controller.signal })
      .then((response) => response.ok ? response.text() : Promise.reject(new Error(`Не удалось загрузить экран ${stage}`)))
      .then((document) => setMarkup(extractBody(document)))
      .catch((error: unknown) => { if (!(error instanceof DOMException && error.name === 'AbortError')) throw error })
    return () => controller.abort()
  }, [stage])

  useEffect(() => {
    const logo = pageRef.current?.querySelector<HTMLElement>('[data-pencil-name="Логотип ТюмГУ"]')
    if (logo) logo.style.backgroundImage = `url("${utmnLogo}")`
  }, [markup])

  const handleClick = (event: MouseEvent<HTMLDivElement>) => {
    let current = event.target instanceof HTMLElement ? event.target : null
    const names: string[] = []
    while (current && current !== pageRef.current) {
      const name = current.dataset.pencilName
      if (name) names.push(name)
      current = current.parentElement
    }

    if (names.some((name) => name === 'Перейти к декомпозиции')) navigate(2)
    else if (names.some((name) => name === 'Перейти к результатам')) navigate(3)
    else if (names.some((name) => name === 'Разослать письма')) navigate(4)
    else if (names.some((name) => name === 'Создать черновик')) navigate(5)
    else if (names.some((name) => name === 'Изменить факты')) navigate(4)
    else if (names.some((name) => name === 'Вернуться к заявке')) navigate(stage === 2 ? 1 : stage === 3 ? 2 : stage === 4 ? 3 : 4)
  }

  return <main className="pencil-stage" onClick={handleClick}>
    <div ref={pageRef} className="pencil-canvas" dangerouslySetInnerHTML={{ __html: markup }} />
  </main>
}
