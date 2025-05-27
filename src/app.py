from flask import Flask
from flask import request, jsonify
from flasgger import Swagger, swag_from
import requests
from libml.preprocessing import preprocess_inference

import pickle
import numpy as np
import os
import logging
from config import MODEL_VERSION, BASE_URL

# Set up environment variables
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = os.environ.get("PORT", 8080)


if not os.path.exists("models"):
    os.makedirs("models")

# Download models from GitHub Releases
files = {
    "model": f"{BASE_URL}/sentiment_model_{MODEL_VERSION}.pkl",
    "vectorizer": f"{BASE_URL}/c1_BoW_Sentiment_Model_{MODEL_VERSION}.pkl",
}
for name, url in files.items():
    response = requests.get(url)
    response.raise_for_status()
    with open(f"models/{name}.pkl", "wb") as f:
        f.write(response.content)

# Load downloaded model and vectorizer
try:
    with open("models/model.pkl", "rb") as f:
        model = pickle.load(f)
    logging.info("Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    raise

try:
    with open("models/vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    logging.info("Vectorizer loaded successfully.")
except Exception as e:
    logging.error(f"Error loading vectorizer: {e}")
    raise

app = Flask(__name__)
swagger = Swagger(app)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@app.route("/")
def home():
    """
    Home endpoint
    ---
    responses:
      200:
        description: Welcome message
    """
    return "Hello, welcome to the model-service!"


@app.route("/predict", methods=["POST"])
@swag_from(
    {
        "summary": "Make a sentiment prediction based on input review",
        "tags": ["Prediction"],
        "parameters": [
            {
                "name": "data",
                "in": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "example": "I love this product!"}
                    },
                    "required": ["data"],
                },
            }
        ],
        "responses": {
            200: {
                "description": "Prediction successful",
                "schema": {
                    "type": "object",
                    "properties": {"prediction": {"type": "string"}},
                },
            },
            400: {"description": "Bad Request"},
            500: {"description": "Internal Server Error"},
        },
    }
)
def predict():
    try:
        data = request.get_json()
        data = data["data"]
        if not data:
            return jsonify({"error": "No input data provided"}), 400

        # Use lib-ml function for preprocessing
        logging.debug(f"Preprocessing input data: {data}")
        processed_data = preprocess_inference(data, "models/vectorizer.pkl")

        np.set_printoptions(threshold=np.inf)

        logging.debug(f"processed_data {processed_data}")

        # Fetch model and run predictions
        batch_size = 1
        flatten_dim = -1
        prediction = model.predict(processed_data.reshape(batch_size, flatten_dim))
        logging.info(f"Prediction result: {prediction[0]}")

        # Return results
        result = {"prediction": int(prediction[0])}
        return jsonify(result), 200

    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return jsonify({"error": "Prediction failed"}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
