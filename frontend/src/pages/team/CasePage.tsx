import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router'
import { ApiError } from '../../api/client'
import { type CaseDetail, type Decision, decide, fetchCase, setHidden, type Target } from '../../api/moderation'
import Button from '../../components/Button'
import PageTitle from '../../components/PageTitle'
import ReasonForm from '../../components/ReasonForm'
import Sheet from '../../components/Sheet'
import { useToast } from '../../lib/toast'
import { DECISION_HINTS, DECISION_LABELS, REASON_LABELS, ROLE_LABELS, teamDate } from '../../lib/moderation'
import TeamGuard from './TeamGuard'
import styles from './Team.module.css'

const SLUG: Record<string, Target> = { personnage: 'character', histoire: 'story' }

function contentLink(c: CaseDetail): string {
  return c.target === 'character' ? `/personnages/${c.target_id}` : `/histoires/${c.target_id}`
}

/** Le bilan de qui signale : de quoi repérer un abus qui se répète. */
function ReporterLine({ r }: { r: CaseDetail['reports'][number]['reporter'] }) {
  if (r.id === null) return <span className={styles.muted}>Compte supprimé depuis</span>
  return (
    <span className={styles.muted}>
      Par le <Link to={`/equipe/comptes/${r.id}`}>compte n°{r.id}</Link> : {r.reports_sent} signalement
      {r.reports_sent > 1 ? 's' : ''}, {r.founded} fondé{r.founded > 1 ? 's' : ''}, {r.abusive} abusif{r.abusive > 1 ? 's' : ''}
      {r.reporting_revoked && ' · droit de signaler retiré'}
    </span>
  )
}

