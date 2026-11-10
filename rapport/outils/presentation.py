"""Genere la presentation PPTX du mini-projet IAM."""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

RACINE = Path(__file__).resolve().parent.parent
CAP = RACINE / "captures"
ORANGE = RGBColor(0xF3, 0x70, 0x2B)
NOIR = RGBColor(0x1B, 0x1B, 0x1B)
GRIS = RGBColor(0x66, 0x66, 0x66)
CLAIR = RGBColor(0xF6, 0xF6, 0xF6)
VERT = RGBColor(0x1A, 0x8F, 0x3C)
ROUGE = RGBColor(0xC6, 0x28, 0x28)
BLEU = RGBColor(0x2F, 0x6D, 0xB5)
BLANC = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
VIDE = prs.slide_layouts[6]
W, H = prs.slide_width, prs.slide_height
numero = [0]


def texte(slide, x, y, w, h, lignes, taille=18, couleur=NOIR, gras=False, police="Segoe UI", align=PP_ALIGN.LEFT, puces=False):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    for i, ligne in enumerate(lignes if isinstance(lignes, list) else [lignes]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        segments = ligne if isinstance(ligne, list) else [(ligne, gras)]
        if puces:
            r = p.add_run()
            r.text = "▪  "
            r.font.color.rgb = ORANGE
            r.font.size = Pt(taille)
        for seg, g in segments:
            r = p.add_run()
            r.text = seg
            r.font.size = Pt(taille)
            r.font.bold = g
            r.font.color.rgb = couleur
            r.font.name = police
        p.space_after = Pt(taille * 0.45)
    return tb


def diapo(titre, sous_titre=None):
    s = prs.slides.add_slide(VIDE)
    numero[0] += 1
    bande = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.18), H)
    bande.fill.solid(); bande.fill.fore_color.rgb = ORANGE; bande.line.fill.background()
    texte(s, Inches(0.55), Inches(0.3), Inches(12), Inches(0.8), titre, 30, NOIR, True)
    trait = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.58), Inches(1.08), Inches(1.4), Inches(0.06))
    trait.fill.solid(); trait.fill.fore_color.rgb = ORANGE; trait.line.fill.background()
    if sous_titre:
        texte(s, Inches(0.55), Inches(1.18), Inches(12.2), Inches(0.5), sous_titre, 15, GRIS)
    texte(s, Inches(0.55), Inches(7.0), Inches(9), Inches(0.35), "Portail SSO adossé à un annuaire — Ghassen Cheyah & Anas Abaza", 10, GRIS)
    texte(s, Inches(12.2), Inches(7.0), Inches(0.8), Inches(0.35), str(numero[0]), 10, GRIS, align=PP_ALIGN.RIGHT)
    return s


def image(slide, nom, x, y, w_max, h_max, legende=None, cadre=True):
    chemin = CAP / f"{nom}.png"
    iw, ih = Image.open(chemin).size
    h_util = h_max - (Inches(0.35) if legende else 0)
    echelle = min(w_max / iw, h_util / ih)
    w, h = int(iw * echelle), int(ih * echelle)
    px = x + (w_max - w) // 2
    pic = slide.shapes.add_picture(str(chemin), px, y, w, h)
    if cadre:
        pic.line.color.rgb = RGBColor(0xCC, 0xCC, 0xCC); pic.line.width = Pt(0.75)
    if legende:
        texte(slide, x, y + h + Inches(0.03), w_max, Inches(0.35), legende, 11, GRIS, align=PP_ALIGN.CENTER)
    return pic


def boite(slide, x, y, w, h, titre, sous, fond, bord):
    b = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    b.fill.solid(); b.fill.fore_color.rgb = fond
    b.line.color.rgb = bord; b.line.width = Pt(2)
    tf = b.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for i, (t, taille, g, c) in enumerate([(titre, 16, True, NOIR)] + [(l, 11.5, False, GRIS) for l in sous]):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(taille); r.font.bold = g; r.font.color.rgb = c; r.font.name = "Segoe UI"
    return b


