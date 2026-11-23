import Field from './Field'
import styles from './HangoutsEditor.module.css'

export type HangoutDraft = { area: string; x: string; y: string; label: string; habits: string }

export const MAX_HANGOUTS = 3

const EMPTY_HANGOUT: HangoutDraft = { area: '', x: '', y: '', label: '', habits: '' }

type Props = {
  value: HangoutDraft[]
  onChange: (value: HangoutDraft[]) => void
  error?: string
}

/** Les lieux de prédilection d'un personnage : trois au plus, chacun avec ses coordonnées. */
function HangoutsEditor({ value, onChange, error }: Props) {
  function update(index: number, changes: Partial<HangoutDraft>) {
    onChange(value.map((hangout, i) => (i === index ? { ...hangout, ...changes } : hangout)))
  }
  // Une coordonnée garde seulement un signe moins au début et des chiffres.
  const coordinate = (text: string) => text.replace(/[^\d-]/g, '').replace(/(?!^)-/g, '')

  return (
    <div className={styles.editor}>
      {value.map((hangout, index) => (
        <fieldset key={index} className={styles.place}>
          <legend className={styles.legend}>Lieu {index + 1}</legend>
          <div className={styles.row}>
            <Field label="Zone" name={`area-${index}`} value={hangout.area} onChange={(area) => update(index, { area })} maxLength={40} hint="Astrub, Bonta…" />
            <Field label="X" name={`x-${index}`} value={hangout.x} onChange={(x) => update(index, { x: coordinate(x) })} />
            <Field label="Y" name={`y-${index}`} value={hangout.y} onChange={(y) => update(index, { y: coordinate(y) })} />
          </div>
          <Field label="Nom du lieu" name={`label-${index}`} value={hangout.label} onChange={(label) => update(index, { label })} maxLength={60} hint="Facultatif : Taverne du Bouftou Ivre…" />
          <Field label="Ses habitudes là-bas" name={`habits-${index}`} value={hangout.habits} onChange={(habits) => update(index, { habits })} maxLength={200} hint="Facultatif : accoudé au comptoir, dos au mur…" />
          <button type="button" className={styles.remove} onClick={() => onChange(value.filter((_, i) => i !== index))}>
            Retirer ce lieu
          </button>
        </fieldset>
      ))}
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {value.length < MAX_HANGOUTS ? (
        <button type="button" className={styles.add} onClick={() => onChange([...value, EMPTY_HANGOUT])}>
          Ajouter un lieu
        </button>
      ) : (
        <p className={styles.full}>Trois lieux au plus : les autres le trouveront plus facilement.</p>
      )}
    </div>
  )
}

export default HangoutsEditor
