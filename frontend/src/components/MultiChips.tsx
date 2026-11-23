import type { ChipOption } from './Chips'
import styles from './Chips.module.css'

type Props<T extends string | number> = {
  legend: string
  options: ChipOption<T>[]
  value: T[]
  onChange: (value: T[]) => void
}

/** Comme Chips, mais on peut en choisir plusieurs : un clic ajoute, un second retire. */
function MultiChips<T extends string | number>({ legend, options, value, onChange }: Props<T>) {
  function toggle(option: T) {
    const next = value.includes(option) ? value.filter((v) => v !== option) : [...value, option]
    // On garde l'ordre des options (lundi avant mardi), pas l'ordre des clics.
    onChange(options.map((o) => o.value).filter((v) => next.includes(v)))
  }

  return (
    <fieldset className={styles.group}>
      <legend className={styles.legend}>{legend}</legend>
      <div className={styles.chips}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            className={styles.chip}
            aria-pressed={value.includes(option.value)}
            aria-label={option.title}
            title={option.title}
            onClick={() => toggle(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </fieldset>
  )
}

export default MultiChips