def fleche(slide, x1, y1, x2, y2, couleur=GRIS, pointe=True):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    c.line.color.rgb = couleur; c.line.width = Pt(2)
    if pointe:
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"}))
    return c


def tableau(slide, x, y, w, lignes, largeurs, taille=12, h_ligne=0.42):
    t = slide.shapes.add_table(len(lignes), len(lignes[0]), x, y, w, Inches(h_ligne * len(lignes))).table
    for j, l in enumerate(largeurs):
        t.columns[j].width = Inches(l)
    for i, ligne in enumerate(lignes):
        for j, val in enumerate(ligne):
            cel = t.cell(i, j)
            cel.text = val
            cel.fill.solid()
            cel.fill.fore_color.rgb = ORANGE if i == 0 else (CLAIR if i % 2 == 0 else BLANC)
            for p in cel.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(taille); r.font.name = "Segoe UI"; r.font.color.rgb = NOIR; r.font.bold = (i == 0)
            cel.margin_left = cel.margin_right = Inches(0.08)
    return t


def encadre(slide, x, y, w, h, lignes, couleur=VERT, taille=14):
    b = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    b.fill.solid(); b.fill.fore_color.rgb = {VERT: RGBColor(0xEA, 0xF7, 0xEE), ROUGE: RGBColor(0xFD, 0xEC, 0xEA), BLEU: RGBColor(0xE8, 0xF0, 0xFB)}[couleur]
    b.line.fill.background()
    liseré = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(0.08), h)
    liseré.fill.solid(); liseré.fill.fore_color.rgb = couleur; liseré.line.fill.background()
    texte(slide, x + Inches(0.2), y + Inches(0.08), w - Inches(0.3), h - Inches(0.1), lignes, taille)


# 1. Titre
s = prs.slides.add_slide(VIDE); numero[0] += 1
fond = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, Inches(0.35)); fond.fill.solid(); fond.fill.fore_color.rgb = ORANGE; fond.line.fill.background()
texte(s, Inches(0.9), Inches(1.7), Inches(11.5), Inches(1.2), "Portail SSO adossé à un annuaire", 44, NOIR, True)
texte(s, Inches(0.9), Inches(2.85), Inches(11.5), Inches(0.8), "Mini-projet IAM n°1 — Polycorp : OpenLDAP, Keycloak, SAML 2.0 et OpenID Connect", 22, GRIS)
x = Inches(0.9)
for tag in ["LDAP", "SAML 2.0", "OAuth 2.0", "OIDC", "Keycloak 26.8", "Docker"]:
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(3.9), Inches(1.55), Inches(0.45))
    b.fill.solid(); b.fill.fore_color.rgb = RGBColor(0xFD, 0xE7, 0xDA); b.line.color.rgb = ORANGE
    b.text_frame.text = tag
    r = b.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(13); r.font.color.rgb = RGBColor(0xB4, 0x50, 0x1B); r.font.name = "Segoe UI"
    b.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    x += Inches(1.7)
texte(s, Inches(0.9), Inches(5.4), Inches(8), Inches(1.2), [[("Ghassen Cheyah", True)], [("Anas Abaza", True)], [("Novembre 2026", False)]], 20)
bas = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, H - Inches(0.12), W, Inches(0.12)); bas.fill.solid(); bas.fill.fore_color.rgb = ORANGE; bas.line.fill.background()

# 2. Contexte
s = diapo("Contexte et objectifs", "Ouvrir deux applications web sur l'annuaire existant, sans recréer les comptes")
texte(s, Inches(0.6), Inches(1.9), Inches(6.2), Inches(4.8), [
    [("Polycorp ", True), ("possède déjà un annuaire OpenLDAP (comptes, groupes, mots de passe).", False)],
    [("Portail RH ", True), ("en SAML 2.0, réservé au groupe rh.", False)],
    [("Portail Notes ", True), ("en OpenID Connect, avec une API protégée.", False)],
    [("Une seule saisie ", True), ("du mot de passe pour les deux portails (SSO).", False)],
    [("Keycloak ", True), ("fédère l'annuaire en lecture seule et sert d'IdP pour les deux protocoles.", False)]], 18, puces=True)
