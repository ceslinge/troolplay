import { hashString } from '../lib/hash'
import styles from './Seal.module.css'

const WAX = ['#7d2a20', '#3f5a3a', '#2f4660', '#5b3a5e', '#7a5a1f', '#40494f', '#6e3b1f', '#35505a']

/** Tant que les sceaux ne sont pas choisis par les joueurs, la couleur vient du nom. */
function waxFor(name: string): string {
  return WAX[hashString(name) % WAX.length]
}

type Props = {
  name: string
  size?: 'sm' | 'lg'
}

function Seal({ name, size = 'sm' }: Props) {
  return (
    <span
      className={`${styles.seal} ${styles[size]}`}
      style={{ background: waxFor(name) }}
      aria-hidden="true"
    >
      {name.charAt(0)}
    </span>
  )
}

export default Seal
