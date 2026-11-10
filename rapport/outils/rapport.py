"""Genere le rapport du mini-projet IAM (HTML puis PDF via Edge)."""
from html import escape
from pathlib import Path

from playwright.sync_api import sync_playwright

RACINE = Path(__file__).resolve().parent.parent
TP4 = RACINE.parent / "TP4"
AUTEURS = "Ghassen Cheyah &amp; Anas Abaza"


def fig(nom, legende, largeur=100):
    return (f'<figure><img src="captures/{nom}.png" style="max-width:{largeur}%">'
            f"<figcaption>{legende}</figcaption></figure>")


def code(texte, titre=None):
    t = f'<div class="code-titre">{escape(titre)}</div>' if titre else ""
    return f"{t}<pre>{escape(texte.strip())}</pre>"


LDIF = (TP4 / "ldap" / "ldif" / "01-structure.ldif").read_text(encoding="utf-8")
ACL = (TP4 / "ldap" / "02-acl.ldif").read_text(encoding="utf-8")

ARCHI = """
<svg viewBox="0 0 900 360" xmlns="http://www.w3.org/2000/svg" font-family="Segoe UI,Arial" font-size="13">
 <defs><marker id="f" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
 <path d="M0,0 L10,5 L0,10 z" fill="#555"/></marker></defs>
 <rect x="20" y="140" width="150" height="70" rx="10" fill="#fff" stroke="#888"/>
 <text x="95" y="170" text-anchor="middle" font-weight="bold">Navigateur</text>
 <text x="95" y="190" text-anchor="middle">alice / emma</text>
 <rect x="360" y="20" width="180" height="80" rx="10" fill="#FDE7DA" stroke="#F3702B" stroke-width="2"/>
 <text x="450" y="52" text-anchor="middle" font-weight="bold">Keycloak 26.8</text>
 <text x="450" y="72" text-anchor="middle">IdP SAML + serveur OIDC</text>
 <text x="450" y="90" text-anchor="middle" fill="#666">realm polycorp :8180</text>
 <rect x="700" y="20" width="180" height="80" rx="10" fill="#E8F0FB" stroke="#2F6DB5" stroke-width="2"/>
 <text x="790" y="52" text-anchor="middle" font-weight="bold">OpenLDAP 1.5</text>
 <text x="790" y="72" text-anchor="middle">annuaire dc=polycorp,dc=com</text>
 <text x="790" y="90" text-anchor="middle" fill="#666">ldap://ldap:389</text>
 <rect x="360" y="250" width="180" height="80" rx="10" fill="#EAF7EE" stroke="#1a8f3c" stroke-width="2"/>
 <text x="450" y="282" text-anchor="middle" font-weight="bold">Portail RH</text>
 <text x="450" y="302" text-anchor="middle">SP SAML 2.0 :8181</text>
 <rect x="590" y="250" width="160" height="80" rx="10" fill="#EAF7EE" stroke="#1a8f3c" stroke-width="2"/>
 <text x="670" y="282" text-anchor="middle" font-weight="bold">Portail Notes</text>
 <text x="670" y="302" text-anchor="middle">client OIDC :8182</text>
 <rect x="780" y="250" width="110" height="80" rx="10" fill="#F6F6F6" stroke="#888"/>
 <text x="835" y="282" text-anchor="middle" font-weight="bold">API Notes</text>
 <text x="835" y="302" text-anchor="middle">:8183</text>
 <line x1="540" y1="60" x2="698" y2="60" stroke="#555" marker-end="url(#f)" stroke-width="1.6"/>
 <text x="620" y="50" text-anchor="middle">bind + recherche</text>
 <text x="620" y="80" text-anchor="middle" fill="#666">svc-keycloak (lecture)</text>
 <line x1="170" y1="165" x2="358" y2="75" stroke="#555" marker-end="url(#f)" stroke-width="1.6"/>
 <text x="235" y="105" text-anchor="middle">1 seule saisie du</text>
 <text x="235" y="121" text-anchor="middle">mot de passe</text>
 <line x1="170" y1="185" x2="358" y2="280" stroke="#555" marker-end="url(#f)" stroke-width="1.6"/>
 <line x1="170" y1="195" x2="588" y2="300" stroke="#555" marker-end="url(#f)" stroke-width="1.6"/>
 <line x1="430" y1="100" x2="430" y2="248" stroke="#1a8f3c" marker-end="url(#f)" stroke-width="1.6" stroke-dasharray="5 3"/>
 <text x="425" y="180" text-anchor="end" fill="#1a8f3c">assertion SAML signée</text>
 <line x1="520" y1="100" x2="640" y2="248" stroke="#1a8f3c" marker-end="url(#f)" stroke-width="1.6" stroke-dasharray="5 3"/>
 <text x="600" y="170" fill="#1a8f3c">code + PKCE, jetons</text>
 <line x1="750" y1="290" x2="778" y2="290" stroke="#555" marker-end="url(#f)" stroke-width="1.6"/>
 <text x="790" y="240" text-anchor="middle" fill="#666">Bearer</text>
</svg>"""

DIT = """dc=polycorp,dc=com
├── ou=people                      (organizationalUnit)
│   ├── uid=alice   Alice Martin   (inetOrgPerson, userPassword {SSHA})
│   ├── uid=bob     Bob Durand     (inetOrgPerson)
│   └── uid=emma    Emma Petit     (inetOrgPerson)
├── ou=groups                      (organizationalUnit)
│   ├── cn=rh        member: alice                 (groupOfNames)
│   └── cn=employes  member: alice, bob, emma      (groupOfNames)
└── ou=services                    (organizationalUnit)
    └── cn=svc-keycloak            (organizationalRole + simpleSecurityObject)"""

