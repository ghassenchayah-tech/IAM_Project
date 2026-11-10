"""Serveur de ressources : API de notes protegee par des jetons d'acces (JWT)."""
import os
import time

import jwt
from flask import Flask, jsonify, request

ISSUER = os.environ["KC_ISSUER"]
AUDIENCE = os.environ["API_AUDIENCE"]
JWKS = jwt.PyJWKClient(os.environ["KC_INTERNE"] + "/protocol/openid-connect/certs", cache_keys=False)
NOTES = [{"id": 1, "auteur": "système", "texte": "Bienvenue sur l'API de notes Polycorp"}]
app = Flask(__name__)


def refus(statut, code, raison, controles):
    r = jsonify(statut=statut, erreur=code, raison=raison, controles=controles)
    r.status_code = statut
    r.headers["WWW-Authenticate"] = f'Bearer error="{code}"'
    return r


def controler(scope_requis, role_requis=None):
    """Retourne (revendications, controles, reponse_de_refus)."""
    controles = {}
    entete = request.headers.get("Authorization", "")
    if not entete.startswith("Bearer "):
        return None, controles, refus(401, "invalid_request", "Aucun jeton Bearer fourni", controles)
    jeton = entete[7:]
    try:
        cle = JWKS.get_signing_key_from_jwt(jeton).key
        jwt.decode(jeton, cle, algorithms=["RS256"], options={"verify_aud": False, "verify_iss": False, "verify_exp": False})
    except jwt.PyJWTError as e:
        controles["signature"] = "KO"
        return None, controles, refus(401, "invalid_token", f"Signature invalide : {e}", controles)
    controles["signature"] = "OK (clé publique JWKS)"
    c = jwt.decode(jeton, options={"verify_signature": False})
    if c.get("iss") != ISSUER:
        controles["iss"] = "KO"
        return None, controles, refus(401, "invalid_token", f"Émetteur inattendu : {c.get('iss')}", controles)
    controles["iss"] = "OK"
    aud = c.get("aud") or []
    aud = [aud] if isinstance(aud, str) else aud
    if AUDIENCE not in aud:
        controles["aud"] = f"KO : {aud}"
        return None, controles, refus(401, "invalid_token", f"Jeton non destiné à {AUDIENCE} (aud={aud})", controles)
    controles["aud"] = f"OK ({AUDIENCE})"
    if c.get("exp", 0) <= time.time():
        controles["exp"] = "KO"
        return None, controles, refus(401, "invalid_token", f"Jeton expiré depuis {int(time.time() - c['exp'])} s", controles)
    controles["exp"] = f"OK (reste {int(c['exp'] - time.time())} s)"
    scopes = c.get("scope", "").split()
    if scope_requis not in scopes:
        controles["scope"] = f"KO : {scopes}"
        return None, controles, refus(403, "insufficient_scope", f"Scope {scope_requis} absent du jeton", controles)
    controles["scope"] = f"OK ({scope_requis})"
    if role_requis:
        roles = c.get("realm_access", {}).get("roles", [])
        if role_requis not in roles:
            controles["role"] = "KO"
            return None, controles, refus(403, "access_denied", f"Le compte n'a pas le rôle {role_requis}", controles)
        controles["role"] = f"OK ({role_requis})"
    return c, controles, None


@app.get("/")
def accueil():
    return jsonify(service="API Notes", routes={"GET /notes": "scope notes.read", "POST /notes": "scope notes.write + rôle editeur"})


@app.get("/notes")
def lire():
    c, controles, r = controler("notes.read")
    if r:
        return r
    return jsonify(statut=200, compte=c.get("preferred_username"), client=c.get("azp"), controles=controles, notes=NOTES)


@app.post("/notes")
def ecrire():
    c, controles, r = controler("notes.write", "editeur")
    if r:
        return r
    note = {"id": len(NOTES) + 1, "auteur": c.get("preferred_username"), "texte": (request.get_json(silent=True) or {}).get("texte", "note de test")}
    NOTES.append(note)
    return jsonify(statut=201, compte=c.get("preferred_username"), client=c.get("azp"), controles=controles, note=note), 201
