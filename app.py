from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# Fichier JSON des matchs
MATCH_FILE = 'matchs.json'
BET_FILE = 'paris.json'
RESULT_FILE = 'resultats.json'

# Créer les fichiers vides s'ils n'existent pas
for file in [MATCH_FILE, BET_FILE, RESULT_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([], f)


@app.route('/add_match', methods=['POST'])
def add_match():
    data = request.json
    with open(MATCH_FILE, 'r+') as f:
        matchs = json.load(f)
        matchs.append(data)
        f.seek(0)
        json.dump(matchs, f, indent=2)
    return jsonify({'message': 'Match ajouté'})


@app.route('/get_matches', methods=['GET'])
def get_matches():
    with open(MATCH_FILE) as f:
        matchs = json.load(f)
    return jsonify(matchs)


@app.route('/place_bet', methods=['POST'])
def place_bet():
    data = request.json
    with open(BET_FILE, 'r+') as f:
        paris = json.load(f)
        paris.append(data)
        f.seek(0)
        json.dump(paris, f, indent=2)
    return jsonify({'message': 'Pari enregistré'})


@app.route('/post_result', methods=['POST'])
def post_result():
    data = request.json
    with open(RESULT_FILE, 'r+') as f:
        resultats = json.load(f)
        resultats.append(data)
        f.seek(0)
        json.dump(resultats, f, indent=2)
    return jsonify({'message': 'Résultat ajouté'})


@app.route('/get_results/<username>', methods=['GET'])
def get_results(username):
    with open(BET_FILE) as f1, open(RESULT_FILE) as f2:
        paris = json.load(f1)
        resultats = json.load(f2)
        resultats_dict = {r['match']: r['resultat'] for r in resultats}
        user_results = []
        for p in paris:
            if p['user'] == username and p['match'] in resultats_dict:
                gagne = p['choix'] == resultats_dict[p['match']]
                user_results.append({
                    'match': p['match'],
                    'choix': p['choix'],
                    'resultat': resultats_dict[p['match']],
                    'gagne': gagne
                })
    return jsonify(user_results)


@app.route('/')
def home():
    return "API de paris opérationnelle !"

