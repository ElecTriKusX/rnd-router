import {
  Clock3,
  Files,
  PanelLeftOpen,
  Settings2,
  Sparkles,
  UsersRound,
} from 'lucide-react'
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
  return <>
    <aside className="sidebar sidebar--expanded" data-pencil-name="Боковая навигация">
      <img className="sidebar__logo" src={logo} alt="Тюменский государственный университет" />
      <div className="sidebar__project">
        <span>НИОКР · ТЮМГУ</span>
        <strong>Маршрутизатор<br />НИОКР</strong>
      </div>
      <nav className="sidebar__navigation" aria-label="Основная навигация">
        {navigation.map(({ label, icon: Icon, active }) => (
          <div className={`sidebar__nav-item${active ? ' is-active' : ''}`} key={label}>
            <Icon size={17} strokeWidth={2} />
            <span>{label}</span>
          </div>
        ))}
      </nav>
      <div className="sidebar__spacer" />
      <div className="sidebar__profile">
        <span className="sidebar__avatar" />
        <span className="sidebar__profile-copy">
          <strong>Валерия Петрова</strong>
          <small>Менеджер НИОКР</small>
        </span>
      </div>
    </aside>

    <aside className="sidebar sidebar--compact" data-pencil-name="Сжатая боковая навигация">
      <img className="sidebar__compact-logo" src={compactLogo} alt="ТюмГУ" />
      <nav className="sidebar__compact-navigation" aria-label="Основная навигация">
        {navigation.map(({ label, icon: Icon, active }) => (
          <div
            className={`sidebar__compact-item${active ? ' is-active' : ''}`}
            title={label}
            key={label}
          >
            <Icon size={18} strokeWidth={2} />
          </div>
        ))}
      </nav>
      <div className="sidebar__spacer" />
      <div className="sidebar__compact-profile">
        <span className="sidebar__compact-avatar" />
        <PanelLeftOpen size={14} />
      </div>
    </aside>
  </>
}
