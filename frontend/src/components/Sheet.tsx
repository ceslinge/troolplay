import type { CSSProperties, ReactNode } from 'react'
import { hashString } from '../lib/hash'
import styles from './Sheet.module.css'

type Props = {
  children: ReactNode
  variant?: 'plain' | 'marked' | 'muted'
  edge?: 'torn' | 'straight'
  pinned?: boolean
  as?: 'div' | 'section' | 'article' | 'aside'
  /** Placement de la feuille dans la page (largeur, flex…). */
  className?: string
  /** Mise en page de son contenu. */
  contentClassName?: string
  /** Donne à la feuille une légère inclinaison, toujours la même pour un même texte. */
  seed?: string
  /** De 0 (neuve) à 1 (vieille) : jaunit les bords du papier. */
  age?: number
}

/** Entre -0,4 et +0,4 degré : assez pour le vivant, pas assez pour gêner la lecture. */
function tiltFor(seed: string): string {
  return `${((hashString(seed) % 81) - 40) / 100}deg`
}

/**
 * Une feuille de papier posée sur le panneau.
 * Le support porte l'ombre, le papier porte le bord déchiré :
 * un masque couperait sinon l'ombre avec le bord.
 */
function Sheet({
  children,
  variant = 'plain',
  edge = 'torn',
  pinned = false,
  as: Tag = 'div',
  className = '',
  contentClassName = '',
  seed,
  age = 0,
}: Props) {
  const style = {
    '--tilt': seed ? tiltFor(seed) : '0deg',
    '--age': Math.min(Math.max(age, 0), 1),
  } as CSSProperties

  return (
    <Tag className={`${styles.sheet} ${className}`} style={style}>
      {pinned && <span className={styles.pin} aria-hidden="true" />}
      <div className={`${styles.paper} ${styles[variant]} ${styles[edge]} ${contentClassName}`}>
        {children}
      </div>
    </Tag>
  )
}

export default Sheet
