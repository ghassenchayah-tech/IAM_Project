# A lancer une fois, apres le demarrage de l'annuaire.
Set-Location (Split-Path $PSScriptRoot -Parent)
docker compose cp ldap/02-acl.ldif ldap:/tmp/02-acl.ldif
docker compose exec ldap ldapmodify -Y EXTERNAL -H ldapi:/// -f /tmp/02-acl.ldif