SP_EXTRAIT = """GROUPE_RH = "rh"  # groupe LDAP requis pour l'Espace RH

@app.get("/rh")
def rh():
    if not session.get("nameid"):
        ...
        return redirect(url_for("connexion"))          # AuthnRequest vers Keycloak
    attrs = session.get("attributs", {})
    if GROUPE_RH not in set(attrs.get("groups", [])) | set(attrs.get("Role", [])):
        return vue(... "Accès refusé" ...), 403          # authentifié mais non autorisé
    return vue(... "accès accordé" ...)"""

API_EXTRAIT = """@app.post("/notes")
def ecrire():
    c, controles, r = controler("notes.write", "editeur")   # scope du client + rôle de l'utilisateur
    if r:
        return r                                           # 401 jeton invalide / 403 scope ou rôle"""

CSS = """
@page { size: A4; margin: 18mm 16mm 20mm 16mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; color:#1b1b1b; font-size: 10.5pt; line-height: 1.5; counter-reset: figure; }
h1 { font-size: 20pt; color:#F3702B; border-bottom: 3px solid #F3702B; padding-bottom: 4px; margin-top: 0; page-break-before: always; }
h1.premier { page-break-before: avoid; }
h2 { font-size: 13.5pt; border-left: 6px solid #F3702B; padding-left: 9px; margin-top: 22px; }
h3 { font-size: 11.5pt; color:#333; margin-bottom: 4px; }
p { text-align: justify; margin: 6px 0; }
table { border-collapse: collapse; width: 100%; margin: 8px 0 12px; font-size: 9.5pt; page-break-inside: avoid; }
th { background:#F3702B; color:#111; text-align:left; padding:5px 8px; }
td { padding:5px 8px; border-bottom:1px solid #e3e3e3; vertical-align: top; }
tr:nth-child(even) td { background:#F7F7F7; }
pre { font-family: Consolas, monospace; font-size: 8.4pt; background:#F6F6F6; border:1px solid #ddd; padding:8px 10px;
      white-space: pre-wrap; word-break: break-all; page-break-inside: avoid; margin: 4px 0 10px; }
.code-titre { font-size: 8.5pt; color:#666; margin-top: 8px; }
figure { margin: 10px 0 14px; text-align: center; page-break-inside: avoid; }
figure img { border: 1px solid #ccc; max-height: 205mm; }
figcaption { font-size: 9pt; color:#555; margin-top: 4px; font-style: italic; }
figcaption::before { counter-increment: figure; content: "Figure " counter(figure) " – "; font-weight: 600; font-style: normal; }
.cadre { border-left: 5px solid #1a8f3c; background:#EAF7EE; padding: 8px 12px; margin: 10px 0; page-break-inside: avoid; }
.alerte { border-left: 5px solid #c62828; background:#FDECEA; padding: 8px 12px; margin: 10px 0; page-break-inside: avoid; }
.info { border-left: 5px solid #2F6DB5; background:#E8F0FB; padding: 8px 12px; margin: 10px 0; page-break-inside: avoid; }
.couv { height: 255mm; display:flex; flex-direction:column; justify-content:space-between; }
.couv .bandeau { background:#F3702B; height: 14mm; }
.couv h0 { display:block; font-size: 28pt; font-weight: 700; line-height:1.2; margin-top: 40mm; }
.couv .sous { font-size: 15pt; color:#444; margin-top: 6mm; }
.couv .tech { margin-top: 10mm; font-size: 11pt; }
.couv .tech span { display:inline-block; border:1px solid #F3702B; color:#b4501b; padding:3px 10px; border-radius: 12px; margin: 0 6px 6px 0; }
.couv .auteurs { font-size: 13pt; }
.couv .auteurs b { font-size: 15pt; }
.toc a { color:#1b1b1b; text-decoration:none; }
.toc li { margin: 3px 0; }
.deux { display:flex; gap: 10px; }
.deux figure { flex: 1; }
"""


