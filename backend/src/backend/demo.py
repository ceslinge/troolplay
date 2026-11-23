"""Remplit la base de dev avec les personnages des maquettes.

Lancer depuis backend : uv run python -m backend.demo
Ne fait rien si les données de démo sont déjà là.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.accounts.models import User
from backend.characters.models import Character, CharacterHangout
from backend.db import SessionLocal
from backend.servers.models import GameServer

# Un hash impossible : ces comptes ne pourront jamais se connecter.
NO_LOGIN = "!demo"

PLAYERS = ["demo-1", "demo-2", "demo-3", "demo-4"]

TAVERNE = ("Astrub", 5, -18, "Taverne du Bouftou Ivre")
QUAIS = ("Madrestam", 7, -4, "Quais du port")
BIBLIOTHEQUE = ("Bonta", -28, -56, "Bibliothèque")

CHARACTERS = [
    {
        "player": "demo-1",
        "name": "Maëlis Sombrefeu",
        "pronoun": "elle",
        "ingame_name": "Maelis-Sombrefeu",
        "class_": "Crâ",
        "level": 142,
        "hook": "Si c'est pour l'arc, il n'est pas à vendre. "
        "Si c'est pour mon père, assieds-toi.",
        "appearance": "Grande, cape de voyage râpée, un arc bien trop beau "
        "pour le reste de sa tenue.",
        "personality": "Polie avec tout le monde, confiante avec personne.",
        "backstory": "Fille d'un archer de la milice d'Astrub, elle a quitté la "
        "ville après une affaire que personne n'évoque devant elle. Elle est "
        "revenue l'an dernier, seule, et loue une chambre au-dessus de la taverne.",
        "goals": "Le nom de celui qui a signé l'ordre.",
        "flaws": "La rancune. Et le vin, qu'elle boit pour ne pas dormir.",
        "rumors": "On dit qu'elle paie sa chambre avec des kamas qui ne sont "
        "pas à elle.",
        "ooc_note": "Partante pour de l'enquête et des scènes de taverne. "
        "Abordez-la en jeu, elle mord rarement !",
        "play_days": [1, 3, 5],
        "play_periods": ["evening"],
        "hangouts": [(*TAVERNE, "Accoudée au comptoir, dos au mur.")],
    },
    {
        "player": "demo-2",
        "name": "Gorrik le Tanneur",
        "pronoun": "il",
        "class_": "Enutrof",
        "level": 88,
        "hook": "Tout se paie. Même les sourires.",
        "play_days": [6, 7],
        "play_periods": ["afternoon", "evening"],
        "hangouts": [(*TAVERNE, "Toujours la même table, près de la porte.")],
    },
    {
        "player": "demo-3",
        "name": "Lysandre Vey",
        "class_": "Eniripsa",
        "level": 199,
        "hook": "Assieds-toi, tu saignes sur le parquet.",
        "play_days": [2, 4],
        "play_periods": ["evening", "night"],
        "hangouts": [(*TAVERNE, None)],
    },
    {
        "player": "demo-4",
        "name": "Pip Cendremousse",
        "class_": "Ecaflip",
        "level": 61,
        "hook": "Pile, je gagne. Face, tu perds.",
        "play_days": [6, 7],
        "play_periods": ["evening"],
        "hangouts": [(*TAVERNE, "Là où il y a des dés.")],
    },
    {
        "player": "demo-2",
        "name": "Ysolde Brisemer",
        "pronoun": "elle",
        "class_": "Pandawa",
        "level": 175,
        "hook": "Le large ne pose pas de questions.",
        "play_days": [1, 2, 3, 4, 5, 6, 7],
        "play_periods": ["evening"],
        "hangouts": [(*QUAIS, None)],
    },
    {
        "player": "demo-1",
        "name": "Tobias Crochefer",
        "pronoun": "il",
        "class_": "Roublard",
        "level": 120,
        "hook": "Je n'étais pas là. Demande à n'importe qui.",
        "play_days": [5, 6],
        "play_periods": ["night"],
        "hangouts": [(*QUAIS, None)],
    },
    {
        "player": "demo-3",
        "name": "Aldegonde Fervent",
        "pronoun": "elle",
        "class_": "Féca",
        "level": 160,
        "hook": "Chut.",
        "play_days": [1, 2, 3, 4, 5],
        "play_periods": ["morning"],
        "hangouts": [(*BIBLIOTHEQUE, None)],
    },
    {
        "player": "demo-4",
        "name": "Nérée Vifargent",
        "pronoun": "elle",
        "class_": "Xélor",
        "level": 133,
        "hook": "Tu es en retard. Ou moi en avance.",
        "play_days": [3, 7],
        "play_periods": ["morning", "evening"],
        "hangouts": [(*BIBLIOTHEQUE, "Toujours au même rayon, la même heure.")],
    },
    {
        "player": "demo-1",
        "name": "Oswin Bruyère",
        "pronoun": "il",
        "class_": "Sadida",
        "level": 47,
        "hook": "Les arbres de Bonta ont la mémoire courte.",
        "play_days": [6],
        "play_periods": ["afternoon"],
        "hangouts": [(*BIBLIOTHEQUE, None)],
    },
]


def get_or_create_server(session: Session, game: str, name: str) -> GameServer:
    server = session.scalars(
        select(GameServer).where(GameServer.game == game, GameServer.name == name)
    ).one_or_none()
    if server is None:
        server = GameServer(game=game, name=name)
        session.add(server)
        session.flush()
    return server


def load(session: Session) -> bool:
    first = f"{PLAYERS[0]}@example.invalid"
    if session.scalars(select(User).where(User.email == first)).first():
        return False

    ombrelune = get_or_create_server(session, "dofus", "Ombrelune")
    get_or_create_server(session, "dofus", "Vent-Gris")

    users = {}
    for player in PLAYERS:
        users[player] = User(email=f"{player}@example.invalid", password_hash=NO_LOGIN)
        session.add(users[player])
    session.flush()

    for data in CHARACTERS:
        data = dict(data)
        hangouts = data.pop("hangouts")
        player = data.pop("player")
        character = Character(user_id=users[player].id, server_id=ombrelune.id, **data)
        session.add(character)
        session.flush()
        for area, x, y, label, habits in hangouts:
            session.add(
                CharacterHangout(
                    character_id=character.id,
                    area=area,
                    x=x,
                    y=y,
                    label=label,
                    habits=habits,
                )
            )
    return True


def main() -> None:
    with SessionLocal.begin() as session:
        if load(session):
            print(f"{len(CHARACTERS)} personnages de démo ajoutés.")
        else:
            print("Les données de démo sont déjà là, rien à faire.")


if __name__ == "__main__":
    main()
