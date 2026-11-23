import { normalize } from '../lib/text'
import Field from './Field'
import styles from './HangoutsEditor.module.css'
import Suggestions from './Suggestions'

export type HangoutDraft = { area: string; x: string; y: string; label: string; habits: string }

export const MAX_HANGOUTS = 3

const EMPTY_HANGOUT: HangoutDraft = { area: '', x: '', y: '', label: '', habits: '' }

/** Un lieu déjà épinglé sur le serveur, par d'autres ou par soi. */
export type KnownPlace = { area: string; x: number; y: number; label: string | null; count: number }

const keyOf = (p: { area: string; x: number | string; y: number | string }) => `${normalize(p.area)}|${p.x}|${p.y}`

/**
 * Les lieux qui ressemblent à ce que la personne tape, les plus fréquentés d'abord.
 * Seulement tant que le lieu n'a pas ses coordonnées : une fois rempli, on ne dérange plus.
 * Jamais un lieu déjà présent sur la fiche : il serait refusé en double.
 */
function suggestionsFor(hangout: HangoutDraft, known: KnownPlace[], used: Set<string>): KnownPlace[] {
  if (hangout.x !== '' && hangout.y !== '') return []
  const typed = [hangout.label, hangout.area].map(normalize).filter(Boolean)
  return known
    .filter((place) => !used.has(keyOf(place)))
    .filter((place) => {
      if (typed.length === 0) return true
      const haystack = normalize(`${place.label ?? ''} ${place.area}`)
      return typed.some((word) => haystack.includes(word))
    })
    .slice(0, 4)
}

type Props = {
  value: HangoutDraft[]
  onChange: (value: HangoutDraft[]) => void
  error?: string
  /** Les lieux déjà épinglés sur le serveur, à proposer pendant la saisie. */
  known?: KnownPlace[]
}

/** Les lieux de prédilection d'un personnage : trois au plus, chacun avec ses coordonnées. */
function HangoutsEditor({ value, onChange, error, known = [] }: Props) {
  function update(index: number, changes: Partial<HangoutDraft>) {
    onChange(value.map((hangout, i) => (i === index ? { ...hangout, ...changes } : hangout)))
  }
  // Une coordonnée garde seulement un signe moins au début et des chiffres.
  const used = new Set(value.filter((h) => h.x !== '' && h.y !== '').map(keyOf))
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
          <Suggestions
            title="Déjà épinglés sur ce serveur, un clic pour reprendre :"
            items={suggestionsFor(hangout, known, used).map((place) => ({
              key: keyOf(place),
              label: place.label ?? place.area,
              detail: `${place.label ? `${place.area} ` : ''}[${place.x}, ${place.y}] · ${place.count} habitué${place.count > 1 ? 's' : ''}`,
            }))}
            onPick={(key) => {
              const place = known.find((p) => keyOf(p) === key)
              if (place) update(index, { area: place.area, x: String(place.x), y: String(place.y), label: place.label ?? '' })
            }}
          />
          <Field label="Nom du lieu" name={`label-${index}`} value={hangout.label} onChange={(label) => update(index, { label })} maxLength={60} hint="Facultatif : Taverne du Bouftou Ivre…" />
          <Field label="Ses habitudes là-bas" name={`habits-${index}`} value={hangout.habits} onChange={(habits) => update(index, { habits })} maxLength={200} hint="Facultatif : souvent le soir, accoudé au comptoir, dos au mur…" />
          <button type="button" className={styles.remove} onClick={() => onChange(value.filter((_, i) => i !== index))}>
            Retirer ce lieu
          </button>
        </fieldset>
      ))}
      {error && (
        <p className={styles.error} role="alert" data-error tabIndex={-1}>
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
