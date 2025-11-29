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


@app.route("/ledger")
def view_ledger():
    """Route to view the separate ledger dashboard."""
    return render_template("view_transactions.html")


@app.route("/auto_sign", methods=["POST"])
def auto_sign():
    """
    Simulates the doctor signing the prescription with their private key.
    """
    # Get data from the form
    values = request.form.to_dict()


    # Security Check: Is the user authorized?
    if values.get("network_key") != NETWORK_KEY:
        return jsonify({"message": "Unauthorized Network Key"}), 401
   
    prescriber_id = values.get("prescriber_public_key")


    if prescriber_id not in DOCTOR_SECRETS:
        return jsonify({"message": "Doctor not found in database"}), 400


    # Get the doctor's secret key
    secret_key = DOCTOR_SECRETS[prescriber_id]


    # Generate the digital signature
    signature = generate_signature(
        secret_key,
        prescriber_id,
        values.get("pharmacy_public_key"),
        values.get("patient_id"),
        values.get("drug_name"),
        values.get("dosage"),
        values.get("quantity")
    )


    return jsonify({"signature": signature})




@app.route("/new_transaction", methods=["POST"])
def new_transaction():
    """
    Submits a new prescription to the network.
    """
    values = request.form.to_dict()


    # 1. Check Network Access
    if values.get("network_key") != NETWORK_KEY:
        return jsonify({"message": "Unauthorized"}), 401


    prescriber = values.get("prescriber_public_key")
    pharmacy = values.get("pharmacy_public_key")
    provided_signature = values.get("signature")


    # 2. Verify Doctor and Pharmacy exist
    if prescriber not in DOCTOR_SECRETS:
        return jsonify({"message": "Invalid Doctor ID"}), 400
   
    if pharmacy not in PHARMACY_WHITELIST:
        return jsonify({"message": "Invalid Pharmacy ID"}), 400


    # 3. VERIFY SIGNATURE (The core security step)
    # We regenerate the signature using the data we received and the doctor's secret.
    # If it matches the signature they sent, the data is authentic.
    real_secret = DOCTOR_SECRETS[prescriber]
   
    expected_signature = generate_signature(
        real_secret,
        prescriber,
        pharmacy,
        values.get("patient_id"),
        values.get("drug_name"),
        values.get("dosage"),
        values.get("quantity")
    )


    if provided_signature != expected_signature:
        print("!! Security Alert: Invalid Signature Detected !!")
        return jsonify({"message": "Invalid Signature - Data may have been tampered with."}), 400


    # 4. Create Transaction Object
    # Create a unique ID for this prescription (Hash of the data)
    raw_tx_string = prescriber + pharmacy + values["patient_id"] + values["drug_name"]
    tx_id = hashlib.sha256(raw_tx_string.encode()).hexdigest()


    transaction = {
        "prescription_id": tx_id,
        "prescriber_public_key": prescriber,
        "pharmacy_public_key": pharmacy,
        "patient_id": values["patient_id"],
        "drug_name": values["drug_name"],
        "dosage": values["dosage"],
        "quantity": values["quantity"],
        "signature": provided_signature
    }


    # Add to the "Mempool" (Waiting area)
    blockchain.add_prescription(transaction)
   
    print(f"New Prescription Added: {values['drug_name']} for {values['patient_id']}")
   
    return jsonify({"message": "Prescription successfully added to pool", "id": tx_id})




@app.route("/mine", methods=["GET"])
def mine():
    """
    Mines a block to secure the pending transactions.
    """
    # Check authorization (optional, but good practice)
    if request.args.get("network_key") != NETWORK_KEY:
        return jsonify({"message": "Unauthorized"}), 401


    last_block = blockchain.get_last_block()
    previous_nonce = last_block["nonce"]
   
    # Start the "Work" (Solving the puzzle)
    nonce = blockchain.proof_of_work(previous_nonce)
   
    previous_hash = blockchain.hash_block(last_block)
    new_block = blockchain.create_block(nonce, previous_hash)


    print(f"Block #{new_block['block_number']} Mined! Hash: {previous_hash[:10]}...")


    return jsonify(new_block)




@app.route("/chain", methods=["GET"])
def full_chain():
    """Returns the full blockchain data."""
    return jsonify({
        "chain": blockchain.chain,
        "length": len(blockchain.chain)
    })




@app.route("/transactions/get", methods=["GET"])
def get_pending():
    """Returns transactions waiting to be mined."""
    return jsonify({"transactions": blockchain.pending_prescriptions})




@app.route("/validate", methods=["GET"])
def validate_chain():
    """Checks if the chain is valid."""
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        return jsonify({"valid": True, "message": "Blockchain is secure."})
    else:
        return jsonify({"valid": False, "message": "Blockchain invalid!"})




if __name__ == "__main__":
    # Running on port 5001 to avoid conflicts
    app.run(port=5001, debug=True)