def construire():
    h = []
    h.append(f"""
<div class="couv"><div class="bandeau"></div><div>
<h0>Portail SSO adossé à un annuaire</h0>
<div class="sous">Mini-projet IAM n°1 — Polycorp : OpenLDAP, Keycloak, SAML 2.0 et OpenID Connect</div>
<div class="tech"><span>LDAP</span><span>SAML 2.0</span><span>OAuth 2.0</span><span>OpenID Connect</span><span>Keycloak 26.8</span><span>Docker Compose</span></div>
</div>
<div class="auteurs">Réalisé par<br><b>{AUTEURS}</b><br><br>Novembre 2026</div>
<div class="bandeau" style="height:4mm"></div></div>""")

    h.append("""<h1 class="premier" style="page-break-before:always">Sommaire</h1><ol class="toc">
<li><a href="#s1">Contexte et objectifs</a></li><li><a href="#s2">Architecture de la solution</a></li>
<li><a href="#s3">Conception de l'annuaire : DIT, LDIF et ACL</a></li><li><a href="#s4">Connexion de Keycloak à l'annuaire</a></li>
<li><a href="#s5">Correspondance attributs, groupes, claims et rôles</a></li><li><a href="#s6">Les deux portails et le contrôle d'accès RH</a></li>
<li><a href="#s7">Démonstrations</a><ol><li>Un seul mot de passe pour deux portails</li><li>Assertion SAML et ID token</li>
<li>Emma authentifiée mais refusée</li><li>Propagation des changements LDAP</li><li>Le mot de passe n'est que dans l'annuaire</li></ol></li>
<li><a href="#s8">Kerberos : intégration possible avec la fédération LDAP</a></li><li><a href="#s9">Sécurité, limites et recommandations</a></li>
<li><a href="#s10">Conclusion</a></li><li><a href="#s11">Annexe : procédure de reproduction</a></li></ol>""")

    h.append("""<h1 id="s1">1. Contexte et objectifs</h1>
<p>Polycorp dispose déjà d'un annuaire <b>OpenLDAP</b> qui contient ses comptes et ses groupes. L'entreprise veut ouvrir deux applications web
sans recréer ces comptes : un <b>Portail RH</b> qui parle <b>SAML 2.0</b> et un <b>Portail Notes</b> qui parle <b>OpenID Connect</b> (OIDC, construit sur OAuth 2.0).
Un utilisateur ne doit saisir son mot de passe qu'une seule fois pour accéder aux deux applications (<i>Single Sign-On</i>).</p>
<p>Nous avons placé <b>Keycloak</b> entre l'annuaire et les applications. Il joue à la fois le rôle de fournisseur d'identité (IdP) SAML
et de serveur d'autorisation OIDC. Il ne stocke pas les comptes : il les lit dans LDAP au travers d'une <i>fédération</i>, avec un compte de service
qui n'a que des droits de lecture.</p>
<h2>Travail demandé</h2>
<table><tr><th>Exigence</th><th>Réalisation</th><th>Section</th></tr>
<tr><td>Concevoir le DIT et les LDIF (unités, utilisateurs, groupes rh et employes)</td><td>3 OU, 3 utilisateurs, 2 groupes, 1 compte de service, ACL dédiées</td><td>3</td></tr>
<tr><td>Connecter Keycloak à l'annuaire avec un compte de service limité, en lecture seule</td><td>Fédération LDAP <code>READ_ONLY</code>, bind <code>cn=svc-keycloak</code>, ACL testées</td><td>4</td></tr>
<tr><td>Faire correspondre attributs et groupes LDAP aux attributs SAML, claims OIDC et rôles</td><td>Mappers LDAP, groupes → rôles, mappers SAML et OIDC</td><td>5</td></tr>
<tr><td>Reprendre les portails du TP4 et réserver l'espace RH au groupe rh</td><td>SP SAML (8181), client OIDC (8182), API (8183), contrôle <code>GROUPE_RH</code></td><td>6</td></tr></table>
<h2>Démonstrations attendues</h2>
<table><tr><th>Démonstration</th><th>Résultat obtenu</th></tr>
<tr><td>Alice ouvre les deux portails en ne saisissant son mot de passe qu'une fois</td><td>✔ Une session Keycloak, deux clients (section 7.1)</td></tr>
<tr><td>Le même utilisateur apparaît dans l'assertion SAML et dans l'ID token</td><td>✔ Comparaison champ par champ (section 7.2)</td></tr>
<tr><td>Emma est authentifiée mais refusée sur l'espace RH</td><td>✔ HTTP 403 sur /rh et sur POST /notes</td></tr>
<tr><td>Un changement de mot de passe ou de groupe dans LDAP se répercute : mesurer quand</td><td>✔ 0,26 s à 0,32 s sans cache, 51,97 s avec cache</td></tr>
<tr><td>Le mot de passe n'est stocké que dans l'annuaire</td><td>✔ Credential « Provided by ldap », hash visible uniquement par l'admin LDAP</td></tr></table>""")

    h.append(f"""<h1 id="s2">2. Architecture de la solution</h1>
<p>Toute la plateforme tourne dans <b>Docker Compose</b> (projet <code>tp4</code>). Les ports ne sont publiés que sur <code>127.0.0.1</code>.
Le navigateur joint Keycloak sur <code>localhost:8180</code> ; les conteneurs le joignent en interne sur <code>keycloak:8080</code>.</p>
<figure>{ARCHI}<figcaption>Architecture : l'annuaire reste la seule source des comptes, Keycloak fédère, les portails font confiance à Keycloak</figcaption></figure>
<table><tr><th>Service</th><th>Image / technologie</th><th>Port</th><th>Rôle</th></tr>
<tr><td>ldap</td><td>osixia/openldap 1.5.0</td><td>127.0.0.1:1389</td><td>Annuaire : comptes, groupes, mots de passe (hash SSHA)</td></tr>
<tr><td>keycloak</td><td>quay.io/keycloak/keycloak 26.8.1</td><td>127.0.0.1:8180</td><td>IdP SAML et serveur d'autorisation OIDC, realm <code>polycorp</code></td></tr>
<tr><td>sp-saml</td><td>Flask + python3-saml</td><td>127.0.0.1:8181</td><td>Portail RH, fournisseur de service SAML</td></tr>
<tr><td>client-oauth</td><td>Flask + PyJWT</td><td>127.0.0.1:8182</td><td>Portail Notes, client OIDC public (code + PKCE S256)</td></tr>
<tr><td>api-notes</td><td>Flask + PyJWT</td><td>127.0.0.1:8183</td><td>Serveur de ressources : vérifie signature, iss, aud, exp, scope et rôle</td></tr></table>
<div class="info"><b>Remarque de déploiement.</b> Les trois applications partagent la même image <code>tp4-apps:1.0</code>. À l'origine, les trois services
déclaraient chacun <code>build:</code> avec ce même tag, et BuildKit échouait avec <i>image already exists</i>. Seul <code>sp-saml</code> construit désormais l'image ;
<code>client-oauth</code> et <code>api-notes</code> la réutilisent.</div>""")

    h.append(f"""<h1 id="s3">3. Conception de l'annuaire : DIT, LDIF et ACL</h1>
<h2>3.1 Arbre de l'annuaire (DIT)</h2>
<p>Nous avons séparé les personnes, les groupes et les comptes techniques dans trois unités organisationnelles. Ce découpage permet d'écrire des ACL simples :
le compte de service voit <code>ou=people</code> et <code>ou=groups</code>, mais pas <code>ou=services</code>.</p>
{code(DIT, "Structure du DIT")}
<table><tr><th>Élément</th><th>Choix</th><th>Justification</th></tr>
<tr><td>Utilisateurs</td><td><code>inetOrgPerson</code>, RDN <code>uid</code></td><td>Classe standard : <code>uid</code>, <code>cn</code>, <code>givenName</code>, <code>sn</code>, <code>mail</code>, <code>userPassword</code></td></tr>
<tr><td>Groupes</td><td><code>groupOfNames</code>, attribut <code>member</code> (DN)</td><td>Appartenance lisible et directement exploitable par le mapper de groupes de Keycloak</td></tr>
<tr><td>Mots de passe</td><td><code>{{SSHA}}</code></td><td>Jamais en clair dans l'annuaire : SHA-1 salé</td></tr>
<tr><td>Compte de service</td><td><code>organizationalRole</code> + <code>simpleSecurityObject</code></td><td>Compte technique sans boîte mail ni identité de personne, seulement un mot de passe</td></tr></table>
<h2>3.2 Fichier LDIF chargé au démarrage</h2>
{code(LDIF, "TP4/ldap/ldif/01-structure.ldif")}
<h2>3.3 ACL : un compte de service à droits limités</h2>
<p>Les ACL sont appliquées sur la base <code>mdb</code> par <code>ldapmodify -Y EXTERNAL -H ldapi:///</code> : l'authentification se fait par le socket Unix,
en tant que root du conteneur, sans mot de passe. Les règles sont évaluées dans l'ordre et la première qui correspond s'applique.</p>
{code(ACL, "TP4/ldap/02-acl.ldif")}
<table><tr><th>Règle</th><th>Effet</th></tr>
<tr><td>{{0}}</td><td>Root local (socket <code>ldapi</code>) : <code>manage</code> sur tout, sinon on passe aux règles suivantes (<code>break</code>)</td></tr>
<tr><td>{{1}}</td><td><code>userPassword</code> : utilisable seulement pour s'authentifier (<code>anonymous auth</code>), illisible pour tous les autres</td></tr>
<tr><td>{{2}} / {{3}}</td><td><code>svc-keycloak</code> peut lire <code>ou=people</code> et <code>ou=groups</code>, et rien d'autre</td></tr>
<tr><td>{{4}}</td><td>Refus par défaut de tout le reste</td></tr></table>
{fig("40-term-acl-compte-service", "Tests des ACL : lecture autorisée sans le mot de passe, écriture refusée (50), ou=services invisible (32)")}""")

    h.append(f"""<h1 id="s4">4. Connexion de Keycloak à l'annuaire</h1>
<p>Dans le realm <code>polycorp</code>, nous avons créé un fournisseur <b>User federation → LDAP</b>. Keycloak s'y connecte avec le compte
<code>cn=svc-keycloak,ou=services,dc=polycorp,dc=com</code>, en <b>lecture seule</b>.</p>
<table><tr><th>Paramètre</th><th>Valeur</th><th>Pourquoi</th></tr>
<tr><td>Connection URL</td><td><code>ldap://ldap:389</code></td><td>Nom du service dans le réseau Docker (LDAPS en production)</td></tr>
<tr><td>Bind DN</td><td><code>cn=svc-keycloak,ou=services,…</code></td><td>Compte dédié, jamais l'administrateur de l'annuaire</td></tr>
<tr><td>Edit mode</td><td><code>READ_ONLY</code></td><td>Keycloak ne modifie jamais l'annuaire, qui reste la source de vérité</td></tr>
<tr><td>Users DN / filtre</td><td><code>ou=people,dc=polycorp,dc=com</code>, <code>inetOrgPerson</code>, scope un niveau</td><td>Seules les personnes sont des comptes utilisateurs</td></tr>
<tr><td>Username / RDN / UUID</td><td><code>uid</code> / <code>uid</code> / <code>entryUUID</code></td><td>Identifiant stable côté LDAP, même si un attribut change</td></tr>
<tr><td>Import users</td><td>On</td><td>Keycloak garde une copie locale des fiches (sans mot de passe). Le <code>sub</code> est un UUID Keycloak</td></tr>
<tr><td>Cache policy</td><td><code>NO_CACHE</code> (testé aussi en <code>MAX_LIFESPAN</code> 1 min)</td><td>Voir la mesure de propagation (section 7.4)</td></tr></table>
{fig("20a-kc-ldap-connexion-compte-service", "Connexion et authentification : URL, bind simple avec le compte de service, mode READ_ONLY")}
{fig("20b-kc-ldap-recherche-read-only", "Recherche LDAP : DN des utilisateurs, attributs uid / entryUUID, classe inetOrgPerson")}
{fig("21-kc-ldap-mappers", "Mappers de la fédération : attributs utilisateur et mapper de groupes")}
{fig("22-kc-ldap-mapper-groupes", "Mapper de groupes : groupOfNames sous ou=groups, appartenance par l'attribut member (DN), mode READ_ONLY")}
<div class="info"><b>Correction apportée.</b> Le mapper « first name » créé par défaut lisait <code>cn</code> (« Alice Martin »). Le jeton affichait donc
<code>"name": "Alice Martin Martin"</code>. Nous l'avons fait pointer vers <code>givenName</code>, puis lancé une synchronisation complète :
« 0 imported users, 3 updated users ». L'ID token contient désormais <code>given_name: Alice</code>, <code>family_name: Martin</code>.</div>""")

    h.append(f"""<h1 id="s5">5. Correspondance attributs, groupes, claims et rôles</h1>
<p>Une même information LDAP traverse trois niveaux : la fédération la convertit en attribut ou en groupe Keycloak, les groupes portent des
rôles de realm, puis chaque client publie ce dont il a besoin dans son protocole.</p>
<table><tr><th>LDAP</th><th>Keycloak</th><th>Assertion SAML (Portail RH)</th><th>Jetons OIDC (Portail Notes)</th></tr>
<tr><td><code>uid</code></td><td>username</td><td><code>NameID</code> (format username)</td><td><code>preferred_username</code></td></tr>
<tr><td><code>entryUUID</code></td><td>ID LDAP de l'utilisateur ; ID Keycloak = UUID</td><td>–</td><td><code>sub</code> (UUID Keycloak)</td></tr>
<tr><td><code>mail</code></td><td>email</td><td>attribut <code>email</code></td><td><code>email</code></td></tr>
<tr><td><code>givenName</code> / <code>sn</code></td><td>firstName / lastName</td><td>–</td><td><code>given_name</code>, <code>family_name</code>, <code>name</code></td></tr>
<tr><td><code>cn=rh</code> (member)</td><td>groupe <code>rh</code> → rôles <code>rh</code>, <code>editeur</code></td><td>attributs <code>groups</code> et <code>Role</code></td><td><code>groups</code>, <code>realm_access.roles</code></td></tr>
<tr><td><code>cn=employes</code> (member)</td><td>groupe <code>employes</code> → rôle <code>employe</code></td><td>attributs <code>groups</code> et <code>Role</code></td><td><code>groups</code>, <code>realm_access.roles</code></td></tr></table>
{fig("23-kc-groupes", "Groupes importés depuis LDAP : employes et rh", 85)}
{fig("24-kc-groupe-rh-roles", "Le groupe rh porte les rôles de realm rh et editeur", 85)}
<h2>Côté SAML</h2>
<p>Le client SAML <code>http://localhost:8181/saml/metadata</code> signe la réponse et l'assertion (RSA-SHA256), force le binding POST vers l'ACS
<code>/saml/acs</code> et utilise le format de NameID <i>username</i>. Le scope par défaut <code>role_list</code> émet l'attribut <code>Role</code>.
Nous avons ajouté un mapper <b>Group list</b> (<code>groups</code>, sans chemin complet) pour transmettre les groupes LDAP tels quels.</p>
{fig("26-kc-client-saml-mappers", "Mappers du client SAML : groups (Group list) et email (User Property)", 85)}
<h2>Côté OIDC</h2>
<p>Le client <code>portail-notes</code> est <b>public</b> (pas de secret dans une application que l'utilisateur pourrait inspecter), avec le
<i>Standard flow</i> et <b>PKCE S256 obligatoire</b>. Deux scopes optionnels décrivent ce que le client peut demander : <code>notes.read</code> et <code>notes.write</code>.
Le mapper <code>aud-api-notes</code> ajoute <code>api-notes</code> dans l'audience de l'access token ; sans lui, l'API rejette le jeton.
Le mapper <code>groups</code> publie les groupes dans l'ID token et l'access token. Enfin, le mapper <i>realm roles</i> écrit aussi les rôles dans l'ID token.</p>
{fig("27-kc-client-portail-notes", "Client portail-notes : client public, redirect URI /callback, Standard flow", 85)}
{fig("28-kc-portail-notes-scopes", "Scopes du client : notes.read et notes.write en Optional", 85)}
{fig("29-kc-portail-notes-mappers", "Mappers dédiés : audience api-notes et groups", 85)}""")

    h.append(f"""<h1 id="s6">6. Les deux portails et le contrôle d'accès RH</h1>
<h2>6.1 Portail RH : fournisseur de service SAML</h2>
<p>La confiance SAML est réciproque. Les métadonnées du SP (<code>sp-metadata.xml</code>) ont été importées dans Keycloak pour créer le client.
Les métadonnées de l'IdP (<code>/realms/polycorp/protocol/saml/descriptor</code>) ont été chargées dans le SP, qui retient l'entityID, l'URL SSO et le certificat de signature.</p>
<div class="deux">{fig("01-rh-accueil", "Accueil du SP : entityID, ACS, aucune session locale")}{fig("02-rh-config-metadonnees", "Métadonnées de l'IdP chargées : confiance établie")}</div>
<p><b>Réservation de l'espace RH au groupe rh.</b> Keycloak authentifie, mais c'est l'application qui autorise. Le SP lit les attributs
<code>groups</code> et <code>Role</code> de l'assertion validée et exige la valeur <code>rh</code>. Cette valeur provient directement du groupe LDAP <code>cn=rh</code>.</p>
{code(SP_EXTRAIT, "TP4/apps/sp_saml.py (extrait)")}
<p>Le SP vérifie aussi la signature de l'assertion (<code>wantAssertionsSigned</code>), la destination, l'audience, les dates, le <code>InResponseTo</code>
(pas de réponse non sollicitée) et refuse de rejouer une assertion déjà consommée.</p>
<h2>6.2 Portail Notes : client OIDC et API</h2>
<p>Le portail montre chaque étape du flux <i>Authorization Code</i> : paramètres envoyés, <code>code_challenge</code> PKCE, code reçu, échange au point
<code>/token</code>, puis validation de l'ID token (signature JWKS, <code>iss</code>, <code>aud</code>, <code>exp</code>, <code>nonce</code>).
L'API vérifie de son côté la signature, l'émetteur, l'audience <code>api-notes</code>, l'expiration, le scope et, pour l'écriture, le rôle <code>editeur</code>.</p>
{code(API_EXTRAIT, "TP4/apps/api_notes.py (extrait)")}
{fig("07-notes-demande-prete", "Demande d'autorisation préparée : scopes, state, nonce, code_challenge S256 ; le code_verifier reste côté client", 90)}""")

    h.append(f"""<h1 id="s7">7. Démonstrations</h1>
<h2>7.1 Un seul mot de passe pour les deux portails</h2>
<p>Alice ouvre <code>http://localhost:8181/rh</code>. N'ayant pas de session locale, le SP envoie une <code>AuthnRequest</code> à Keycloak, qui affiche
le formulaire du realm <b>polycorp</b>. C'est la seule saisie du mot de passe : Keycloak le vérifie par un bind LDAP puis renvoie une assertion signée.</p>
<div class="deux">{fig("03-keycloak-login-polycorp", "Formulaire du realm polycorp : unique saisie du mot de passe")}{fig("04z-rh-alice-attributs", "Portail RH : accès accordé à alice, attributs reçus")}</div>
<p>Elle ouvre ensuite le Portail Notes et lance la demande d'autorisation. Keycloak reconnaît la session SSO (cookie du realm) et renvoie
immédiatement un code, <b>sans afficher de formulaire</b>.</p>
{fig("08-notes-code-recu-sans-formulaire", "Portail Notes : code d'autorisation reçu directement, state vérifié, sans nouvelle saisie", 90)}
{fig("13-kc-sessions-alice-deux-clients", "Console Keycloak, realm polycorp : une seule session pour alice, deux clients (SAML et portail-notes)")}
<div class="cadre"><b>Résultat :</b> une authentification, une session IdP, deux applications et deux protocoles différents.</div>

<h2>7.2 Le même utilisateur dans l'assertion SAML et dans l'ID token</h2>
<div class="deux">{fig("05z-saml-assertion-champs", "Assertion SAML reçue par le Portail RH")}{fig("09z-oidc-id-token-alice", "ID token décodé par le Portail Notes")}</div>
<table><tr><th>Information</th><th>Assertion SAML</th><th>ID token OIDC</th><th>Analyse</th></tr>
<tr><td>Sujet</td><td><code>NameID = alice</code></td><td><code>sub = 89dff7c0-1b22-…-bc9283fad1e3</code></td><td>Même personne. SAML transmet le login ; OIDC l'UUID Keycloak, stable même si le login change (le login est dans <code>preferred_username</code>)</td></tr>
<tr><td>Émetteur</td><td><code>Issuer</code> = http://localhost:8180/realms/polycorp</td><td><code>iss</code> = même valeur</td><td>Un seul IdP pour les deux protocoles</td></tr>
<tr><td>Destinataire</td><td><code>Audience</code> = http://localhost:8181/saml/metadata</td><td><code>aud</code> = portail-notes</td><td>Chaque preuve n'est valable que pour son destinataire</td></tr>
<tr><td>Fin de validité</td><td><code>NotOnOrAfter</code> = NotBefore + 60 s</td><td><code>exp</code> = iat + 300 s</td><td>Même rôle ; date ISO 8601 contre horodatage Unix</td></tr>
<tr><td>Droits</td><td><code>Role</code> : rh, editeur, employe… ; <code>groups</code> : rh, employes</td><td><code>realm_access.roles</code> ; <code>groups</code> : rh, employes</td><td>Mêmes droits, issus des groupes LDAP</td></tr>
<tr><td>Intégrité</td><td>Signature XML de la Response et de l'Assertion</td><td>Signature JWS RS256 (clé publique JWKS)</td><td>Le destinataire vérifie sans contacter l'IdP</td></tr>
<tr><td>Anti-rejeu</td><td><code>InResponseTo</code> + ID d'assertion consommé une fois</td><td><code>nonce</code> + code à usage unique</td><td>Lien entre la demande et la réponse</td></tr></table>
{fig("09v-oidc-validation-id-token", "Validation de l'ID token par le client : signature, iss, aud, exp et nonce OK", 85)}
{fig("05a-saml-authnrequest", "AuthnRequest envoyée par le SP (HTTP-Redirect)", 90)}

<h2>7.3 Emma est authentifiée, mais refusée</h2>
<p>Après fermeture de la session locale du SP et de la session Keycloak, emma se connecte sur <code>/rh</code>. Son authentification réussit, mais
l'assertion ne contient ni le groupe ni le rôle <code>rh</code> : le portail répond <b>403</b> et affiche les attributs reçus.</p>
{fig("14-rh-emma-403", "Portail RH : emma authentifiée, groups = employes, accès refusé (403)", 90)}
<p>Sur le Portail Notes, emma obtient bien un jeton avec <code>notes.read</code> et <code>notes.write</code>. La lecture passe, mais l'écriture est refusée
car elle n'a pas le rôle <code>editeur</code>.</p>
<div class="deux">{fig("16-notes-api-get-emma-200", "GET /notes : 200 (scope notes.read)")}{fig("17-notes-api-post-emma-403", "POST /notes : 403, rôle editeur absent")}</div>
<div class="cadre"><b>À retenir :</b> le <b>scope</b> est ce que le client a le droit de demander, le <b>rôle</b> est ce que l'utilisateur a le droit de faire.
L'API vérifie les deux. Par comparaison, alice obtient 201 sur le même appel (figure suivante).</div>
{fig("11-notes-api-post-alice-201", "POST /notes avec le jeton d'alice : 201, rôle editeur présent", 80)}
<div class="info"><b>Observation pendant les essais.</b> Un premier essai avait donné 201 pour « emma » : le portail utilisait encore le jeton d'alice gardé en mémoire.
L'API ne regarde pas qui est devant le navigateur. Elle fait confiance au <b>jeton présenté</b>, valable jusqu'à <code>exp</code>.</div>

<h2>7.4 Propagation d'un changement dans LDAP : mesure</h2>
<p>Pour mesurer sans navigateur, nous avons créé temporairement un client public <code>probe</code> avec <i>Direct access grants</i>. Le script de mesure
(équivalent PowerShell de <code>scripts/mesurer.sh</code>, car <code>jq</code> et <code>bc</code> sont absents sous Windows) change le mot de passe d'alice
avec <code>ldappasswd</code> et ajoute emma au groupe <code>rh</code> avec <code>ldapmodify</code>. Il demande ensuite un jeton en boucle jusqu'à ce que le changement soit visible,
puis il remet l'annuaire dans son état initial.</p>
<table><tr><th>Changement dans LDAP</th><th>NO_CACHE</th><th>MAX_LIFESPAN = 1 min</th></tr>
<tr><td>Nouveau mot de passe accepté</td><td><b>0,32 s</b></td><td><b>0,26 s</b></td></tr>
<tr><td>Ancien mot de passe encore accepté ?</td><td>non</td><td>non</td></tr>
<tr><td>Rôle rh visible pour emma</td><td><b>0,28 s</b></td><td><b>51,97 s</b></td></tr></table>
<div class="deux">{fig("42-term-mesure-sans-cache", "Mesure avec la politique NO_CACHE")}{fig("43-term-mesure-avec-cache", "Mesure avec MAX_LIFESPAN = 1 minute")}</div>
<p><b>Interprétation.</b> Le mot de passe n'est jamais mis en cache : Keycloak le vérifie par un bind LDAP à chaque connexion, d'où une prise en compte
immédiate dans les deux cas. Les groupes, eux, font partie de la fiche utilisateur mise en cache. Avec <code>MAX_LIFESPAN</code>, Keycloak sert la copie
en cache d'emma jusqu'à son expiration : les 51,97 s correspondent au temps restant sur cette minute, emma ayant été lue environ 8 s avant la modification.</p>
<div class="alerte"><b>Conséquence sur la révocation.</b> Le même délai s'applique quand on <i>retire</i> quelqu'un d'un groupe. Il faut y ajouter la durée de vie
des preuves déjà émises : une assertion SAML (60 s ici) et surtout un access token (<code>exp</code> = 300 s), que l'API accepte jusqu'à expiration.
Avec le cache d'une minute, un droit retiré dans LDAP peut donc survivre jusqu'à environ six minutes. Le cache réduit la charge sur l'annuaire
au prix de la réactivité. Nous avons remis <code>NO_CACHE</code> après la mesure et supprimé le client <code>probe</code>.</div>
{fig("20d-kc-ldap-cache", "Politique de cache de la fédération LDAP (remise à NO_CACHE après la mesure)", 85)}

<h2>7.5 Le mot de passe n'est stocké que dans l'annuaire</h2>
<p>La fiche d'alice dans Keycloak porte le <b>Federation link : ldap</b>. Ses champs (username, email, nom) sont en lecture seule, car ils viennent de l'annuaire.
L'onglet <i>Credentials</i> n'affiche qu'une ligne « password — <b>Provided by ldap</b> ». Il s'agit d'une credential <i>virtuelle</i> : l'API d'administration la renvoie
sans identifiant, avec une date de création à <code>-1</code> et le lien de fédération. Keycloak ne détient aucun hash.</p>
<div class="deux">{fig("30-kc-alice-federation-link", "Fiche d'alice : Federation link ldap")}{fig("31-kc-alice-credentials-vide", "Credentials : mot de passe fourni par LDAP, non stocké")}</div>
{fig("41-term-hash-admin-vs-service", "Le hash {SSHA} n'est lisible que par l'administrateur LDAP ; le compte de service ne le voit pas")}""")

    h.append(f"""<h1 id="s8">8. Kerberos : intégration possible avec la fédération LDAP</h1>
<p>La fédération LDAP de Keycloak comporte une section <b>Kerberos integration</b> et crée par défaut un <i>Kerberos principal attribute mapper</i>
(attribut <code>krb5PrincipalName</code>). Kerberos permettrait un SSO « de bureau » : un poste déjà connecté au domaine présente son ticket
via SPNEGO (<code>Authorization: Negotiate</code>), et Keycloak ouvre la session sans aucun formulaire.</p>
{fig("20c-kc-ldap-kerberos", "Section Kerberos de la fédération : Allow Kerberos authentication et Use Kerberos for password authentication désactivés", 72)}
<table><tr><th>Option</th><th>Valeur</th><th>Effet si activée</th></tr>
<tr><td>Allow Kerberos authentication</td><td>Off</td><td>Authentification SPNEGO avec le ticket du poste (nécessite un KDC, un keytab HTTP/&lt;hôte&gt; et la configuration du navigateur)</td></tr>
<tr><td>Use Kerberos for password authentication</td><td>Off</td><td>Le mot de passe saisi serait vérifié auprès du KDC au lieu d'un bind LDAP</td></tr>
<tr><td>Kerberos principal attribute</td><td><code>krb5PrincipalName</code></td><td>Lien entre le principal Kerberos et l'entrée LDAP de l'utilisateur</td></tr></table>
<p><b>Pourquoi nous ne l'avons pas activé.</b> Le laboratoire ne contient ni KDC (Active Directory ou MIT Kerberos), ni domaine pour les postes.
Le sujet demandait une authentification adossée à l'annuaire : le bind LDAP suffit et reste la seule source de vérité pour le mot de passe.
Dans un SI réel avec Active Directory, l'activer serait l'étape suivante logique : les utilisateurs déjà connectés à Windows n'auraient même plus à saisir leur mot de passe une fois.</p>""")

    h.append(f"""<h1 id="s9">9. Sécurité, limites et recommandations</h1>
<h2>9.1 Mécanismes de sécurité vérifiés</h2>
{fig("12-notes-api-jeton-modifie-401", "Jeton modifié (ajout de notes.write dans la charge utile sans re-signature) : rejeté en 401, signature invalide", 85)}
<table><tr><th>Menace</th><th>Contre-mesure en place</th></tr>
<tr><td>Modification d'un jeton par le client</td><td>Signature RS256 vérifiée par l'API avec les clés JWKS (figure ci-dessus)</td></tr>
<tr><td>Interception du code d'autorisation</td><td>PKCE S256 obligatoire, code à usage unique, <code>state</code> contre le CSRF</td></tr>
<tr><td>Jeton utilisé auprès d'un autre service</td><td>Contrôle de l'audience : <code>aud = api-notes</code> pour l'API, <code>Audience</code> SAML pour le SP</td></tr>
<tr><td>Rejeu d'une assertion SAML</td><td><code>InResponseTo</code>, durée de 60 s, ID d'assertion consommé une seule fois</td></tr>
<tr><td>Fuite du compte de service</td><td>Lecture seule, sans accès à <code>userPassword</code> ni à <code>ou=services</code></td></tr>
<tr><td>Vol des mots de passe dans l'IdP</td><td>Aucun mot de passe stocké dans Keycloak, hash SSHA uniquement dans LDAP</td></tr></table>
<h2>9.2 Limites du laboratoire et recommandations pour la production</h2>
<table><tr><th>Limite actuelle</th><th>Recommandation</th></tr>
<tr><td><code>ldap://</code> en clair : le mot de passe transite en clair lors du bind</td><td><b>LDAPS</b> (636) ou <b>StartTLS</b>, avec la vérification du certificat</td></tr>
<tr><td>Keycloak en <code>start-dev</code>, HTTP, administrateur temporaire <code>admin/admin</code></td><td>Mode <code>start</code> derrière TLS, compte administrateur permanent, MFA pour la console</td></tr>
<tr><td>Hash SSHA (SHA-1 salé)</td><td>Schéma plus robuste (PBKDF2, Argon2 via module OpenLDAP) et politique de mots de passe</td></tr>
<tr><td>Métadonnées de l'IdP gardées en mémoire par le SP</td><td>Les persister (fichier ou URL de métadonnées rafraîchie), sinon un redémarrage casse la confiance</td></tr>
<tr><td>Révocation retardée (cache + durée de vie des jetons)</td><td>Access tokens courts, <i>refresh tokens</i> révocables, cache adapté au besoin, déconnexion globale</td></tr>
<tr><td>Contrôle <code>rh</code> codé dans l'application</td><td>Acceptable, mais à documenter ; on peut aussi l'imposer dans Keycloak (politique d'accès au client)</td></tr>
<tr><td>Client <code>probe</code> avec <i>password grant</i></td><td>Réservé aux mesures, supprimé après usage ; ce flux est déconseillé (OAuth 2.1)</td></tr></table>""")

    h.append(f"""<h1 id="s10">10. Conclusion</h1>
<p>Nous avons ouvert deux applications de Polycorp sur l'annuaire existant sans recréer un seul compte. OpenLDAP reste la seule source des identités,
des groupes et des mots de passe. Keycloak les fédère en lecture seule avec un compte de service limité par des ACL, puis les traduit en assertions SAML
pour le Portail RH et en jetons OIDC pour le Portail Notes.</p>
<p>Les démonstrations confirment les objectifs : une seule saisie du mot de passe pour deux protocoles ; le même utilisateur reconnu dans l'assertion et dans l'ID token ;
une autorisation fine (emma authentifiée mais refusée) fondée sur les groupes LDAP ; des changements visibles en moins d'une demi-seconde sans cache, et jusqu'à une
minute avec cache ; enfin, l'absence de tout mot de passe dans Keycloak.</p>
<p>Le projet montre aussi que l'authentification et l'autorisation sont deux étapes distinctes. Keycloak dit <i>qui</i> est l'utilisateur ; chaque application et l'API
décident <i>ce qu'il peut faire</i>, à partir des groupes, des rôles et des scopes. Il met enfin en évidence le compromis entre performance et réactivité de la révocation,
qui doit guider le choix du cache et des durées de vie des jetons en production.</p>""")

    h.append("""<h1 id="s11">11. Annexe : procédure de reproduction</h1>""" + code(r"""# 1. Démarrer la plateforme (depuis le dossier TP4)
cd TP4
docker compose up -d --build

# 2. Appliquer puis tester les ACL de l'annuaire
docker compose cp ldap/02-acl.ldif ldap:/tmp/02-acl.ldif
docker compose exec ldap ldapmodify -Y EXTERNAL -H ldapi:/// -f /tmp/02-acl.ldif
bash scripts/tester-acl.sh          # ou l'équivalent PowerShell

# 3. Keycloak (http://localhost:8180/admin, realm polycorp)
#    - User federation > LDAP : ldap://ldap:389, bind svc-keycloak, READ_ONLY, mapper de groupes
#    - Groupes rh -> rôles rh, editeur ; employes -> rôle employe
#    - Client SAML : import de sp-metadata.xml, mapper Group list "groups"
#    - Client portail-notes : public, PKCE S256, scopes notes.read / notes.write, mappers aud-api-notes et groups

# 4. Portail RH : charger les métadonnées de l'IdP
#    http://localhost:8180/realms/polycorp/protocol/saml/descriptor  ->  http://localhost:8181/config

# 5. Démonstrations
#    http://localhost:8181/rh (alice puis emma)  /  http://localhost:8182 (Demande > Jetons > API)
#    Mesure : client public "probe" (Direct access grants), script de mesure, puis suppression

# 6. Le hash n'est visible que par l'administrateur LDAP
docker compose exec ldap ldapsearch -x -D cn=admin,dc=polycorp,dc=com -w admin -b ou=people,dc=polycorp,dc=com uid=alice userPassword""", "Commandes principales") + """
<h2>Comptes de test</h2><table><tr><th>Compte</th><th>Groupes LDAP</th><th>Accès attendu</th></tr>
<tr><td>alice</td><td>rh, employes</td><td>Espace RH autorisé ; lecture et écriture des notes</td></tr>
<tr><td>bob</td><td>employes</td><td>Espace RH refusé ; lecture des notes</td></tr>
<tr><td>emma</td><td>employes</td><td>Espace RH refusé ; lecture des notes, écriture refusée</td></tr></table>
<p style="color:#666;font-size:9pt">Les captures ont été produites automatiquement (Playwright + Microsoft Edge) sur la plateforme en fonctionnement le 10 novembre 2026 ;
les sorties de terminal sont celles des exécutions réelles.</p>""")

    return f"<!doctype html><html lang=fr><meta charset=utf-8><title>Rapport - Portail SSO adossé à un annuaire</title><style>{CSS}</style><body>{''.join(h)}</body></html>"


def main():
    html = RACINE / "rapport.html"
    html.write_text(construire(), encoding="utf-8")
    pdf = RACINE / "Rapport_SSO_LDAP_Cheyah_Abaza.pdf"
    with sync_playwright() as p:
        nav = p.chromium.launch(channel="msedge", headless=True)
        pg = nav.new_page()
        pg.goto(html.as_uri())
        pg.wait_for_load_state("networkidle")
        pg.pdf(path=str(pdf), format="A4", print_background=True, display_header_footer=True,
               margin={"top": "16mm", "bottom": "18mm", "left": "15mm", "right": "15mm"},
               header_template="<div style='font-size:7.5pt;color:#999;width:100%;text-align:right;padding-right:15mm'>Portail SSO adossé à un annuaire — Cheyah &amp; Abaza</div>",
               footer_template="<div style='font-size:8pt;color:#777;width:100%;text-align:center'><span class=pageNumber></span> / <span class=totalPages></span></div>")
        nav.close()
    print("PDF :", pdf)


if __name__ == "__main__":
    main()