function Case({ target, id }: { target: Target; id: number }) {
  const queryClient = useQueryClient()
  const toast = useToast()
  const query = useQuery({ queryKey: ['moderation', 'case', target, id], queryFn: () => fetchCase(target, id) })
  const [acting, setActing] = useState<'hide' | 'decide' | null>(null)
  const [decision, setDecision] = useState<Decision | null>(null)

  async function refresh() {
    setActing(null)
    setDecision(null)
    await queryClient.invalidateQueries({ queryKey: ['moderation'] })
  }

  const hide = useMutation({
    mutationFn: (reason: string) => setHidden(target, id, !query.data!.hidden, reason),
    onSuccess: async (r) => {
      toast.show(r.detail, 'success')
      await refresh()
    },
  })
  const close = useMutation({
    mutationFn: (reason: string) => decide(target, id, decision!, reason),
    onSuccess: async () => {
      toast.show('Dossier tranché.', 'success')
      await refresh()
    },
  })

  if (query.isPending) return null
  if (query.isError) {
    const missing = query.error instanceof ApiError && query.error.status === 404
    return <p className={styles.muted}>{missing ? 'Aucun signalement pour ce contenu.' : 'Impossible de charger ce dossier.'}</p>
  }
  const c = query.data
  const pending = c.reports.filter((r) => !r.handled_at)

  return (
    <>
      <PageTitle>{`Dossier : ${c.label}`}</PageTitle>
      <div className={styles.head}>
        <h1>{c.label}</h1>
        <Link to="/equipe/signalements" className={styles.crumb}>
          Tous les dossiers
        </Link>
      </div>

      <Sheet seed={`dossier-${target}-${id}`} contentClassName={styles.card}>
        <dl className={styles.facts}>
          <dt>Contenu</dt>
          <dd>
            {c.target === 'character' ? 'Une fiche' : 'Une histoire'}
            {c.exists ? (
              <>
                {' · '}
                <Link to={contentLink(c)}>l'ouvrir sur le site</Link>
                {c.hidden && (c.auto_hidden ? ' · masqué automatiquement' : ' · masqué')}
              </>
            ) : (
              ', supprimée depuis : seules les copies restent'
            )}
          </dd>
          <dt>Propriétaire</dt>
          <dd>
            {c.owner ? (
              <>
                <Link to={`/equipe/comptes/${c.owner.id}`}>Compte n°{c.owner.id}</Link> · {ROLE_LABELS[c.owner.role]} ·{' '}
                {c.owner.characters.map((ch) => ch.name).join(', ') || 'aucun personnage'}
                {c.owner.suspended && ' · suspendu'}
              </>
            ) : (
              'Un PNJ, ou un compte supprimé'
            )}
          </dd>
          <dt>Signalements</dt>
          <dd>
            {pending.length} en attente, {c.total_reports} en tout
          </dd>
        </dl>

        {acting === null && (
          <div className={styles.actions}>
            {c.exists && (
              <Button variant={c.hidden ? 'secondary' : 'danger'} onClick={() => setActing('hide')}>
                {c.hidden ? 'Rétablir' : 'Masquer'}
              </Button>
            )}
            {pending.length > 0 && <Button onClick={() => setActing('decide')}>Trancher le dossier</Button>}
          </div>
        )}
        {c.auto_hidden && acting === null && (
          <p className={styles.muted}>
            Plusieurs membres fiables l'ont signalé : il est caché en attendant ta décision. « Sans suite » ou « Abusif » le
            rétablit tout seul et prévient son auteur ; « Fondé » le laisse masqué.
          </p>
        )}
        {acting === 'hide' && (
          <ReasonForm
            title={c.hidden ? 'Rétablir ce contenu' : 'Masquer ce contenu'}
            confirm={c.hidden ? 'Rétablir' : 'Masquer'}
            danger={!c.hidden}
            busy={hide.isPending}
            error={hide.error}
            onConfirm={(reason) => hide.mutate(reason)}
            onCancel={() => setActing(null)}
          />
        )}
        {acting === 'decide' && (
          <ReasonForm
            title="Trancher le dossier"
            hint="Gardée au journal. Les copies des signalements seront effacées."
            confirm="Trancher"
            busy={close.isPending}
            error={close.error}
            ready={decision !== null}
            onConfirm={(reason) => close.mutate(reason)}
            onCancel={() => setActing(null)}
          >
            <fieldset className={styles.choices}>
              {(Object.keys(DECISION_LABELS) as Decision[]).map((d) => (
                <label key={d}>
                  <input type="radio" name="decision" checked={decision === d} onChange={() => setDecision(d)} />
                  <span>
                    {DECISION_LABELS[d]}
                    <small>{DECISION_HINTS[d]}</small>
                  </span>
                </label>
              ))}
            </fieldset>
          </ReasonForm>
        )}
      </Sheet>

      <Sheet seed={`dossier-${target}-${id}-signalements`} contentClassName={styles.card}>
        <h2>Les signalements</h2>
        {c.reports
          .slice()
          .reverse()
          .map((r) => (
            <div key={r.id} className={styles.report}>
              <span className={styles.badges}>
                <span className={`${styles.badge} ${r.handled_at ? '' : styles.alert}`}>{REASON_LABELS[r.reason]}</span>
                {r.decision && <span className={styles.badge}>{DECISION_LABELS[r.decision]}</span>}
                <span className={styles.muted}>le {teamDate(r.created_at)}</span>
              </span>
              {r.details && <p>« {r.details} »</p>}
              <ReporterLine r={r.reporter} />
              {r.snapshot && (
                <details className={styles.snapshot}>
                  <summary>Le contenu tel qu'il était signalé</summary>
                  <pre>{snapshotText(r.snapshot)}</pre>
                </details>
              )}
            </div>
          ))}
      </Sheet>
    </>
  )
}

/** La copie, lisible : les champs remplis, sans les détails techniques. */
function snapshotText(snapshot: Record<string, unknown>): string {
  const skip = new Set(['id', 'server', 'character', 'hangouts', 'is_npc', 'is_mine', 'avatar', 'seal', 'gender', 'published'])
  return Object.entries(snapshot)
    .filter(([key, value]) => !skip.has(key) && value !== null && value !== '' && !(Array.isArray(value) && value.length === 0))
    .map(([key, value]) => `${key} : ${Array.isArray(value) ? value.join(', ') : String(value)}`)
    .join('\n\n')
}

function CasePage() {
  const { kind = '', id = '' } = useParams()
  const target = SLUG[kind]
  return (
    <TeamGuard>
      <main className={styles.page}>{target ? <Case target={target} id={Number(id)} /> : <p>Dossier inconnu.</p>}</main>
    </TeamGuard>
  )
}

export default CasePage
