import { WORDMARK_MARKED, WORDMARK_PLAIN, WORDMARK_VIEWBOX } from './wordmarkPaths'
import styles from './Wordmark.module.css'

/**
 * Le logo : « tRoolPlay », le R et le P tracés à la plume pour que le RP se lise dans le nom
 * (#108). Des tracés vectoriels plutôt que des polices : rien de plus à télécharger.
 */
function Wordmark({ className }: { className?: string }) {
  return (
    <svg className={`${styles.mark} ${className ?? ''}`} viewBox={WORDMARK_VIEWBOX} aria-hidden="true" focusable="false">
      <path className={styles.plain} d={WORDMARK_PLAIN} />
      <path className={styles.marked} d={WORDMARK_MARKED} />
    </svg>
  )
}

export default Wordmark
