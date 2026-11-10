"""Client OAuth 2.0 / OIDC pedagogique : chaque etape du flux est visible."""
import base64
import hashlib
import json
import os
import secrets
import time
from html import escape
from urllib.parse import urlencode

import jwt
import requests
from flask import Flask, redirect, request

from commun import decoder_jwt, page, tableau

KC_PUBLIC = os.environ["KC_PUBLIC"]
KC_INTERNE = os.environ["KC_INTERNE"]
BASE = os.environ["CLIENT_BASE"]
API = os.environ["API_INTERNE"]
CLIENT_ID = "portail-notes"
REDIRECT = BASE + "/callback"
TOKEN_URL = KC_INTERNE + "/protocol/openid-connect/token"
SCOPES = ["openid", "profile", "email", "notes.read", "notes.write"]
LIENS = [("1. Demande", "/"), ("2. Jetons", "/jetons"), ("3. API", "/api"), ("Client Credentials", "/service")]
ETAT = {}
app = Flask(__name__)


def vue(corps):
    return page("Portail Notes - client OAuth 2.0 / OIDC", LIENS, corps)


def json_html(obj):
    return "<pre>" + escape(json.dumps(obj, indent=2, ensure_ascii=False)) + "</pre>"


@app.get("/")
def accueil():
    coches = "".join(f'<label><input type=checkbox name=scope value="{s}" {"checked" if s in ("openid", "notes.read") else ""}> {s}</label>' for s in SCOPES)
    return vue(f"""<h2>Étape 1 : préparer la demande d'autorisation</h2>
<form action=/preparer method=post><p>Scopes demandés :<br>{coches}</p>
<p><label><input type=checkbox name=pkce checked> Utiliser PKCE (S256)</label></p>
<p>redirect_uri : <input name=redirect_uri size=50 value="{REDIRECT}"></p>
<button>Préparer la demande</button></form>
<p><a class="bouton gris" href=/deconnexion>Fermer la session Keycloak (changer de compte)</a></p>""")


@app.post("/preparer")
def preparer():
    ETAT.clear()
    scopes = request.form.getlist("scope")
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state, nonce = secrets.token_urlsafe(12), secrets.token_urlsafe(12)
    redirect_uri = request.form.get("redirect_uri") or REDIRECT
    params = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": redirect_uri,
              "scope": " ".join(scopes), "state": state}
    if "openid" in scopes:
        params["nonce"] = nonce
    if request.form.get("pkce"):
        params.update(code_challenge=challenge, code_challenge_method="S256")
    ETAT.update(verifier=verifier, state=state, nonce=nonce, redirect_uri=redirect_uri, pkce=bool(request.form.get("pkce")))
    url = KC_PUBLIC + "/protocol/openid-connect/auth?" + urlencode(params)
    return vue(f"""<h2>Étape 1 : demande prête</h2>
{tableau(list(params.items()), ("Paramètre", "Valeur envoyée dans l'URL"))}
<div class=info><b>code_verifier</b> (secret, gardé par le client, jamais dans l'URL) :<br><code>{verifier}</code><br>
code_challenge = BASE64URL(SHA-256(code_verifier))</div>
<a class=bouton href="{escape(url)}">Envoyer le navigateur vers Keycloak</a>""")


@app.get("/callback")
def callback():
    if "error" in request.args:
        return vue(f"<div class=ko><b>Keycloak a renvoyé une erreur :</b> {escape(request.args.get('error', ''))} - {escape(request.args.get('error_description', ''))}</div>")
    code = request.args.get("code", "")
    if request.args.get("state") != ETAT.get("state"):
        return vue("<div class=ko><b>state différent de celui envoye :</b> reponse refusee (protection CSRF).</div>")
    ETAT["code"] = code
    return vue(f"""<h2>Étape 2 : code d'autorisation reçu par le navigateur</h2>
{tableau([("code", code), ("state", request.args.get("state") + " (identique à la demande : OK)"), ("iss", request.args.get("iss", ""))])}
<div class=info>Ce code transite par le navigateur : seul, il ne suffit pas. Le client doit aussi prouver le code_verifier.</div>
<form action=/echanger method=post style="display:inline"><button>Échanger le code contre les jetons</button></form>
<form action=/echanger method=post style="display:inline"><input type=hidden name=faux value=1><button class=gris>Essayer avec un mauvais code_verifier</button></form>""")


def appeler_token(donnees):
    r = requests.post(TOKEN_URL, data=donnees, timeout=20)
    return r.status_code, r.json()


