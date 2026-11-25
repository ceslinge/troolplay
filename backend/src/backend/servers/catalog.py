"""Les serveurs officiels d'Ankama, jeu par jeu.

Pour ajouter un serveur qu'Ankama vient d'ouvrir : l'écrire ici, puis lancer
`uv run python -m backend.servers.sync` (aussi lancé à chaque déploiement).
Un serveur qui ferme ne s'enlève pas d'ici : un admin le ferme depuis l'Espace équipe,
et les fiches qui y vivent restent lisibles. Un serveur renommé depuis l'Espace équipe
garde ici son ancien nom : il est reconnu, et ne revient pas en double.

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
