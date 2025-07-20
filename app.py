from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")  # Permet à Flutter de se connecter

# Fichiers JSON
MATCHS_FILE = "matchs.json"
PARIS_FILE = "paris.json"
RESULTATS_FILE = "resultats.json"

# Créer les fichiers s'ils n'existent pas
for file in [MATCHS_FILE, PARIS_FILE, RESULTATS_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)

def load_json(file):
    with open(file, 'r') as f:
        return json.load(f)

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

# 🔄 Publier une publicité (envoyée à tous les clients connectés)
@app.route("/send_pub", methods=["POST"])
def send_pub():
    data = request.json
    message = data.get("message", "")
    socketio.emit("pub", message)  # Événement envoyé aux clients
    return jsonify({"status": "pub envoyée"}), 200

# ✅ Ajouter un match
@app.route("/add_match", methods=["POST"])
def add_match():
    data = request.json
    equipe1 = data.get("equipe1")
    equipe2 = data.get("equipe2")
    match_id = f"match_{len(load_json(MATCHS_FILE)) + 1}"
    new_match = {"id": match_id, "equipe1": equipe1, "equipe2": equipe2}
    matchs = load_json(MATCHS_FILE)
    matchs.append(new_match)
    save_json(MATCHS_FILE, matchs)
    return jsonify({"message": "Match ajouté", "match": new_match}), 201

# 📋 Voir tous les matchs
@app.route("/get_matchs", methods=["GET"])
def get_matchs():
    return jsonify(load_json(MATCHS_FILE))

# 🗳 Parier sur un match
@app.route("/parier", methods=["POST"])
def parier():
    data = request.json
    user = data.get("user")
    match_id = data.get("match_id")
    choix = data.get("choix")

    paris = load_json(PARIS_FILE)
    for p in paris:
        if p["user"] == user and p["match_id"] == match_id:
            return jsonify({"error": "Vous avez déjà parié sur ce match"}), 400

    paris.append({"user": user, "match_id": match_id, "choix": choix})
    save_json(PARIS_FILE, paris)
    return jsonify({"message": "Pari enregistré"}), 200

# ✅ Ajouter un résultat
@app.route("/add_resultat", methods=["POST"])
def add_resultat():
    data = request.json
    match_id = data.get("match_id")
    gagnant = data.get("gagnant")

    resultats = load_json(RESULTATS_FILE)
    resultats.append({"match_id": match_id, "gagnant": gagnant})
    save_json(RESULTATS_FILE, resultats)
    return jsonify({"message": "Résultat ajouté"}), 200

# 📊 Voir les résultats d’un utilisateur
@app.route("/get_resultat/<user>", methods=["GET"])
def get_resultat(user):
    paris = load_json(PARIS_FILE)
    resultats = load_json(RESULTATS_FILE)
    matchs = load_json(MATCHS_FILE)

    retour = []
    for p in paris:
        if p["user"] == user:
            match = next((m for m in matchs if m["id"] == p["match_id"]), None)
            resultat = next((r for r in resultats if r["match_id"] == p["match_id"]), None)
            if match and resultat:
                etat = "gagné" if p["choix"] == resultat["gagnant"] else "perdu"
                retour.append({
                    "match": f'{match["equipe1"]} vs {match["equipe2"]}',
                    "choix": p["choix"],
                    "gagnant": resultat["gagnant"],
                    "résultat": etat
                })

    return jsonify(retour), 200

# 🚀 Lancer le serveur
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