@app.post("/echanger")
def echanger():
    donnees = {"grant_type": "authorization_code", "code": ETAT.get("code", ""), "redirect_uri": ETAT.get("redirect_uri", REDIRECT), "client_id": CLIENT_ID}
    if ETAT.get("pkce"):
        donnees["code_verifier"] = "mauvais-" + secrets.token_urlsafe(48) if request.form.get("faux") else ETAT["verifier"]
    statut, rep = appeler_token(donnees)
    if statut != 200:
        return vue(f"""<h2>Réponse du point de terminaison /token : HTTP {statut}</h2><div class=ko>Échange refusé par Keycloak.</div>{json_html(rep)}
<a class=bouton href=/>Recommencer une demande</a>""")
    ETAT["jetons"] = rep
    return redirect("/jetons")


def valider_id_token(jeton):
    res = []
    jwks = jwt.PyJWKClient(KC_INTERNE + "/protocol/openid-connect/certs", cache_keys=False)
    try:
        c = jwt.decode(jeton, jwks.get_signing_key_from_jwt(jeton).key, algorithms=["RS256"], audience=CLIENT_ID, issuer=KC_PUBLIC)
        res += [("signature (JWKS)", "OK"), ("iss", "OK : " + c["iss"]), ("aud = client_id", "OK : " + str(c["aud"])), ("exp", f"OK : reste {int(c['exp'] - time.time())} s")]
        res.append(("nonce", "OK" if c.get("nonce") == ETAT.get("nonce") else "KO"))
    except jwt.PyJWTError as e:
        res.append(("validation", f"KO : {e}"))
    return res


@app.get("/jetons")
def jetons():
    j = ETAT.get("jetons")
    if not j:
        return vue("<div class=info>Aucun jeton : commencez par l'étape 1.</div>")
    corps = "<h2>Réponse du point de terminaison /token</h2>"
    corps += tableau([("token_type", j.get("token_type")), ("expires_in (s)", j.get("expires_in")), ("scope accordé", j.get("scope")),
                      ("access_token", "présent"), ("id_token", "présent" if j.get("id_token") else "ABSENT (pas de scope openid : pur OAuth 2.0)"),
                      ("refresh_token", "présent" if j.get("refresh_token") else "absent")])
    entete, charge = decoder_jwt(j["access_token"])
    corps += f"<h2>Access token : pour l'API (décodé)</h2>{json_html(entete)}{json_html(charge)}<details><summary>Jeton brut</summary><pre>{j['access_token']}</pre></details>"
    if j.get("id_token"):
        _, charge = decoder_jwt(j["id_token"])
        corps += f"<h2>ID token : pour le client (décodé)</h2>{json_html(charge)}<h2>Validation de l'ID token par le client</h2>{tableau(valider_id_token(j['id_token']), ('Contrôle', 'Résultat'))}"
    corps += """<h2>Actions</h2><form action=/userinfo method=post style="display:inline"><button>Appeler /userinfo</button></form>
<form action=/rejouer method=post style="display:inline"><button class=gris>Rejouer le code d'autorisation</button></form>
<a class=bouton href=/api>Aller aux appels API</a>"""
    return vue(corps)


@app.post("/rafraichir")
def rafraichir():
    j = ETAT.get("jetons", {})
    statut, rep = appeler_token({"grant_type": "refresh_token", "refresh_token": j.get("refresh_token", ""), "client_id": CLIENT_ID})
    if statut == 200:
        ETAT["jetons"] = rep
        return vue(f"<div class=ok>Nouveau jeton d'accès obtenu sans nouvelle authentification (expires_in = {rep.get('expires_in')} s).</div><a class=bouton href=/api>Retour aux appels API</a>")
    return vue(f"<div class=ko>Renouvellement refusé (HTTP {statut}).</div>{json_html(rep)}")


@app.post("/rejouer")
def rejouer():
    statut, rep = appeler_token({"grant_type": "authorization_code", "code": ETAT.get("code", ""), "redirect_uri": ETAT.get("redirect_uri", REDIRECT), "client_id": CLIENT_ID, "code_verifier": ETAT.get("verifier", "")})
    return vue(f"<h2>Deuxième utilisation du même code : HTTP {statut}</h2><div class={'ok' if statut == 200 else 'ko'}>Le code d'autorisation est à usage unique.</div>{json_html(rep)}<a class=bouton href=/jetons>Retour</a>")


