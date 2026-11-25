import { Link } from 'react-router'
import type { JournalEntry } from '../../api/moderation'

/** Ce que vise une ligne du journal : une histoire, une fiche ou un serveur. */
function JournalTarget({ entry }: { entry: JournalEntry }) {
  if (entry.target_story_id) return <Link to={`/histoires/${entry.target_story_id}`}>une histoire</Link>
  if (entry.target_character_id) return <Link to={`/personnages/${entry.target_character_id}`}>une fiche</Link>
  if (entry.target_server_id) return <span>{entry.target_server_name ?? 'un serveur'}</span>
  return null
}

export default JournalTarget