tableau(s, Inches(7.1), Inches(1.95), Inches(5.7), [
    ["Démonstration attendue", "Résultat"],
    ["Un seul mot de passe pour 2 portails", "✔ 1 session, 2 clients"],
    ["Même utilisateur en SAML et OIDC", "✔ comparé champ par champ"],
    ["Emma authentifiée mais refusée", "✔ 403 sur /rh et POST /notes"],
    ["Propagation LDAP mesurée", "✔ 0,3 s / 52 s avec cache"],
    ["Mot de passe seulement dans LDAP", "✔ « Provided by ldap »"]], [3.2, 2.5], 13, 0.55)

# 3. Architecture
s = diapo("Architecture de la solution", "Docker Compose, ports publiés sur 127.0.0.1 uniquement")
nav = boite(s, Inches(0.6), Inches(3.4), Inches(2.2), Inches(1.1), "Navigateur", ["alice / emma"], BLANC, GRIS)
kc = boite(s, Inches(5.2), Inches(1.75), Inches(2.9), Inches(1.25), "Keycloak 26.8", ["IdP SAML + serveur OIDC", "realm polycorp :8180"], RGBColor(0xFD, 0xE7, 0xDA), ORANGE)
ld = boite(s, Inches(9.9), Inches(1.75), Inches(2.9), Inches(1.25), "OpenLDAP", ["dc=polycorp,dc=com", "ldap://ldap:389"], RGBColor(0xE8, 0xF0, 0xFB), BLEU)
rh = boite(s, Inches(4.4), Inches(5.2), Inches(2.5), Inches(1.15), "Portail RH", ["SP SAML 2.0 :8181"], RGBColor(0xEA, 0xF7, 0xEE), VERT)
nt = boite(s, Inches(7.4), Inches(5.2), Inches(2.5), Inches(1.15), "Portail Notes", ["client OIDC :8182"], RGBColor(0xEA, 0xF7, 0xEE), VERT)
ap = boite(s, Inches(10.4), Inches(5.2), Inches(2.4), Inches(1.15), "API Notes", ["serveur de ressources :8183"], CLAIR, GRIS)
fleche(s, Inches(8.1), Inches(2.37), Inches(9.9), Inches(2.37))
texte(s, Inches(8.1), Inches(1.75), Inches(1.8), Inches(0.6), "bind + recherche", 11, GRIS, align=PP_ALIGN.CENTER)
texte(s, Inches(8.1), Inches(2.45), Inches(1.8), Inches(0.6), "svc-keycloak (lecture)", 11, GRIS, align=PP_ALIGN.CENTER)
fleche(s, Inches(2.8), Inches(3.6), Inches(5.2), Inches(2.6))
texte(s, Inches(2.4), Inches(2.45), Inches(2.6), Inches(0.6), "1 seule saisie du mot de passe", 12, NOIR, True, align=PP_ALIGN.CENTER)
fleche(s, Inches(2.8), Inches(4.2), Inches(4.4), Inches(5.5))
fleche(s, Inches(1.7), Inches(4.5), Inches(1.7), Inches(6.65), pointe=False)
fleche(s, Inches(1.7), Inches(6.65), Inches(8.65), Inches(6.65), pointe=False)
fleche(s, Inches(8.65), Inches(6.65), Inches(8.65), Inches(6.35))
fleche(s, Inches(6.0), Inches(3.0), Inches(5.65), Inches(5.2), VERT)
texte(s, Inches(3.55), Inches(3.75), Inches(2.4), Inches(0.5), "assertion SAML signée", 12, VERT, align=PP_ALIGN.RIGHT)
fleche(s, Inches(7.3), Inches(3.0), Inches(8.65), Inches(5.2), VERT)
texte(s, Inches(8.1), Inches(3.75), Inches(2.6), Inches(0.5), "code + PKCE → jetons", 12, VERT)
fleche(s, Inches(9.9), Inches(5.78), Inches(10.4), Inches(5.78))

