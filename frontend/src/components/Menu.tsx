import { type KeyboardEvent, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { normalize } from '../lib/text'
import styles from './Menu.module.css'

export type MenuOption<T> = { value: T; label: string }

type MenuProps<T> = {
  label: string
  /** Le libellé reste lu par les lecteurs d'écran, mais n'est pas affiché. */
  hideLabel?: boolean
  value: T
  options: MenuOption<T>[]
  onChange: (value: T) => void
  /** Ce que montre le bouton tant qu'aucune option ne correspond à la valeur. */
  placeholder?: string
  error?: string
  /** field : dans un formulaire. title : un grand titre qui se déroule. compact : dans un coin de carte. */
  variant?: 'field' | 'title' | 'compact'
}

type Place = { top: number; left: number; minWidth: number; maxHeight: number; above: boolean }

const GAP = 4
const TYPE_AHEAD_DELAY = 600

/**
 * Un menu déroulant dessiné par nous, à la place du <select> natif dont la liste
 * ne s'habille pas. Il suit le modèle « combobox sans saisie » des recommandations ARIA :
 * le focus reste sur le bouton, les flèches parcourent la liste, Entrée choisit, Échap ferme,
 * une lettre saute à l'option qui commence par elle.
 */
function Menu<T extends string | number>({
  label,
  hideLabel = false,
  value,
  options,
  onChange,
  placeholder = 'Choisir',
  error,
  variant = 'field',
}: MenuProps<T>) {
  const id = useId()
  const button = useRef<HTMLButtonElement>(null)
  const list = useRef<HTMLUListElement>(null)
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const [place, setPlace] = useState<Place | null>(null)
  const typed = useRef({ text: '', at: 0 })

  const selected = options.findIndex((o) => o.value === value)
  const current = options[selected]

  function show(index = selected) {
    if (options.length === 0) return
    setActive(Math.max(0, index))
    setOpen(true)
  }

  function choose(index: number) {
    const option = options[index]
    if (option && option.value !== value) onChange(option.value)
    setOpen(false)
  }

  // La liste vit hors de la feuille (son bord déchiré la couperait) : on la pose sous le bouton,
  // ou au-dessus quand la place manque en bas de l'écran.
  useLayoutEffect(() => {
    if (!open) return
    function measure() {
      const rect = button.current?.getBoundingClientRect()
      if (!rect) return
      const below = window.innerHeight - rect.bottom - GAP * 3
      const aboveSpace = rect.top - GAP * 3
      const above = below < 200 && aboveSpace > below
      setPlace({
        top: above ? rect.top - GAP : rect.bottom + GAP,
        left: Math.max(GAP, Math.min(rect.left, window.innerWidth - rect.width - GAP)),
        minWidth: rect.width,
        maxHeight: Math.min(320, above ? aboveSpace : below),
        above,
      })
    }
    measure()
    window.addEventListener('resize', measure)
    window.addEventListener('scroll', measure, true)
    return () => {
      window.removeEventListener('resize', measure)
      window.removeEventListener('scroll', measure, true)
    }
  }, [open])

  // Un clic ou un toucher ailleurs referme la liste.
  useEffect(() => {
    if (!open) return
    function outside(event: PointerEvent) {
      const target = event.target as Node
      if (!button.current?.contains(target) && !list.current?.contains(target)) setOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])

  // L'option active reste visible quand on descend dans une longue liste.
  useEffect(() => {
    if (open) document.getElementById(`${id}-${active}`)?.scrollIntoView({ block: 'nearest' })
  }, [open, active, id])

  /** Une lettre, ou quelques-unes tapées vite : l'option suivante qui commence ainsi. */
  function typeAhead(key: string) {
    const now = Date.now()
    const memory = typed.current
    memory.text = now - memory.at > TYPE_AHEAD_DELAY ? key : memory.text + key
    memory.at = now
    const wanted = normalize(memory.text)
    // La même lettre répétée fait défiler les options qui commencent par elle.
    const repeated = wanted.length > 1 && [...wanted].every((c) => c === wanted[0])
    const search = repeated ? wanted[0] : wanted
    const from = open ? active : Math.max(0, selected)
    const start = search.length === 1 ? from + 1 : from
    for (let step = 0; step < options.length; step++) {
      const index = (start + step) % options.length
      if (normalize(options[index].label).startsWith(search)) return index
    }
    return -1
  }

  function onKeyDown(event: KeyboardEvent) {
    const last = options.length - 1
    const keys: Record<string, () => void> = open
      ? {
          ArrowDown: () => (event.altKey ? choose(active) : setActive(Math.min(last, active + 1))),
          ArrowUp: () => (event.altKey ? choose(active) : setActive(Math.max(0, active - 1))),
          Home: () => setActive(0),
          End: () => setActive(last),
          PageDown: () => setActive(Math.min(last, active + 10)),
          PageUp: () => setActive(Math.max(0, active - 10)),
          Enter: () => choose(active),
          ' ': () => choose(active),
          Escape: () => setOpen(false),
        }
      : {
          ArrowDown: () => show(),
          ArrowUp: () => show(),
          Home: () => show(0),
          End: () => show(last),
          Enter: () => show(),
          ' ': () => show(),
        }
    const action = keys[event.key]
    if (action && !(event.key === ' ' && typed.current.text && Date.now() - typed.current.at < TYPE_AHEAD_DELAY)) {
      event.preventDefault()
      action()
      return
    }
    if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      const index = typeAhead(event.key)
      if (index >= 0) {
        event.preventDefault()
        // Fermé, comme un menu natif : la lettre change directement la valeur.
        if (open) setActive(index)
        else if (options[index].value !== value) onChange(options[index].value)
      }
    }
  }

  return (
    <div className={`${styles.menu} ${styles[variant]}`}>
      <span id={`${id}-label`} className={hideLabel ? styles.hidden : styles.label}>
        {label}
      </span>
      <button
        ref={button}
        id={`${id}-button`}
        type="button"
        role="combobox"
        className={styles.button}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={`${id}-list`}
        aria-labelledby={`${id}-label ${id}-button`}
        aria-activedescendant={open ? `${id}-${active}` : undefined}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        onClick={() => (open ? setOpen(false) : show())}
        onKeyDown={onKeyDown}
        onBlur={() => setOpen(false)}
      >
        <span className={current ? undefined : styles.placeholder}>{current?.label ?? placeholder}</span>
        <svg className={styles.chevron} viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      {error && (
        <span id={`${id}-error`} className={styles.error}>
          {error}
        </span>
      )}
      {open &&
        place &&
        createPortal(
          <ul
            ref={list}
            id={`${id}-list`}
            role="listbox"
            aria-labelledby={`${id}-label`}
            tabIndex={-1}
            className={`${styles.list} ${place.above ? styles.above : ''}`}
            style={{ top: place.top, left: place.left, minWidth: place.minWidth, maxHeight: place.maxHeight }}
            // Le focus reste sur le bouton : cliquer dans la liste ne doit pas le lui retirer.
            onMouseDown={(event) => event.preventDefault()}
          >
            {options.map((option, index) => (
              <li
                key={String(option.value)}
                id={`${id}-${index}`}
                role="option"
                aria-selected={index === selected}
                className={`${styles.option} ${index === active ? styles.active : ''}`}
                onPointerMove={() => setActive(index)}
                onClick={() => choose(index)}
              >
                {option.label}
              </li>
            ))}
          </ul>,
          document.body,
        )}
    </div>
  )
}

export default Menu
