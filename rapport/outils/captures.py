"""Rejoue les demonstrations du mini-projet et capture chaque etape (portails 8181/8182 et console Keycloak)."""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

KC = "http://localhost:8180"
SP = "http://localhost:8181"
CL = "http://localhost:8182"
PW = "Polycorp-TP4!"
OUT = Path(__file__).resolve().parent.parent / "captures"
OUT.mkdir(exist_ok=True)


def admin_token():
    data = urllib.parse.urlencode({"grant_type": "password", "client_id": "admin-cli", "username": "admin", "password": "admin"}).encode()
    with urllib.request.urlopen(f"{KC}/realms/master/protocol/openid-connect/token", data) as r:
        return json.load(r)["access_token"]


def api(path, methode="GET"):
    req = urllib.request.Request(f"{KC}/admin/realms/polycorp{path}", method=methode, headers={"Authorization": "Bearer " + admin_token()})
    with urllib.request.urlopen(req) as r:
        corps = r.read()
        return json.loads(corps) if corps else None


def shot(page, nom, full=False, pause=0.6):
    page.wait_for_load_state("networkidle")
    time.sleep(pause)
    page.screenshot(path=str(OUT / f"{nom}.png"), full_page=full)
    print("capture", nom)


def zoom(page, selecteur, nom):
    page.locator(selecteur).first.screenshot(path=str(OUT / f"{nom}.png"))
    print("zoom", nom)


def section_ldap(page, titre, nom):
    page.locator("[class*='jump-links'] >> text=" + titre).first.click()
    time.sleep(1.5)
    page.screenshot(path=str(OUT / f"{nom}.png"))
    print("capture", nom)


def login_kc(page, user):
    page.wait_for_selector("#username", timeout=15000)
    page.fill("#username", user)
    page.fill("#password", PW)
    page.click("#kc-login")
    page.wait_for_load_state("networkidle")


def flux_notes(page, ecriture=True, prefixe="", capturer=True):
    page.goto(CL + "/")
    if ecriture:
        page.check("input[value='notes.write']")
    page.check("input[value='profile']")
    if capturer:
        shot(page, f"{prefixe}demande")
    page.click("button:has-text('Préparer la demande')")
    page.wait_for_load_state("networkidle")
    if capturer:
        shot(page, f"{prefixe}demande-prete", full=True)
    page.click("a:has-text('Envoyer le navigateur vers Keycloak')")
    page.wait_for_load_state("networkidle")
    return page


def echanger(page):
    page.click("button:has-text('Échanger le code contre les jetons')")
    page.wait_for_load_state("networkidle")


def api_action(page, valeur):
    page.goto(CL + "/api")
    page.click(f"button[value='{valeur}']")
    page.wait_for_load_state("networkidle")


def console(page, fragment):
    # La console garde le realm courant si seul le fragment change : on recharge.
    page.goto(f"{KC}/admin/master/console/#/polycorp/{fragment}")
    page.reload()
    page.wait_for_load_state("networkidle")
    time.sleep(3)


