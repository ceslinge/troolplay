// L'image des aperçus de liens (#53) : le sceau et le logo sur le bois du panneau.
// Tout vient des fichiers du site : refaire l'image après un changement de logo.
//
//   npm run preview-image
//
// Il faut Chromium (ou Chrome) : la page composée est photographiée en 600 × 600.
// CHROMIUM : le navigateur à lancer. Un Chromium installé en snap ne voit pas /tmp :
// PREVIEW_TMP=~/snap/chromium/common lui donne un dossier de travail qu'il peut lire.
import { execFileSync } from 'node:child_process'
import { copyFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const css = readFileSync(join(root, 'src/index.css'), 'utf8')
const seal = readFileSync(join(root, 'public/favicon.svg'), 'utf8')
const paths = readFileSync(join(root, 'src/components/wordmarkPaths.ts'), 'utf8')
const value = (name) => paths.match(new RegExp(`${name} = '([^']+)'`))[1]

// Le bois et les couleurs du site, tels quels : la règle body et les variables de :root.
const rootVars = css.match(/:root \{[^}]+\}/)[0]
const body = css.match(/\nbody \{[\s\S]+?\n\}/)[0]

const html = `<!doctype html>
<meta charset="utf-8">
<style>
${rootVars}
${body}
html, body { width: 600px; height: 600px; overflow: hidden; }
body { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 36px; }
.seal { width: 260px; height: 260px; filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.45)); }
.mark { height: 92px; width: auto; color: var(--papier); filter: drop-shadow(0 2px 3px rgba(0, 0, 0, 0.5)); }
.mark .marked { fill: var(--laiton); }
</style>
<div class="seal">${seal.replace('<svg ', '<svg width="260" height="260" ')}</div>
<svg class="mark" viewBox="${value('WORDMARK_VIEWBOX')}">
  <path fill="currentColor" d="${value('WORDMARK_PLAIN')}"/>
  <path class="marked" d="${value('WORDMARK_MARKED')}"/>
</svg>
`

const dir = mkdtempSync(join(process.env.PREVIEW_TMP ?? tmpdir(), 'apercu-'))
writeFileSync(join(dir, 'apercu.html'), html)
const shot = join(dir, 'apercu.png')
const out = join(root, 'public/apercu.png')
const browser = process.env.CHROMIUM ?? 'chromium'
execFileSync(browser, ['--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=600,600', `--screenshot=${shot}`, `file://${join(dir, 'apercu.html')}`], { stdio: 'ignore' })
copyFileSync(shot, out)
console.log(`Image écrite : ${out}`)