# 4. DIT
s = diapo("Conception de l'annuaire : le DIT", "Trois unités pour séparer personnes, groupes et comptes techniques")
dit = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.85), Inches(7.3), Inches(4.7))
dit.fill.solid(); dit.fill.fore_color.rgb = CLAIR; dit.line.color.rgb = RGBColor(0xDD, 0xDD, 0xDD)
texte(s, Inches(0.75), Inches(1.95), Inches(7.1), Inches(4.6), [
    "dc=polycorp,dc=com",
    "├── ou=people",
    "│   ├── uid=alice   Alice Martin",
    "│   ├── uid=bob     Bob Durand",
    "│   └── uid=emma    Emma Petit",
    "├── ou=groups",
    "│   ├── cn=rh        member: alice",
    "│   └── cn=employes  member: alice, bob, emma",
    "└── ou=services",
    "    └── cn=svc-keycloak   (compte de service)"], 15, NOIR, police="Consolas")
texte(s, Inches(8.3), Inches(1.9), Inches(4.6), Inches(4.8), [
    [("Utilisateurs : ", True), ("inetOrgPerson, RDN uid, mot de passe {SSHA}", False)],
    [("Groupes : ", True), ("groupOfNames, appartenance par l'attribut member (DN)", False)],
    [("Compte de service : ", True), ("organizationalRole + simpleSecurityObject, sans identité de personne", False)],
    [("Avantage : ", True), ("des ACL simples par branche de l'arbre", False)]], 16, puces=True)

# 5. ACL
s = diapo("Un compte de service à droits limités", "ACL OpenLDAP appliquées par ldapmodify -Y EXTERNAL -H ldapi:///")
tableau(s, Inches(0.6), Inches(1.9), Inches(5.6), [
    ["Règle", "Effet"],
    ["{0}", "root local (socket) : manage, sinon break"],
    ["{1}", "userPassword : auth seulement, illisible"],
    ["{2}", "svc-keycloak lit ou=people"],
    ["{3}", "svc-keycloak lit ou=groups"],
    ["{4}", "tout le reste : refusé"]], [0.9, 4.7], 14, 0.55)
image(s, "40-term-acl-compte-service", Inches(6.5), Inches(1.85), Inches(6.4), Inches(4.9), "Lecture sans le hash, écriture refusée (50), ou=services invisible (32)", cadre=False)

# 6. Federation
s = diapo("Fédération Keycloak ↔ LDAP", "User federation du realm polycorp, en lecture seule")
image(s, "20a-kc-ldap-connexion-compte-service", Inches(0.5), Inches(1.75), Inches(7.6), Inches(5.15))
texte(s, Inches(8.4), Inches(1.85), Inches(4.6), Inches(5), [
    [("URL : ", True), ("ldap://ldap:389", False)],
    [("Bind DN : ", True), ("cn=svc-keycloak,ou=services", False)],
    [("Edit mode : ", True), ("READ_ONLY", False)],
    [("Users DN : ", True), ("ou=people, inetOrgPerson", False)],
    [("UUID : ", True), ("entryUUID ; Import users : On", False)],
    [("Mapper de groupes : ", True), ("ou=groups, groupOfNames, member", False)],
    [("Cache : ", True), ("NO_CACHE (testé à 1 min)", False)],
    [("Correction : ", True), ("first name lu dans givenName au lieu de cn", False)]], 15, puces=True)

# 7. Correspondances
s = diapo("Correspondance LDAP → Keycloak → SAML / OIDC", "Une même donnée de l'annuaire, publiée dans chaque protocole")
tableau(s, Inches(0.6), Inches(1.9), Inches(12.2), [
    ["LDAP", "Keycloak", "Assertion SAML (Portail RH)", "Jetons OIDC (Portail Notes)"],
    ["uid", "username", "NameID (format username)", "preferred_username"],
    ["entryUUID", "lien LDAP ; ID Keycloak = UUID", "–", "sub (UUID)"],
    ["mail", "email", "attribut email", "email"],
    ["givenName / sn", "firstName / lastName", "–", "given_name, family_name, name"],
    ["cn=rh (member)", "groupe rh → rôles rh, editeur", "groups, Role", "groups, realm_access.roles"],
    ["cn=employes (member)", "groupe employes → rôle employe", "groups, Role", "groups, realm_access.roles"]], [2.4, 3.4, 3.1, 3.3], 14, 0.6)
