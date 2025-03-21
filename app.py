from flask import Flask, request, jsonify, render_template,  send_from_directory
import asyncio
import sys
import json
import random
import subprocess
import os

app = Flask(__name__)

@app.route('/image')
def image_page():
    return render_template('images.html')

@app.route('/generated_image.png')
def serve_image():
    return send_from_directory('.', 'generated_image.png')

@app.route('/image/generate', methods=['POST'])
def generate_image():
    data = request.json
    prompt = data.get("prompt")
    resolution = data.get("resolution")

    try:
        python_executable = sys.executable
        script_path = os.path.join(os.path.dirname(__file__), 'image_generator.py')

        args = [
            python_executable, 
            script_path, 
            json.dumps(prompt),  # Prompt bleibt als JSON-String
            resolution  # Direkt als String übergeben
        ]
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"Error output: {stderr}")
            return jsonify({"error": stderr}), 500
        
        return jsonify({
            "image": "generated_image.png",
        })
               
    except Exception as e:
        print(f"Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)