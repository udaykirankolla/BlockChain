import hashlib
import json
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000/frontend.html"}})

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.create_block(previous_hash="1", proof=100)

    def create_block(self, proof, previous_hash=None):
        block = {'index': len(self.chain) + 1, 'timestamp': time(),
                 'transactions': self.current_transactions, 'proof': proof,
                 'previous_hash': previous_hash or self.hash(self.chain[-1]),}
        self.current_transactions, self.chain = [], self.chain + [block]
        return block

    def create_transaction(self, sender, recipient, amount):
        self.current_transactions += [{'sender': sender, 'recipient': recipient, 'amount': amount}]
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        target_prefix, proof = '0000', 0
        while not self.valid_proof(last_proof, proof, target_prefix):
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof, target_prefix):
        guess_hash = hashlib.sha256(f'{last_proof}{proof}'.encode()).hexdigest()
        return guess_hash.startswith(target_prefix)

node_identifier, blockchain = str(uuid4()).replace('-', ''), Blockchain()

@app.route('/mine', methods=['GET'])
@cross_origin()
def mine():
    last_block, last_proof = blockchain.last_block, blockchain.last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    blockchain.create_transaction(sender="0", recipient=node_identifier, amount=1)
    block = blockchain.create_block(proof, blockchain.hash(last_block))
    response = {k: block[k] for k in ('message', 'index', 'transactions', 'proof', 'previous_hash')}
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
@cross_origin()
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required): return 'Missing values', 400
    index = blockchain.create_transaction(*[values[k] for k in required])
    return jsonify({'message': f'Transaction will be added to block {index}'}), 201

@app.route('/chain', methods=['GET'])
@cross_origin()
def full_chain():
    return jsonify({'chain': blockchain.chain, 'length': len(blockchain.chain)}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