encadre(s, Inches(0.6), Inches(6.2), Inches(12.2), Inches(0.62), "Mappers ajoutés : Group list « groups » (SAML) ; aud-api-notes et groups (portail-notes) ; realm roles aussi dans l'ID token.", BLEU, 14)

# 8. Demo a
s = diapo("Démo 1 — Un seul mot de passe pour deux portails", "Alice se connecte sur le Portail RH, puis ouvre le Portail Notes")
image(s, "03-keycloak-login-polycorp", Inches(0.5), Inches(1.75), Inches(4.1), Inches(2.6), "① Unique saisie : formulaire du realm polycorp")
image(s, "08-notes-code-recu-sans-formulaire", Inches(0.5), Inches(4.45), Inches(4.1), Inches(2.5), "② Portail Notes : code reçu, sans formulaire")
image(s, "13-kc-sessions-alice-deux-clients", Inches(4.9), Inches(1.75), Inches(8.0), Inches(4.4), "③ Une seule session alice, deux clients : SAML et portail-notes")
encadre(s, Inches(4.9), Inches(6.25), Inches(8.0), Inches(0.62), "1 authentification → 1 session IdP → 2 applications, 2 protocoles", VERT, 15)

# 9. Demo b captures
s = diapo("Démo 2 — Le même utilisateur en SAML et en OIDC", "Assertion SAML (Portail RH) et ID token décodé (Portail Notes)")
image(s, "05z-saml-assertion-champs", Inches(0.5), Inches(1.8), Inches(6.2), Inches(5.0), "Assertion SAML : NameID, Issuer, Audience, NotOnOrAfter, signatures")
image(s, "09z-oidc-id-token-alice", Inches(6.9), Inches(1.8), Inches(6.0), Inches(5.0), "ID token : sub, iss, aud, exp, groups, realm_access")

# 10. Demo b tableau
s = diapo("Démo 2 — Comparaison champ par champ")
tableau(s, Inches(0.6), Inches(1.5), Inches(12.2), [
    ["Information", "Assertion SAML", "ID token OIDC", "Analyse"],
    ["Sujet", "NameID = alice", "sub = 89dff7c0-…-bc9283fad1e3", "Login d'un côté, UUID stable de l'autre"],
    ["Émetteur", "Issuer = …/realms/polycorp", "iss = même valeur", "Un seul IdP pour deux protocoles"],
    ["Destinataire", "Audience = …8181/saml/metadata", "aud = portail-notes", "Chaque preuve vise son destinataire"],
    ["Validité", "NotOnOrAfter = NotBefore + 60 s", "exp = iat + 300 s", "Date ISO contre horodatage Unix"],
    ["Droits", "Role, groups = rh, employes", "realm_access.roles, groups", "Mêmes droits, issus de LDAP"],
    ["Intégrité", "Signature XML (RSA-SHA256)", "Signature JWS RS256 (JWKS)", "Vérifiable sans appeler l'IdP"],
    ["Anti-rejeu", "InResponseTo + ID consommé une fois", "nonce + code à usage unique", "Lie la réponse à la demande"]], [1.8, 3.6, 3.4, 3.4], 14, 0.62)

# 11. Demo c
s = diapo("Démo 3 — Emma authentifiée, mais refusée", "Authentification ≠ autorisation")
image(s, "14-rh-emma-403", Inches(0.5), Inches(1.75), Inches(6.2), Inches(3.9), "Portail RH : groups = employes → 403")
image(s, "17-notes-api-post-emma-403", Inches(6.9), Inches(1.75), Inches(6.0), Inches(3.9), "API : scope notes.write OK, rôle editeur KO → 403")
encadre(s, Inches(0.5), Inches(5.95), Inches(12.4), Inches(0.9), [
    [("Le scope ", True), ("est ce que le client peut demander ; ", False), ("le rôle ", True), ("est ce que l'utilisateur peut faire. Alice obtient 201 sur le même appel. Le contrôle rh est fait par le portail (GROUPE_RH), à partir du groupe LDAP.", False)]], VERT, 14)

