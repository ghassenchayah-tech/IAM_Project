$ErrorActionPreference = 'Stop'
$kc = 'http://localhost:8180'
$t = (Invoke-RestMethod -Method Post -Uri "$kc/realms/master/protocol/openid-connect/token" -Body @{grant_type='password';client_id='admin-cli';username='admin';password='admin'}).access_token
$h = @{Authorization = "Bearer $t"}
function J($u) { (Invoke-WebRequest -UseBasicParsing -Uri $u -Headers $h).Content | ConvertFrom-Json | ForEach-Object { $_ } }
function Send($m, $u, $o) { Invoke-WebRequest -UseBasicParsing -Method $m -Uri $u -Headers $h -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes(($o | ConvertTo-Json -Depth 10))) | Out-Null }
$b = "$kc/admin/realms/polycorp"

# Attribut SAML "groups"
$s = J "$b/clients?clientId=http://localhost:8181/saml/metadata" | Select-Object -First 1
if (-not ($s.protocolMappers | Where-Object name -eq 'groups')) {
    Send Post "$b/clients/$($s.id)/protocol-mappers/models" @{ name = 'groups'; protocol = 'saml'; protocolMapper = 'saml-group-membership-mapper'
        config = @{ 'attribute.name' = 'groups'; 'friendly.name' = 'groups'; 'attribute.nameformat' = 'Basic'; 'single' = 'true'; 'full.path' = 'false' } }
    "SAML : mapper groups ajoute"
}

"=== LDAP provider"
$p = J "$b/components?type=org.keycloak.storage.UserStorageProvider" | Select-Object -First 1
$p.config.PSObject.Properties | Where-Object { $_.Name -ne 'bindCredential' } | ForEach-Object { "  $($_.Name) = $($_.Value -join ',')" }
"=== LDAP mappers"
J "$b/components?parent=$($p.id)&type=org.keycloak.storage.ldap.mappers.LDAPStorageMapper" | ForEach-Object {
    "  - $($_.name) [$($_.providerId)]"
    if ($_.providerId -eq 'group-ldap-mapper') { $_.config.PSObject.Properties | ForEach-Object { "      $($_.Name) = $($_.Value -join ',')" } }
}
"=== SAML client"
$s = J "$b/clients?clientId=http://localhost:8181/saml/metadata" | Select-Object -First 1
$s.attributes.PSObject.Properties | Where-Object { $_.Name -match 'saml' } | ForEach-Object { "  $($_.Name) = $($_.Value)" }
"  redirects = $($s.redirectUris -join ',')"
$s.protocolMappers | ForEach-Object { "  mapper $($_.name) [$($_.protocolMapper)]" }
"=== probe"
(J "$b/clients?clientId=probe" | Measure-Object).Count
"=== groups/roles"
J "$b/groups" | ForEach-Object { "  $($_.name) -> " + ((J "$b/groups/$($_.id)/role-mappings/realm").name -join ', ') }
"=== realm"
$r = J $b
"  accessTokenLifespan=$($r.accessTokenLifespan) ssoSessionIdle=$($r.ssoSessionIdleTimeout)"
