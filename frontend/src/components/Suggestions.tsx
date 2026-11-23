import styles from './Suggestions.module.css'

export type Suggestion = { key: string; label: string; detail?: string }

type Props = {
  title: string
  items: Suggestion[]
  onPick: (key: string) => void
}

/**
 * Ce que d'autres joueurs ont déjà écrit, à reprendre d'un clic.
 * De simples boutons : accessibles au clavier et aux lecteurs d'écran sans rien de plus.
 */
function Suggestions({ title, items, onPick }: Props) {
  if (items.length === 0) {
    return null
  }
  return (
    <div className={styles.box}>
      <span className={styles.title}>{title}</span>
      <div className={styles.items}>
        {items.map((item) => (
          <button key={item.key} type="button" className={styles.item} onClick={() => onPick(item.key)}>
            <span className={styles.label}>{item.label}</span>
            {item.detail && <span className={styles.detail}>{item.detail}</span>}
          </button>
        ))}
      </div>
    </div>
  )
}

export default Suggestions