# 12. Demo d
s = diapo("Démo 4 — Propagation d'un changement LDAP", "Client probe (password grant, labo seulement) et script de mesure")
donnees = CategoryChartData()
donnees.categories = ["Mot de passe", "Ajout au groupe rh"]
donnees.add_series("NO_CACHE", (0.32, 0.28))
donnees.add_series("MAX_LIFESPAN 1 min", (0.26, 51.97))
g = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.5), Inches(1.75), Inches(6.3), Inches(4.3), donnees).chart
g.has_legend = True; g.legend.position = XL_LEGEND_POSITION.BOTTOM; g.legend.include_in_layout = False
g.plots[0].has_data_labels = True
g.plots[0].data_labels.number_format = '0.00" s"'; g.plots[0].data_labels.number_format_is_linked = False
g.plots[0].data_labels.font.size = Pt(13)
g.series[0].format.fill.solid(); g.series[0].format.fill.fore_color.rgb = BLEU
g.series[1].format.fill.solid(); g.series[1].format.fill.fore_color.rgb = ORANGE
g.value_axis.has_major_gridlines = False
g.value_axis.tick_labels.font.size = Pt(11); g.category_axis.tick_labels.font.size = Pt(13)
texte(s, Inches(7.1), Inches(1.8), Inches(5.8), Inches(3.2), [
    [("Mot de passe : ", True), ("jamais mis en cache, vérifié par bind LDAP à chaque connexion → immédiat.", False)],
    [("Groupes : ", True), ("dans la fiche utilisateur mise en cache → jusqu'à la durée du cache (51,97 s mesurées).", False)],
    [("Ancien mot de passe : ", True), ("refusé dans les deux cas.", False)]], 16, puces=True)
encadre(s, Inches(7.1), Inches(4.75), Inches(5.8), Inches(1.3), [
    [("Révocation retardée : ", True), ("cache (60 s) + durée de vie du jeton (exp = 300 s) → un droit retiré peut survivre ~6 min.", False)]], ROUGE, 14)
texte(s, Inches(0.5), Inches(6.3), Inches(12.4), Inches(0.5), "Après la mesure : cache remis à NO_CACHE, client probe supprimé, annuaire restauré (rh = alice).", 13, GRIS)

# 13. Demo e
s = diapo("Démo 5 — Le mot de passe n'est que dans l'annuaire")
image(s, "31-kc-alice-credentials-vide", Inches(0.5), Inches(1.4), Inches(6.2), Inches(3.9), "Keycloak : password « Provided by ldap », rien de stocké")
image(s, "41-term-hash-admin-vs-service", Inches(6.9), Inches(1.4), Inches(6.0), Inches(3.9), "LDAP : hash {SSHA} visible par l'admin seulement", cadre=False)
encadre(s, Inches(0.5), Inches(5.6), Inches(12.4), Inches(1.2), [
    [("API d'administration : ", True), ('[{"type":"password","createdDate":-1,"federationLink":"…"}]', False)],
    [("Credential virtuelle : pas d'identifiant, pas de secret. Keycloak vérifie par un bind LDAP ; le compte de service ne lit jamais userPassword.", False)]], BLEU, 14)

# 14. Kerberos
s = diapo("Kerberos et la fédération LDAP", "Intégration disponible dans Keycloak, désactivée dans ce laboratoire")
image(s, "20c-kc-ldap-kerberos", Inches(0.5), Inches(1.75), Inches(6.6), Inches(5.1))
texte(s, Inches(7.4), Inches(1.85), Inches(5.5), Inches(5), [
    [("SPNEGO : ", True), ("le poste déjà connecté au domaine présente son ticket Kerberos, sans aucun formulaire.", False)],
    [("Allow Kerberos authentication : ", True), ("Off", False)],
    [("Use Kerberos for password authentication : ", True), ("Off (bind LDAP utilisé)", False)],
    [("Kerberos principal attribute : ", True), ("krb5PrincipalName", False)],
    [("Pourquoi Off : ", True), ("pas de KDC ni de domaine dans le labo ; le sujet demande l'annuaire comme source de vérité.", False)],
    [("Perspective : ", True), ("avec Active Directory, SSO dès l'ouverture de session Windows.", False)]], 15, puces=True)

