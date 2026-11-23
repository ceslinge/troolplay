# Feuille de route

## 1. Cadrage
- [x] Idée et cible
- [x] Définir le parcours central
- [ ] Valider la V1
- [ ] Interroger des rôlistes
- [ ] Choisir le nom

## 2. Conception
- [x] Premier schéma de base
- [ ] Valider les permissions
- [x] Premières maquettes : accueil, page Communauté, fiche
- [ ] Maquette d'écriture d'une histoire
- [ ] Contrat d'API

## 3. Fondations
- [ ] Installer Docker
- [x] Squelette backend
- [ ] Squelette frontend, `.env.example`
- [ ] Compose : le projet se lance en une commande
- [x] Linters et tests du backend

## 4. Premier déploiement
- [ ] VPS : SSH par clé, pare-feu, base jamais exposée
- [ ] Domaine et HTTPS
- [ ] Hello World en ligne

## 5. CI/CD
- [x] Tests sur chaque PR
- [ ] Déploiement au merge sur main

## 6. Développement
- [ ] Mentions légales, confidentialité et règles d'usage en ligne avant les premiers comptes
- [ ] Alpha : stories 1 à 7, une issue et une PR chacune
- [ ] Test avec 3 à 5 rôlistes
- [ ] V1 publique : stories 8 et 9

## 7. Sécurité
- [ ] Tests de permissions (IDOR, fuite de user_id)
- [ ] XSS, CSRF, rate limiting
- [ ] Revue OWASP Top 10

## 8. Légal
- [ ] Écrire à Ankama
- [ ] Âge minimum, signalement
- [ ] Export et suppression des données, purge des preuves

## 9. Lancement
- [ ] Emails : SPF, DKIM, DMARC
- [ ] Mobile, accessibilité, aperçus de liens
- [ ] 10 à 15 fiches avant l'annonce
- [ ] Lancement sur un serveur de jeu d'abord, avec un meneur RP

## 10. Exploitation
- [ ] Logs et alertes
- [ ] Sauvegardes et restauration testée
- [ ] Mises à jour

## Idées
À noter ici sans alourdir la V1.
- Événements, notifications, chat
- Gazette du serveur
- Rappel par mail ou retrait automatique des personnages inactifs
- Grille jour × créneau, si les cases ne suffisent pas
- Avatars générés à partir du personnage en jeu
- Pages de tavernes
- Tofu voyageur : des lettres d'un personnage à un autre, sans chat
- Rumeurs glissées par d'autres personnages, publiées si le propriétaire accepte
- « Ceux qui l'ont croisé » sur la fiche, tiré des histoires où le personnage apparaît
- Coups de cœur classés par les favoris, sans compteur public
