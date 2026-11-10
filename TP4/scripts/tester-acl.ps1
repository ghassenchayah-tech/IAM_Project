# Verifie les droits du compte de service svc-keycloak sur l'annuaire.
Set-Location (Split-Path $PSScriptRoot -Parent)
$SVC = "cn=svc-keycloak,ou=services,dc=polycorp,dc=com"
$PW = 'Svc-Keycloak-TP4!'

"== 1. lecture d'alice par le compte de service (doit fonctionner, sans userPassword)"
docker compose exec -T ldap ldapsearch -x -H ldap://localhost -D $SVC -w $PW -b ou=people,dc=polycorp,dc=com uid=alice uid mail userPassword

"== 2. ecriture par le compte de service (doit echouer : Insufficient access)"
"dn: uid=alice,ou=people,dc=polycorp,dc=com`nchangetype: modify`nreplace: mail`nmail: pirate@evil.test`n" |
    docker compose exec -T ldap ldapmodify -x -H ldap://localhost -D $SVC -w $PW 2>&1 | ForEach-Object { "$_" }

"== 3. lecture de ou=services (doit etre vide)"
docker compose exec -T ldap ldapsearch -x -H ldap://localhost -D $SVC -w $PW -b ou=services,dc=polycorp,dc=com
