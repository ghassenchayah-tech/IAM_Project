"""Rend les sorties de terminal reelles du projet sous forme d'images."""
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "captures"

TERMINAUX = {
    "40-term-acl-compte-service": ("ACL OpenLDAP : tests avec le compte svc-keycloak", r"""PS C:\...\TP4> # 1. lecture d'alice par le compte de service (doit fonctionner, sans userPassword)
PS C:\...\TP4> docker compose exec ldap ldapsearch -x -H ldap://localhost -D $SVC -w $PW -b ou=people,dc=polycorp,dc=com uid=alice uid mail userPassword
dn: uid=alice,ou=people,dc=polycorp,dc=com
uid: alice
mail: alice.martin@polycorp.test

PS C:\...\TP4> # 2. ecriture par le compte de service (doit echouer)
PS C:\...\TP4> ... | docker compose exec -T ldap ldapmodify -x -H ldap://localhost -D $SVC -w $PW
ldap_modify: Insufficient access (50)
modifying entry "uid=alice,ou=people,dc=polycorp,dc=com"

PS C:\...\TP4> # 3. lecture de ou=services (doit etre vide)
PS C:\...\TP4> docker compose exec ldap ldapsearch -x -H ldap://localhost -D $SVC -w $PW -b ou=services,dc=polycorp,dc=com
No such object (32)"""),
    "41-term-hash-admin-vs-service": ("Le hash du mot de passe n'est visible que par l'administrateur de l'annuaire", r"""PS C:\...\TP4> docker compose exec ldap ldapsearch -x -LLL -D cn=admin,dc=polycorp,dc=com -w admin -b ou=people,dc=polycorp,dc=com uid=alice userPassword
dn: uid=alice,ou=people,dc=polycorp,dc=com
userPassword:: e1NTSEF9dWhoWFJEbDlxM0hJbS9wd3lpYktLSGx1bHhiQmFpZXY=        <- {SSHA}... (base64)

PS C:\...\TP4> docker compose exec ldap ldapsearch -x -LLL -D cn=svc-keycloak,ou=services,dc=polycorp,dc=com -w *** -b ou=people,dc=polycorp,dc=com uid=alice userPassword
dn: uid=alice,ou=people,dc=polycorp,dc=com
                                                                           <- aucun userPassword (ACL {1} : by * none)

PS C:\...\TP4> Invoke-WebRequest .../admin/realms/polycorp/users/<alice>/credentials
[{"type":"password","createdDate":-1,"federationLink":"LlILZ4OATqulQNeMxMbCLg"}]
                                                                           <- credential virtuelle fournie par LDAP, aucun secret dans Keycloak"""),
    "42-term-mesure-sans-cache": ("Propagation LDAP -> Keycloak : cache NO_CACHE", r"""PS C:\...\TP4> # script de mesure (equivalent PowerShell de scripts/mesurer.sh, client probe)
--- Mot de passe d'alice
nouveau mot de passe accepte apres 0.32 s
ancien mot de passe encore accepte ? non
--- Groupe : emma rejoint rh
modifying entry "cn=rh,ou=groups,dc=polycorp,dc=com"

role rh visible pour emma apres 0.28 s
modifying entry "cn=rh,ou=groups,dc=polycorp,dc=com"
"""),
    "43-term-mesure-avec-cache": ("Propagation LDAP -> Keycloak : cache MAX_LIFESPAN = 1 min", r"""PS C:\...\TP4> Tok emma 'Polycorp-TP4!' | Out-Null      # emma mise en cache avant le changement
PS C:\...\TP4> # meme script de mesure
--- Mot de passe d'alice
nouveau mot de passe accepte apres 0.26 s
ancien mot de passe encore accepte ? non
--- Groupe : emma rejoint rh
modifying entry "cn=rh,ou=groups,dc=polycorp,dc=com"

role rh visible pour emma apres 51.97 s
modifying entry "cn=rh,ou=groups,dc=polycorp,dc=com"

PS C:\...\TP4> docker compose exec -T ldap ldapsearch -x -LLL -D cn=admin,dc=polycorp,dc=com -w admin -b cn=rh,ou=groups,dc=polycorp,dc=com member
dn: cn=rh,ou=groups,dc=polycorp,dc=com
member: uid=alice,ou=people,dc=polycorp,dc=com                             <- etat initial restaure
"""),
}

GABARIT = """<!doctype html><meta charset=utf-8><style>
body{margin:0;background:#fff;font-family:Segoe UI,Arial}
.f{width:1180px;border-radius:8px;overflow:hidden;box-shadow:0 2px 10px #0003;margin:10px}
.t{background:#2d2d2d;color:#ddd;padding:7px 12px;font-size:13px}
.t span{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:6px}
pre{margin:0;background:#012456;color:#eee;font:13px/1.45 Consolas,monospace;padding:14px 16px;white-space:pre-wrap}
</style><div class=f><div class=t><span style=background:#ff5f56></span><span style=background:#ffbd2e></span>
<span style=background:#27c93f></span>&nbsp; Windows PowerShell - {titre}</div><pre>{texte}</pre></div>"""

with sync_playwright() as p:
    nav = p.chromium.launch(channel="msedge", headless=True)
    pg = nav.new_page(viewport={"width": 1210, "height": 400}, device_scale_factor=2)
    for nom, (titre, texte) in TERMINAUX.items():
        pg.set_content(GABARIT.replace("{titre}", escape(titre)).replace("{texte}", escape(texte)))
        pg.locator(".f").screenshot(path=str(OUT / f"{nom}.png"))
        print("terminal", nom)
    nav.close()
