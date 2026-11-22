# Permissions (brouillon à valider)

Chaque ligne deviendra un test.

| Action | Visiteur | Joueur | Propriétaire | Modérateur | Admin |
|---|:-:|:-:|:-:|:-:|:-:|
| Lire une fiche ou une histoire publiée | oui | oui | oui | oui | oui |
| Lire un brouillon | non | non | oui | non | non |
| Lire un contenu masqué | non | non | oui | oui | oui |
| Créer personnage, histoire, favori | non | oui | oui | oui | oui |
| Modifier un contenu | non | non | oui | non | non |
| Supprimer un contenu | non | non | oui | non | oui |
| Signaler | non | oui | non | oui | oui |
| Masquer, traiter un signalement | non | non | non | oui | oui |
| Bannir | non | non | non | oui | oui |
| Savoir quel compte possède un personnage | non | non | oui | à décider | oui |
| Gérer PNJ, serveurs et rôles | non | non | non | non | oui |

## Invariants
- Aucune réponse publique ne contient de user_id.
- Le serveur vérifie qu'un personnage appartient au compte avant d'agir en son nom.
- Le rôle ne peut pas être choisi à l'inscription.
- Les favoris ne sont visibles que de leur propriétaire.
- Une implication n'est visible qu'une fois acceptée, sans acceptation automatique.
- Un personnage impliqué peut se retirer à tout moment.
