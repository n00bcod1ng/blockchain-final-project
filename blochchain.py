from flask import Flask, jsonify, request, render_template
import hashlib
import json
from time import time

app = Flask(__name__)

# ==========================================
# 1. NETWORK CONFIGURATION (Simulated Database)
# ==========================================

# The "password" for the network
NETWORK_KEY = "hospital-network-2025"

# Doctor "Private Keys" (Simulated for the project)
# In a real system, these would be RSA private keys held on a doctor's smart card.
DOCTOR_SECRETS = {
    "doctor_emmanuel": "emma-secret444",
    "doctor_alex": "alex-secret123",
    "doctor_kim": "kim-key-987",
    "doctor_graham": "graham-secret555"
}

# Approved Pharmacies
PHARMACY_WHITELIST = [
    "pharmacy_01",
    "pharmacy_downtown",
    "pharmacy_critical_care"
]

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================

def generate_signature(secret_key, prescriber, pharmacy, patient, drug, dosage, qty):
    """
    Creates a unique signature for the prescription.
    If any data changes, this signature will change, alerting the network.
    """
    raw_data = prescriber + pharmacy + patient + drug + dosage + qty + secret_key
    return hashlib.sha256(raw_data.encode()).hexdigest()

# ==========================================
# 3. BLOCKCHAIN CLASS
# ==========================================

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_prescriptions = []
        
        # Create the Genesis Block (The first block in the chain)
        self.create_block(nonce=1, previous_hash="0")

    def create_block(self, nonce, previous_hash):
        """
        Packages pending prescriptions into a new block and adds it to the chain.
        """
        block = {
            "block_number": len(self.chain) + 1,
            "timestamp": time(),
            "transactions": self.pending_prescriptions,
            "nonce": nonce,
            "previous_hash": previous_hash
        }

        self.pending_prescriptions = [] # Clear the list since they are now recorded
        self.chain.append(block)
        return block

    def get_last_block(self):
        return self.chain[-1]

    def add_prescription(self, prescription_data):
        self.pending_prescriptions.append(prescription_data)
        return True

    def proof_of_work(self, previous_nonce):
        """
        The 'Mining' process.
        We try to find a number (nonce) that makes the hash start with '0000'.
        This proves work was done to secure the network.
        """
        new_nonce = 0
        while True:
            # Create a string of the previous and current nonce
            guess = f"{previous_nonce}{new_nonce}".encode()
            guess_hash = hashlib.sha256(guess).hexdigest()

            # The Puzzle: Does the hash start with 4 zeros?
            if guess_hash.startswith("0000"):
                return new_nonce
            
            new_nonce += 1

    def hash_block(self, block):
        """Hashes an entire block to create a unique ID."""
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def is_chain_valid(self, chain):
        """
        Checks if the Blockchain has been tampered with.
        """
        previous_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Check 1: Does the 'previous_hash' match the actual hash of the last block?
            if block["previous_hash"] != self.hash_block(previous_block):
                return False

            # Check 2: Is the Proof of Work correct? (Does it start with 0000?)
            prev_nonce = previous_block["nonce"]
            curr_nonce = block["nonce"]
            guess = f"{prev_nonce}{curr_nonce}".encode()
            guess_hash = hashlib.sha256(guess).hexdigest()

            if not guess_hash.startswith("0000"):
                return False

            previous_block = block
            current_index += 1

        return True

# Initialize the Blockchain
blockchain = Blockchain()


# ==========================================
# 4. FLASK ROUTES (Web Interface)
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")