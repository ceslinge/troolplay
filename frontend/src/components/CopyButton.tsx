import { useState } from 'react'
import styles from './CopyButton.module.css'

type Props = {
  text: string
  label: string
}

function CopyButton({ text, label }: Props) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button type="button" className={styles.button} onClick={copy} aria-label={label}>
      {copied ? 'Copié !' : 'Copier'}
    </button>
  )
}

export default CopyButton
