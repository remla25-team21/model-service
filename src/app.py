from flask import Flask
from flask import request, current_app, jsonify
import logging
from flasgger import Swagger, swag_from
import requests
from libml.preprocessing import preprocess_train, preprocess_inference
import pickle
import numpy as np

# Download models from GitHub Releases
MODEL_VERSION = "v0.0.9"
BASE_URL = f"https://github.com/remla25-team21/model-training/releases/download/{MODEL_VERSION}"
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
with open("models/model.pkl", "rb") as f:
    model = pickle.load(f)

with open("models/vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

app = Flask(__name__)
swagger = Swagger(app)
logger = logging.getLogger(__name__)


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
        logger.debug(f"Preprocessing input data: {data}")
        processed_data = preprocess_inference(data, "models/vectorizer.pkl")

        np.set_printoptions(threshold=np.inf)

        logger.debug(f"processed_data {processed_data}")

        # Fetch model and run predictions
        prediction = model.predict(processed_data.reshape(1, -1))

        # Return results
        result = {"prediction": int(prediction[0])}
        return jsonify(result), 200

    except Exception as e:
        logger.exception(f"Prediction error: {str(e)}")
        return jsonify({"error": "Prediction failed"}), 500


if __name__ == "__main__":
    app.run(debug=True)
