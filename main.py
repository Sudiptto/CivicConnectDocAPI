from flask import Flask, request, jsonify
from flask_cors import CORS
from passwords import *
from quickstart import *

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


@app.route('/grabDocumentData/key=<key>', methods=['GET'])
def grabDocumentData(key):
    if key != secretKey:
        return jsonify({"error": "Invalid API key"}), 401
    else:
        documentData = generate_prompts_json()
        return jsonify(json.loads(documentData))


if __name__ == '__main__':
    app.run(debug=True)