# Mesure la propagation LDAP -> Keycloak.
# Prerequis : client public "probe" avec Direct access grants dans le realm polycorp (lab seulement, a supprimer ensuite).
Set-Location (Split-Path $PSScriptRoot -Parent)
$KC = "http://localhost:8180/realms/polycorp/protocol/openid-connect/token"
$ADMIN = "cn=admin,dc=polycorp,dc=com"

function Tok($u, $p) {
    try { Invoke-RestMethod -Method Post -Uri $KC -Body @{grant_type = 'password'; client_id = 'probe'; username = $u; password = $p} } catch { $null }
}

function Roles($u, $p) {
    $t = Tok $u $p
    if (-not $t) { return @() }
    $x = $t.access_token.Split('.')[1].Replace('-', '+').Replace('_', '/')
    $x = $x.PadRight($x.Length + (4 - $x.Length % 4) % 4, '=')
    ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($x)) | ConvertFrom-Json).realm_access.roles
}

if (-not (Tok emma 'Polycorp-TP4!')) { throw "Client probe absent ou mot de passe d'emma invalide" }

"--- Mot de passe d'alice"
$sw = [Diagnostics.Stopwatch]::StartNew()
docker compose exec -T ldap ldappasswd -x -D $ADMIN -w admin -s 'Nouveau456!' uid=alice,ou=people,dc=polycorp,dc=com
while (-not (Tok alice 'Nouveau456!')) { Start-Sleep -Milliseconds 200 }
"nouveau mot de passe accepte apres $([math]::Round($sw.Elapsed.TotalSeconds, 2)) s"
"ancien mot de passe encore accepte ? " + $(if (Tok alice 'Polycorp-TP4!') { 'OUI' } else { 'non' })
docker compose exec -T ldap ldappasswd -x -D $ADMIN -w admin -s 'Polycorp-TP4!' uid=alice,ou=people,dc=polycorp,dc=com

"--- Groupe : emma rejoint rh"
$sw.Restart()
"dn: cn=rh,ou=groups,dc=polycorp,dc=com`nchangetype: modify`nadd: member`nmember: uid=emma,ou=people,dc=polycorp,dc=com`n" |
    docker compose exec -T ldap ldapmodify -x -D $ADMIN -w admin
while ((Roles emma 'Polycorp-TP4!') -notcontains 'rh') { Start-Sleep -Milliseconds 500 }
"role rh visible pour emma apres $([math]::Round($sw.Elapsed.TotalSeconds, 2)) s"
"dn: cn=rh,ou=groups,dc=polycorp,dc=com`nchangetype: modify`ndelete: member`nmember: uid=emma,ou=people,dc=polycorp,dc=com`n" |
    docker compose exec -T ldap ldapmodify -x -D $ADMIN -w admin
