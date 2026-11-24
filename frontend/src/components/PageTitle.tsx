/**
 * Le titre de l'onglet. React le place dans <head> ; les lecteurs d'écran l'annoncent
 * quand on change de page, et il distingue les onglets ouverts.
 */
function PageTitle({ children }: { children?: string }) {
  return <title>{children ? `${children} · tRoolPlay` : 'tRoolPlay'}</title>
}

export default PageTitle
