$ErrorActionPreference = 'Stop'
$kc = 'http://localhost:8180'
$t = (Invoke-RestMethod -Method Post -Uri "$kc/realms/master/protocol/openid-connect/token" -Body @{grant_type='password';client_id='admin-cli';username='admin';password='admin'}).access_token
$h = @{Authorization = "Bearer $t"}
function J($u) { (Invoke-WebRequest -UseBasicParsing -Uri $u -Headers $h).Content | ConvertFrom-Json | ForEach-Object { $_ } }
$b = "$kc/admin/realms/polycorp"

$p = J "$b/components?type=org.keycloak.storage.UserStorageProvider" | Select-Object -First 1
$m = J "$b/components?parent=$($p.id)&type=org.keycloak.storage.ldap.mappers.LDAPStorageMapper" | Where-Object name -eq 'first name'
"avant : first name <- $($m.config.'ldap.attribute')"
$m.config.'ldap.attribute' = @('givenName')
Invoke-WebRequest -UseBasicParsing -Method Put -Uri "$b/components/$($m.id)" -Headers $h -ContentType 'application/json' -Body ($m | ConvertTo-Json -Depth 10) | Out-Null
$r = Invoke-RestMethod -Method Post -Uri "$b/user-storage/$($p.id)/sync?action=triggerFullSync" -Headers $h
"apres : first name <- givenName ; synchro : $($r.status)"
J "$b/users?max=10" | ForEach-Object { "  $($_.username) : $($_.firstName) $($_.lastName)" }