@app.post("/userinfo")
def userinfo():
    j = ETAT.get("jetons", {})
    r = requests.get(KC_INTERNE + "/protocol/openid-connect/userinfo", headers={"Authorization": "Bearer " + j.get("access_token", "")}, timeout=20)
    try:
        contenu = r.json()
    except ValueError:
        contenu = {"reponse": r.text[:300], "www-authenticate": r.headers.get("WWW-Authenticate", "")}
    return vue(f"<h2>UserInfo : HTTP {r.status_code}</h2>{json_html(contenu)}<a class=bouton href=/jetons>Retour</a>")


def forger(jeton):
    """Ajoute notes.write a la charge du JWT sans pouvoir le resigner."""
    h, _, s = jeton.split(".")
    charge = decoder_jwt(jeton)[1]
    charge["scope"] = charge.get("scope", "") + " notes.write"
    nouveau = base64.urlsafe_b64encode(json.dumps(charge).encode()).rstrip(b"=").decode()
    return f"{h}.{nouveau}.{s}"


def appel_api(methode, jeton):
    entetes = {"Authorization": "Bearer " + jeton} if jeton else {}
    if methode == "POST":
        return requests.post(API + "/notes", json={"texte": "note créée depuis le Portail Notes"}, headers=entetes, timeout=20)
    return requests.get(API + "/notes", headers=entetes, timeout=20)


@app.route("/api", methods=["GET", "POST"])
def api():
    j = ETAT.get("jetons")
    if not j:
        return vue("<div class=info>Aucun jeton : commencez par l'étape 1.</div>")
    charge = decoder_jwt(j["access_token"])[1]
    corps = "<h2>Jeton utilisé</h2>" + tableau([("compte", charge.get("preferred_username")), ("scope", charge.get("scope")), ("aud", charge.get("aud")),
                                               ("roles", (charge.get("realm_access") or {}).get("roles")), ("expire dans (s)", int(charge["exp"] - time.time()))])
    corps += """<form method=post><h2>Appels à l'API</h2>
<button name=act value=lire>GET /notes</button><button name=act value=ecrire>POST /notes</button>
<button class=gris name=act value=sans>GET /notes sans jeton</button>
<button class=gris name=act value=forge>POST /notes avec jeton modifié (ajout notes.write)</button></form>
<form action=/rafraichir method=post><button class=gris>Renouveler (refresh_token)</button></form>"""
    act = request.form.get("act")
    if act:
        methode = "POST" if act in ("ecrire", "forge") else "GET"
        jeton = {"sans": None, "forge": forger(j["access_token"])}.get(act, j["access_token"])
        r = appel_api(methode, jeton)
        classe = "ok" if r.status_code < 300 else "ko"
        corps += f"<h2>Réponse de l'API</h2><div class={classe}><b>{methode} /notes : HTTP {r.status_code}</b></div>{json_html(r.json())}"
    return vue(corps)


@app.route("/service", methods=["GET", "POST"])
def service():
    corps = """<h2>Client Credentials : une application sans utilisateur</h2>
<form method=post><p>client_id : <input name=client_id value="service-batch" size=30></p>
<p>client_secret : <input name=client_secret size=45 type=password></p>
<p>scope : <input name=scope value="notes.read" size=30></p><button>Demander un jeton</button></form>"""
    if request.method == "POST":
        statut, rep = appeler_token({"grant_type": "client_credentials", "client_id": request.form["client_id"], "client_secret": request.form["client_secret"], "scope": request.form["scope"]})
        corps += f"<h2>Réponse de /token : HTTP {statut}</h2>"
        if statut != 200:
            return vue(corps + f"<div class=ko>Demande refusée.</div>{json_html(rep)}")
        charge = decoder_jwt(rep["access_token"])[1]
        corps += tableau([("id_token", "présent" if rep.get("id_token") else "absent"), ("refresh_token", "présent" if rep.get("refresh_token") else "absent"), ("expires_in (s)", rep.get("expires_in")), ("scope accordé", rep.get("scope"))])
        corps += "<h2>Access token (décodé)</h2>" + json_html(charge)
        for m in ("GET", "POST"):
            r = appel_api(m, rep["access_token"])
            corps += f"<h2>{m} /notes : HTTP {r.status_code}</h2>{json_html(r.json())}"
    return vue(corps)


@app.get("/deconnexion")
def deconnexion():
    params = {"client_id": CLIENT_ID, "post_logout_redirect_uri": BASE + "/"}
    if ETAT.get("jetons", {}).get("id_token"):
        params["id_token_hint"] = ETAT["jetons"]["id_token"]
    ETAT.clear()
    return redirect(KC_PUBLIC + "/protocol/openid-connect/logout?" + urlencode(params))
