"""Les emails du site.

En développement, rien ne part : chaque email s'affiche dans le terminal du backend.
Le vrai envoi viendra avec la mise en ligne, sans changer les appels.
"""


def send_email(to: str, subject: str, body: str) -> None:
    print(f"\n--- Email pour {to} ---\nObjet : {subject}\n\n{body}\n---\n", flush=True)
