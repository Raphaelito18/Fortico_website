# Sauvegarde et restauration FORTICO

Procédure proposée pour le futur environnement de production ; aucune sauvegarde, suppression, restauration ni modification de base n'a été effectuée dans le cadre de cet audit.

## Périmètre à sauvegarder

1. PostgreSQL : données métier, utilisateurs/admins, migrations appliquées, métadonnées et références de fichiers. Export cohérent au format custom PostgreSQL (`pg_dump -Fc`).
2. `backend/media/` : fichiers publics éventuellement présents. Aujourd'hui les images applicatives passent également par le stockage privé contrôlé par Django ; ne pas supposer ce dossier vide sans inventaire.
3. `backend/private_media/` : images et documents servis via les endpoints Django. Ces fichiers ne doivent jamais être placés sous le webroot ni dans une archive publiquement accessible.
4. Configuration d'exploitation : code/révision, versions dépendances, fichiers de config non secrets, valeurs de variables et procédures. Les vraies valeurs secrètes sont sauvegardées séparément, chiffrées et à accès restreint ; pas de `.env` en clair dans les archives ordinaires.
5. `backend/staticfiles/` et `frontend/dist/` sont reconstruisibles depuis la révision de code et les dépendances : conserver la révision et les paramètres de build, et les inclure dans l'artefact de release si la politique l'exige, mais la sauvegarde de données doit prioriser DB et uploads.

## Création d'une sauvegarde (Linux, à adapter au serveur choisi)

Utiliser un compte d'exploitation autorisé et un répertoire privé dédié, chiffré au repos et hors du webroot. Exporter `DB_NAME`, `DB_USER`, `DB_HOST` et `DB_PORT` depuis le gestionnaire de configuration ; configurer le mot de passe PostgreSQL via un fichier `.pgpass` temporaire à droits stricts (`0600`)/secret file, sans le placer dans la ligne de commande ou l'historique shell. Les rôles et droits PostgreSQL sont des éléments d'infrastructure à sauvegarder séparément.

```sh
umask 077
backup_dir=/var/backups/fortico
stamp=$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$backup_dir"
pg_dump --format=custom --no-owner --file="$backup_dir/db-$stamp.dump" \
  --dbname="$DB_NAME" --username="$DB_USER" --host="$DB_HOST" --port="$DB_PORT"
tar --create --gzip --file="$backup_dir/uploads-$stamp.tar.gz" \
  -C /srv/fortico/backend media private_media
sha256sum "$backup_dir/db-$stamp.dump" "$backup_dir/uploads-$stamp.tar.gz" \
  > "$backup_dir/SHA256SUMS-$stamp"
```

Adapter chemins et mode d'authentification à l'hébergeur. Le fichier contenant les sommes de contrôle ne remplace ni le chiffrement ni la vérification d'intégrité. Éviter d'archiver un `.env` ou un dump sur un volume public. Restreindre accès, chiffrer avant transfert vers un stockage séparé, surveiller la réussite et appliquer la rétention approuvée.

## Vérification périodique

- Vérifier le code de sortie, la taille, l'horodatage et les sommes de contrôle.
- Vérifier le chiffrement et les droits d'accès aux archives.
- Déclencher une alerte si une sauvegarde manque ou échoue.
- Faire un test de restauration périodique dans un PostgreSQL et un dossier de fichiers isolés, avec les mêmes versions majeures et une copie de test. Noter durée, cohérence fichier/DB et étapes manuelles.

## Restauration dans un environnement isolé

Cette procédure est conçue pour un nouveau nom de base vide explicitement dédié au test. Ne pas viser le nom de production. Avant la commande, vérifier le serveur et la cible via les informations d'environnement et faire confirmer que la base cible est temporaire.

```sh
createdb --host "$RESTORE_PGHOST" --username "$RESTORE_PGUSER" "$RESTORE_TEST_DB"
pg_restore --host "$RESTORE_PGHOST" --username "$RESTORE_PGUSER" \
  --dbname "$RESTORE_TEST_DB" --no-owner --exit-on-error \
  /secure/backup/db-TIMESTAMP.dump
mkdir -p /srv/fortico-restore-test/backend
 tar --extract --gzip --file=/secure/backup/uploads-TIMESTAMP.tar.gz \
  -C /srv/fortico-restore-test/backend
```

`RESTORE_TEST_DB` doit être un nom temporaire qui n'existe pas dans l'environnement réel ; en cas de doute, arrêter. Les variables ci-dessus sont des placeholders, non fournies. Ne pas ajouter `--clean` ou `--create` : la restauration doit remplir une base isolée vide et ne pas supprimer d'objets existants. Ensuite, vérifier les migrations, comptes admin sans afficher de credentials, comptages agrégés, accès API et fichiers au moyen de contrôles non destructifs. Garder le stockage test séparé, puis éliminer l'environnement temporaire selon la procédure de l'hébergeur uniquement après validation et autorisation opérationnelle.

## Paramètres à décider par FORTICO

Fréquence, sauvegarde PITR/WAL ou snapshots, RPO, RTO, rétention, lieu secondaire, clés de chiffrement, responsables et cadence d'exercice de restauration. Aucune de ces valeurs n'est présumée ici.