def main():
    api("/logout-all", "POST")
    users = {u["username"]: u for u in api("/users?max=20")}
    ldap = api("/components?type=org.keycloak.storage.UserStorageProvider")[0]
    mappers = api(f"/components?parent={ldap['id']}&type=org.keycloak.storage.ldap.mappers.LDAPStorageMapper")
    gmapper = next(m for m in mappers if m["providerId"] == "group-ldap-mapper")
    groupes = {g["name"]: g for g in api("/groups")}
    clients = {c["clientId"]: c for c in api("/clients")}
    saml = clients[SP + "/saml/metadata"]
    notes = clients["portail-notes"]

    with urllib.request.urlopen(f"{KC}/realms/polycorp/protocol/saml/descriptor") as r:
        (OUT.parent / "idp-metadata.xml").write_bytes(r.read())

    with sync_playwright() as p:
        nav = p.chromium.launch(channel="msedge", headless=True)
        u = nav.new_context(viewport={"width": 1400, "height": 860}, locale="fr-FR")
        a = nav.new_context(viewport={"width": 1500, "height": 1000}, locale="fr-FR")
        pg = u.new_page()
        adm = a.new_page()

        # --- Portail RH : etat initial et confiance SAML
        pg.goto(SP + "/deconnexion")
        shot(pg, "01-rh-accueil")
        pg.goto(SP + "/config")
        pg.set_input_files("input[name=fichier]", str(OUT.parent / "idp-metadata.xml"))
        pg.click("button:has-text('Charger')")
        shot(pg, "02-rh-config-metadonnees", full=True)

        # --- a) Alice : une seule saisie du mot de passe
        pg.goto(SP + "/rh")
        pg.wait_for_selector("#username")
        shot(pg, "03-keycloak-login-polycorp")
        login_kc(pg, "alice")
        shot(pg, "04-rh-alice-acces-accorde", full=True)
        zoom(pg, "main", "04z-rh-alice-attributs")
        pg.goto(SP + "/messages")
        shot(pg, "05-rh-messages-saml", full=True)
        zoom(pg, "h2:has-text('AuthnRequest') + pre", "05a-saml-authnrequest")
        zoom(pg, "h2:has-text('Éléments à contrôler') + table", "05z-saml-assertion-champs")
        pg.goto(SP + "/")
        shot(pg, "06-rh-accueil-session-alice")

        flux_notes(pg, prefixe="07-notes-")
        shot(pg, "08-notes-code-recu-sans-formulaire")
        echanger(pg)
        shot(pg, "09-notes-jetons-alice", full=True)
        zoom(pg, "h2:has-text('ID token : pour le client') + pre", "09z-oidc-id-token-alice")
        zoom(pg, "h2:has-text('Access token') + pre + pre", "09a-oidc-access-token-alice")
        zoom(pg, "h2:has-text('Validation') + table", "09v-oidc-validation-id-token")
        api_action(pg, "lire")
        shot(pg, "10-notes-api-get-alice", full=True)
        api_action(pg, "ecrire")
        shot(pg, "11-notes-api-post-alice-201", full=True)
        api_action(pg, "forge")
        shot(pg, "12-notes-api-jeton-modifie-401", full=True)

        # --- Console Keycloak (admin)
        adm.goto(f"{KC}/admin/master/console/")
        adm.wait_for_selector("#username")
        adm.fill("#username", "admin")
        adm.fill("#password", "admin")
        adm.click("#kc-login")
        adm.wait_for_load_state("networkidle")
        time.sleep(3)
        console(adm, "sessions")
        shot(adm, "13-kc-sessions-alice-deux-clients")
        console(adm, f"user-federation/ldap/{ldap['id']}")
        shot(adm, "20-kc-ldap-fournisseur")
        section_ldap(adm, "Connection and authentication settings", "20a-kc-ldap-connexion-compte-service")
        section_ldap(adm, "LDAP searching and updating", "20b-kc-ldap-recherche-read-only")
        section_ldap(adm, "Kerberos integration", "20c-kc-ldap-kerberos")
        section_ldap(adm, "Cache settings", "20d-kc-ldap-cache")
        console(adm, f"user-federation/ldap/{ldap['id']}/mappers")
        shot(adm, "21-kc-ldap-mappers")
        console(adm, f"user-federation/ldap/{ldap['id']}/mappers/{gmapper['id']}")
        shot(adm, "22-kc-ldap-mapper-groupes", full=True)
        console(adm, "groups")
        shot(adm, "23-kc-groupes")
        console(adm, f"groups/{groupes['rh']['id']}")
        try:
            adm.click("text=Role mapping", timeout=5000)
            time.sleep(2)
        except Exception:
            pass
        shot(adm, "24-kc-groupe-rh-roles")
        console(adm, "clients")
        shot(adm, "25-kc-clients")
        console(adm, f"clients/{saml['id']}/clientScopes/dedicated")
        shot(adm, "26-kc-client-saml-mappers")
        console(adm, f"clients/{notes['id']}/settings")
        shot(adm, "27-kc-client-portail-notes", full=True)
        console(adm, f"clients/{notes['id']}/clientScopes")
        shot(adm, "28-kc-portail-notes-scopes")
        console(adm, f"clients/{notes['id']}/clientScopes/dedicated")
        shot(adm, "29-kc-portail-notes-mappers")
        console(adm, f"users/{users['alice']['id']}/settings")
        shot(adm, "30-kc-alice-federation-link", full=True)
        console(adm, f"users/{users['alice']['id']}/credentials")
        shot(adm, "31-kc-alice-credentials-vide")
        console(adm, f"users/{users['emma']['id']}/groups")
        shot(adm, "32-kc-emma-groupes")
        console(adm, f"users/{users['alice']['id']}/groups")
        shot(adm, "33-kc-alice-groupes")

        # --- c) Emma : authentifiee mais refusee
        pg.goto(SP + "/deconnexion")
        pg.goto(CL + "/deconnexion")
        pg.wait_for_load_state("networkidle")
        if pg.locator("#kc-logout").count():
            pg.click("#kc-logout")
            pg.wait_for_load_state("networkidle")
        pg.goto(SP + "/rh")
        login_kc(pg, "emma")
        shot(pg, "14-rh-emma-403", full=True)
        flux_notes(pg, prefixe="15-notes-emma-", capturer=False)
        echanger(pg)
        shot(pg, "15-notes-jetons-emma", full=True)
        zoom(pg, "h2:has-text('ID token : pour le client') + pre", "15z-oidc-id-token-emma")
        api_action(pg, "lire")
        shot(pg, "16-notes-api-get-emma-200", full=True)
        api_action(pg, "ecrire")
        shot(pg, "17-notes-api-post-emma-403", full=True)
        console(adm, "sessions")
        shot(adm, "18-kc-sessions-emma")

        nav.close()


if __name__ == "__main__":
    main()
