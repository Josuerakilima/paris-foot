from flask import Flask, request, jsonify
from flask_socketio import SocketIO
import json, os, datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "secret!"
socketio = SocketIO(app, cors_allowed_origins="*")

# ---------- fichiers persistants ----------
DATA = {
    "MATCHS":  "matchs.json",
    "PARIS":   "paris.json",
    "RESULTS": "resultats.json",
    "USERS":   "users.json"          # ➜ nom, âge, soldes
}
for f in DATA.values():
    if not os.path.exists(f):
        with open(f, "w") as fp:
            json.dump([], fp)

# ---------- helpers ----------
def load(path):
    with open(path) as fp: return json.load(fp)

def save(path, data):
    with open(path, "w") as fp: json.dump(data, fp, indent=2)

def user_obj(name):
    users = load(DATA["USERS"])
    return next((u for u in users if u["nom"] == name), None)

# ---------- publicités temps‑réel ----------
@app.route("/send_pub", methods=["POST"])
def send_pub():
    msg = request.json.get("message", "")
    socketio.emit("pub", msg, broadcast=True)
    return {"ok": True}

# ---------- inscription utilisateur ----------
@app.route("/register", methods=["POST"])
def register():
    nom = request.json.get("nom")
    age = int(request.json.get("age", 0))
    if age < 18:
        return {"error": "Interdit aux moins de 18 ans"}, 403

    users = load(DATA["USERS"])
    if user_obj(nom):
        return {"message": "Déjà inscrit"}, 200

    users.append({"nom": nom, "age": age, "fc": 0, "usd": 0})
    save(DATA["USERS"], users)
    return {"message": f"Bienvenue {nom}"}, 201

# ---------- dépôt d’argent ----------
@app.route("/deposit", methods=["POST"])
def deposit():
    nom   = request.json.get("nom")
    fc    = int(request.json.get("fc", 0))
    usd   = int(request.json.get("usd", 0))

    user = user_obj(nom)
    if not user:
        return {"error": "Utilisateur inconnu"}, 404

    user["fc"]  += fc
    user["usd"] += usd
    users = load(DATA["USERS"])
    for u in users:
        if u["nom"] == nom:
            u.update(user)
            break
    save(DATA["USERS"], users)
    return {"message": "Dépôt enregistré", "solde": user}, 200

# ---------- consulter solde ----------
@app.route("/balance/<nom>")
def balance(nom):
    user = user_obj(nom)
    if not user:
        return {"error": "Utilisateur inconnu"}, 404
    return {"fc": user["fc"], "usd": user["usd"]}

# ---------- matchs / paris / résultats (inchangés) ----------
@app.route("/add_match", methods=["POST"])
def add_match():
    d = request.json
    m_id = f"match_{len(load(DATA['MATCHS']))+1}"
    newm = {"id": m_id, "equipe1": d["equipe1"], "equipe2": d["equipe2"]}
    m = load(DATA["MATCHS"]); m.append(newm); save(DATA["MATCHS"], m)
    socketio.emit("pub", "Nouveau match disponible !", broadcast=True)  # optionnel
    return {"match": newm}, 201

@app.route("/get_matchs")
def get_matchs(): return jsonify(load(DATA["MATCHS"]))

@app.route("/parier", methods=["POST"])
def parier():
    d = request.json
    user, match_id, choix = d["user"], d["match_id"], d["choix"]
    p = load(DATA["PARIS"])
    if any(x for x in p if x["user"]==user and x["match_id"]==match_id):
        return {"error":"Déjà parié"},400
    p.append({"user":user,"match_id":match_id,"choix":choix})
    save(DATA["PARIS"], p); return {"ok":True}

@app.route("/add_resultat", methods=["POST"])
def add_result():
    d = request.json
    r = load(DATA["RESULTS"]); r.append(d); save(DATA["RESULTS"], r)
    socketio.emit("pub", f"Résultat publié pour {d['match_id']}", broadcast=True)
    return {"ok":True}

@app.route("/get_resultat/<user>")
def get_res(user):
    p,res,mat = load(DATA["PARIS"]), load(DATA["RESULTS"]), load(DATA["MATCHS"])
    out=[]
    for x in p:
        if x["user"]==user:
            m=next((k for k in mat if k["id"]==x["match_id"]),None)
            r=next((y for y in res if y["match_id"]==x["match_id"]),None)
            if m and r:
                out.append({"match":f"{m['equipe1']} vs {m['equipe2']}",
                            "choix":x["choix"],"gagnant":r["gagnant"],
                            "résultat":"gagné" if x["choix"]==r["gagnant"] else "perdu"})
    return jsonify(out)

# ---------- lancement ----------
if __name__ == "__main__":
    import eventlet; eventlet.monkey_patch()
    port = int(os.environ.get("PORT",5000))
    socketio.run(app, host="0.0.0.0", port=port)

