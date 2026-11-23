"""Les serveurs officiels d'Ankama, jeu par jeu.

Pour ajouter un serveur qu'Ankama vient d'ouvrir : l'écrire ici, puis lancer
`uv run python -m backend.servers.sync` (aussi lancé à chaque déploiement).
Un serveur qui ferme ne s'enlève pas d'ici : on le ferme en base (is_active),
pour que les fiches qui y vivent restent lisibles. L'Espace équipe (#81) le fera depuis le site.

Relevé sur les sites officiels le 2026-11-24.
"""

SERVERS: dict[str, tuple[str, ...]] = {
    "dofus": (
        "Brial",
        "Dakal",
        "Draconiros",
        "Hell Mina",
        "Imagiro",
        "Kourial",
        "Mikhal",
        "Ombre",
        "Orukam",
        "Rafal",
        "Salar",
        "Tal Kasha",
        "Tylezia",
    ),
    "touch": ("Blair", "Kelerog", "Talok", "Tiliwan"),
    "retro": ("Allisteria", "Boune", "Fallanster"),
}
