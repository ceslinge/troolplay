import { Fragment, type ReactNode } from 'react'
import styles from './StoryText.module.css'

// *italique* ou **gras**, sur une seule ligne, sans espace juste après l'ouverture ni juste avant la fermeture.
const MARK = /\*\*(?=\S)(.+?)(?<=\S)\*\*|\*(?=\S)(.+?)(?<=\S)\*/

/** Une ligne, avec son italique et son gras. Un astérisque seul reste un astérisque. */
function inline(text: string, key: string): ReactNode[] {
  const nodes: ReactNode[] = []
  let rest = text
  let n = 0
  for (let match = MARK.exec(rest); match; match = MARK.exec(rest)) {
    if (match.index > 0) nodes.push(rest.slice(0, match.index))
    const [, bold, italic] = match
    // Le gras peut contenir de l'italique : « **un *vrai* cri** ».
    nodes.push(
      bold !== undefined ? (
        <strong key={`${key}-${n}`}>{inline(bold, `${key}-${n}`)}</strong>
      ) : (
        <em key={`${key}-${n}`}>{italic}</em>
      ),
    )
    n += 1
    rest = rest.slice(match.index + match[0].length)
  }
  if (rest) nodes.push(rest)
  return nodes
}

/**
 * Le texte d'une histoire, mis en page : une ligne vide sépare deux paragraphes, un simple
 * retour à la ligne reste un retour à la ligne. Seuls *italique* et **gras** sont mis en forme :
 * rien d'autre n'est interprété, et surtout pas du HTML.
 */
function StoryText({ body }: { body: string }) {
  const paragraphs = body
    .replace(/\r\n?/g, '\n')
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean)

  return (
    <div className={styles.text}>
      {paragraphs.map((paragraph, p) => (
        <p key={p}>
          {paragraph.split('\n').map((line, l) => (
            <Fragment key={l}>
              {l > 0 && <br />}
              {inline(line, `${p}-${l}`)}
            </Fragment>
          ))}
        </p>
      ))}
    </div>
  )
}

export default StoryText
