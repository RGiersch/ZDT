
import websocket 
import uuid
import json
import urllib.request
import urllib.parse
import random
import sys

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('prompt', type=str, help='The prompt for image generation')
parser.add_argument('resolution', type=str, help='Sets the resolution of the image')
args = parser.parse_args(sys.argv[1:])

server_address = "127.0.0.1:8188"
client_id = str(uuid.uuid4())


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    req =  urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(server_address, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(server_address, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    print("get image")
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    current_node = ""
    
    while True:
        out = ws.recv()
        print("WebSocket received:", out)  # Debugging line

        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break  # Execution is done
                    else:
                        current_node = data['node']
        else:
                images_output = output_images.get(current_node, [])
                images_output.append(out[8:])
                output_images[current_node] = images_output
                continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        images_output = []
        if 'images' in node_output:
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
        output_images[node_id] = images_output


    return output_images

with open('generation.json', 'r', encoding='utf-8') as f:
    prompt_text = f.read()

prompt = json.loads(prompt_text)

prompt["3"]["inputs"]["seed"] = random.randint(0, 100000)

prompt["6"]["inputs"]["text"] = args.prompt 

print(repr(args.resolution))
if args.resolution.strip() == "schnell":
    prompt["5"]["inputs"]["width"] = 1819/2
    prompt["5"]["inputs"]["height"] = 1311/2
elif args.resolution.strip() == "qualität":
    prompt["5"]["inputs"]["width"] = 1819
    prompt["5"]["inputs"]["height"] = 1311
elif args.resolution.strip() == "hQualität":
    prompt["5"]["inputs"]["width"] = 1819*1.5
    prompt["5"]["inputs"]["height"] = 1311*1.5

ws = websocket.WebSocket()
try:
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    print("Connected to WebSocket successfully.")
except Exception as e:
    print("WebSocket connection failed:", e)
    exit(1)
images = get_images(ws, prompt)
ws.close() 

print("Received images:", images)

# display the output images:
final_node_id = max(int(node_id) for node_id in images)
if images[str(final_node_id)]:
    from PIL import Image
    import io
    image_data = images[str(final_node_id)][0]
    image = Image.open(io.BytesIO(image_data))
    image.save('generated_image.png')
    image = Image.open('generated_image.png')
    target_size=(1819, 1311)
    resized_image = image.resize(target_size, Image.LANCZOS)
    resized_image.save('generated_image.png') 

