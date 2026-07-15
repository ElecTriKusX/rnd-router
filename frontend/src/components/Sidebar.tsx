import {
  Clock3,
  Files,
  PanelLeftClose,
  PanelLeftOpen,
  Settings2,
  Sparkles,
  UsersRound,
} from 'lucide-react'
import { useState } from 'react'
import logo from '../assets/utmn-logo-rus.png'
import compactLogo from '../assets/utmn-logo-mini-rus.png'

const navigation = [
  { label: 'Подбор экспертов', icon: Sparkles, active: true },
  { label: 'Все заявки', icon: Files },
  { label: 'История заявок', icon: Clock3 },
  { label: 'Эксперты', icon: UsersRound },
  { label: 'Настройки', icon: Settings2 },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)

  return <>
    <aside className={`sidebar sidebar--expanded${collapsed ? ' is-collapsed' : ''}`} data-node-id="JZixB" data-pencil-name="Боковая навигация">
      <img className="sidebar__logo" src={logo} alt="Тюменский государственный университет" />
      <div className="sidebar__project">
        <span>НИОКР · ТЮМГУ</span>
        <strong>Маршрутизатор<br />НИОКР</strong>
      </div>
      <nav className="sidebar__navigation" aria-label="Основная навигация">
        {navigation.map(({ label, icon: Icon, active }) => (
          <button className={`sidebar__nav-item${active ? ' is-active' : ''}`} type="button" key={label}>
            <Icon size={17} strokeWidth={2} />
            <span>{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar__spacer" />
      <div className="sidebar__profile">
        <span className="sidebar__avatar" />
        <span className="sidebar__profile-copy">
          <strong>Администратор</strong>
          <small>Менеджер НИОКР</small>
        </span>
      </div>
      <button className="sidebar__collapse" type="button" onClick={() => setCollapsed(true)}>
        <PanelLeftClose size={16} />
        <span>Свернуть</span>
      </button>
    </aside>

    <aside className={`sidebar sidebar--compact${collapsed ? ' is-visible' : ''}`} data-node-id="uDZr0" data-pencil-name="Сжатая боковая навигация">
      <img className="sidebar__compact-logo" src={compactLogo} alt="ТюмГУ" />
      <nav className="sidebar__compact-navigation" aria-label="Основная навигация">
        {navigation.map(({ label, icon: Icon, active }) => (
          <button
            className={`sidebar__compact-item${active ? ' is-active' : ''}`}
            type="button"
            title={label}
            key={label}
          >
            <Icon size={18} strokeWidth={2} />
          </button>
        ))}
      </nav>
      <div className="sidebar__spacer" />
      <button className="sidebar__compact-profile" type="button" aria-label="Развернуть боковую панель" onClick={() => setCollapsed(false)}>
        <span className="sidebar__compact-avatar" />
        <PanelLeftOpen size={14} />
      </button>
    </aside>
  </>
}
