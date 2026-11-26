import { useState } from 'react'
import type { Character } from '../api/characters'
import { useIgnore } from '../lib/useIgnore'
import { useMe } from '../lib/useMe'
import Button from './Button'
import styles from './IgnoreControl.module.css'

/** Sur la fiche d'un autre : l'ignorer, après une courte explication de ce que ça fait. */
export function IgnoreButton({ character }: { character: Character }) {
  const me = useMe()
  const [asking, setAsking] = useState(false)
  const { ignore } = useIgnore(character.id, character.name)
  if (!me.data || character.is_mine || character.ignored) return null

  if (!asking) {
    return (
      <button type="button" className={`action-link ${styles.open}`} onClick={() => setAsking(true)}>
        Ignorer
      </button>
    )
  }
  return (
    <div className={styles.panel}>
      <p>
        {character.name} n'apparaîtra plus dans tes listes : l'annuaire, « Qui traîne ici ? », les histoires du serveur,
        l'accueil. Personne n'en saura rien, pas même son joueur. Sa fiche reste ouverte par un lien.
      </p>
      <p className="hint">Pour ce qui enfreint les règles, mieux vaut signaler.</p>
      <div className={styles.actions}>
        <Button variant="secondary" onClick={() => setAsking(false)}>
          Annuler
        </Button>
        <Button busy={ignore.isPending} onClick={() => ignore.mutate()}>
          Ignorer {character.name}
        </Button>
      </div>
    </div>
  )
}

/** En haut d'une fiche ignorée : le rappeler, et pouvoir revenir en arrière. */
export function IgnoredBanner({ character }: { character: Character }) {
  const { unignore } = useIgnore(character.id, character.name)
  if (!character.ignored) return null
  return (
    <div className={styles.banner} role="status">
      <span>Tu ignores ce personnage : il n'apparaît plus dans tes listes.</span>
      <Button variant="secondary" busy={unignore.isPending} onClick={() => unignore.mutate()}>
        Ne plus l'ignorer
      </Button>
    </div>
  )
}