# 15. Securite
s = diapo("Mécanismes de sécurité vérifiés")
image(s, "12-notes-api-jeton-modifie-401", Inches(0.5), Inches(1.4), Inches(5.9), Inches(5.4), "Jeton modifié (ajout de notes.write) : 401, signature invalide")
tableau(s, Inches(6.7), Inches(1.5), Inches(6.2), [
    ["Menace", "Contre-mesure"],
    ["Jeton modifié", "Signature RS256 vérifiée (JWKS)"],
    ["Code intercepté", "PKCE S256, code unique, state"],
    ["Jeton pour un autre service", "aud = api-notes / Audience SAML"],
    ["Rejeu d'assertion", "InResponseTo, 60 s, ID unique"],
    ["Fuite du compte de service", "Lecture seule, sans userPassword"],
    ["Vol de mots de passe dans l'IdP", "Aucun stocké dans Keycloak"]], [2.7, 3.5], 13, 0.62)

# 16. Limites
s = diapo("Limites du laboratoire et recommandations")
tableau(s, Inches(0.6), Inches(1.5), Inches(12.2), [
    ["Limite actuelle", "Recommandation pour la production"],
    ["ldap:// en clair : le mot de passe passe en clair au bind", "LDAPS ou StartTLS avec vérification du certificat"],
    ["Keycloak start-dev, HTTP, admin temporaire admin/admin", "Mode start derrière TLS, admin permanent, MFA"],
    ["Hash SSHA (SHA-1 salé)", "Schéma plus robuste + politique de mots de passe"],
    ["Métadonnées IdP en mémoire dans le SP", "Les persister ou les rafraîchir depuis une URL"],
    ["Révocation retardée (cache + jetons)", "Jetons courts, refresh tokens révocables, cache adapté"],
    ["Client probe en password grant", "Réservé aux mesures, supprimé (déconseillé par OAuth 2.1)"]], [5.8, 6.4], 14, 0.66)

# 17. Conclusion
s = diapo("Conclusion")
texte(s, Inches(0.6), Inches(1.6), Inches(12.2), Inches(4.2), [
    [("Aucun compte recréé : ", True), ("OpenLDAP reste la seule source des identités, des groupes et des mots de passe.", False)],
    [("Keycloak fédère en lecture seule ", True), ("avec un compte de service limité par des ACL.", False)],
    [("Deux protocoles, un seul SSO : ", True), ("assertion SAML pour le Portail RH, jetons OIDC pour le Portail Notes.", False)],
    [("Authentification ≠ autorisation : ", True), ("Keycloak dit qui est l'utilisateur ; portails et API décident ce qu'il peut faire.", False)],
    [("Compromis mesuré : ", True), ("le cache soulage l'annuaire mais retarde la révocation des droits.", False)]], 19, puces=True)
encadre(s, Inches(0.6), Inches(5.6), Inches(12.2), Inches(0.9), "Perspectives : LDAPS, Kerberos/SPNEGO avec Active Directory, politique d'accès aux clients dans Keycloak, MFA.", BLEU, 16)

# 18. Questions
s = prs.slides.add_slide(VIDE); numero[0] += 1
f = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H); f.fill.solid(); f.fill.fore_color.rgb = ORANGE; f.line.fill.background()
texte(s, Inches(0.9), Inches(2.6), Inches(11.5), Inches(1.2), "Merci de votre attention", 44, BLANC, True, align=PP_ALIGN.CENTER)
texte(s, Inches(0.9), Inches(3.8), Inches(11.5), Inches(0.8), "Questions ?", 28, BLANC, align=PP_ALIGN.CENTER)
texte(s, Inches(0.9), Inches(5.6), Inches(11.5), Inches(0.6), "Ghassen Cheyah — Anas Abaza", 18, BLANC, align=PP_ALIGN.CENTER)

sortie = RACINE / "Presentation_SSO_LDAP_Cheyah_Abaza.pptx"
prs.save(sortie)
print("PPTX :", sortie, "-", len(prs.slides), "diapositives")
