import styles from './Chips.module.css'

export type ChipOption<T extends string | number> = {
  value: T
  label: string
  /** Texte complet, lu par les lecteurs d'écran quand le libellé est abrégé. */
  title?: string
}

type Props<T extends string | number> = {
  legend: string
  options: ChipOption<T>[]
  value: T | undefined
  onChange: (value: T | undefined) => void
}

/** Une rangée de choix : un clic choisit, un second clic désélectionne. */
function Chips<T extends string | number>({ legend, options, value, onChange }: Props<T>) {
  return (
    <fieldset className={styles.group}>
      <legend className={styles.legend}>{legend}</legend>
      <div className={styles.chips}>
        {options.map((option) => {
          const selected = option.value === value
          return (
            <button
              key={option.value}
              type="button"
              className={styles.chip}
              aria-pressed={selected}
              aria-label={option.title}
              title={option.title}
              onClick={() => onChange(selected ? undefined : option.value)}
            >
              {option.label}
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}

export default Chips
