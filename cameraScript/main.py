import sensor
import time
import network
import socket
import json

# Network Configuration
SSID = "Flavv"
KEY = "ZenZuchu"
HOST = ""
PORT = 8080

# Initialize Camera
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time=2000)
sensor.set_auto_gain(False)
sensor.set_auto_whitebal(False)

# Define Color Thresholds
green_threshold = (30, 100, -70, -10, -10, 60)   # Green for plant
yellow_threshold = (50, 100, -10, 40, 40, 80)    # Yellow for unhealthy leaves
red_threshold = (30, 100, 15, 127, 15, 127)      # Red for fruits

def connect_wifi():
    print("Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, KEY)

    attempt = 0
    while not wlan.isconnected():
        print('Trying to connect to "{:s}"... Attempt {}'.format(SSID, attempt + 1))
        time.sleep_ms(1000)
        attempt += 1
        if attempt >= 10:
            print("Failed to connect. Retrying from scratch...")
            wlan.active(False)
            time.sleep_ms(1000)
            return False

    print("WiFi Connected ", wlan.ifconfig())
    return True

def generate_html():
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plant Monitor</title>
        <style>
            :root {
                --primary: #4CAF50;
                --warning: #FFC107;
                --danger: #F44336;
                --dark: #333;
                --light: #f8f9fa;
            }

            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            body {
                background-color: var(--light);
                color: var(--dark);
                line-height: 1.6;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            header {
                background-color: var(--dark);
                color: white;
                padding: 1rem;
                text-align: center;
                border-radius: 8px 8px 0 0;
                margin-bottom: 20px;
            }

            .dashboard {
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 20px;
            }

            @media (max-width: 768px) {
                .dashboard {
                    grid-template-columns: 1fr;
                }
            }

            .card {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                overflow: hidden;
                margin-bottom: 20px;
            }

            .card-header {
                background-color: var(--primary);
                color: white;
                padding: 15px;
                font-weight: bold;
            }

            .card-body {
                padding: 20px;
            }

            .stream-container {
                position: relative;
                width: 100%;
                overflow: hidden;
                border-radius: 8px;
            }

            .stream-container img {
                width: 100%;
                height: auto;
                display: block;
            }

            .stats-container {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }

            .stat-item {
                display: flex;
                align-items: center;
                padding: 15px;
                border-radius: 8px;
                background-color: rgba(0,0,0,0.05);
            }

            .stat-icon {
                font-size: 2rem;
                margin-right: 15px;
            }

            .stat-value {
                font-size: 1.5rem;
                font-weight: bold;
            }

            .health-bar {
                height: 20px;
                background-color: #e0e0e0;
                border-radius: 10px;
                margin-top: 10px;
                overflow: hidden;
            }

            .health-fill {
                height: 100%;
                border-radius: 10px;
                transition: width 0.5s ease-in-out;
            }

            .good {
                background-color: var(--primary);
            }

            .warning {
                background-color: var(--warning);
            }

            .danger {
                background-color: var(--danger);
            }

            footer {
                text-align: center;
                margin-top: 20px;
                padding: 10px;
                color: #666;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Smart Plant Monitor</h1>
                <p>Real-time plant health monitoring with Nicla Vision</p>
            </header>

            <div class="dashboard">
                <div class="main-content">
                    <div class="card">
                        <div class="card-header">Live Stream</div>
                        <div class="card-body">
                            <div class="stream-container">
                                <img id="stream" src="/stream" alt="Plant Stream">
                            </div>
                        </div>
                    </div>
                </div>

                <div class="side-content">
                    <div class="card">
                        <div class="card-header">Plant Status</div>
                        <div class="card-body">
                            <div class="stats-container">
                                <div class="stat-item">
                                    <div class="stat-icon">🌿</div>
                                    <div class="stat-info">
                                        <div>Plant Detection</div>
                                        <div id="plant-status" class="stat-value">Checking...</div>
                                    </div>
                                </div>

                                <div class="stat-item">
                                    <div class="stat-icon">💧</div>
                                    <div class="stat-info">
                                        <div>Plant Health</div>
                                        <div id="health-value" class="stat-value">0%</div>
                                        <div class="health-bar">
                                            <div id="health-bar" class="health-fill" style="width: 0%"></div>
                                        </div>
                                    </div>
                                </div>

                                <div class="stat-item">
                                    <div class="stat-icon">🍓</div>
                                    <div class="stat-info">
                                        <div>Fruit Detection</div>
                                        <div id="fruit-status" class="stat-value">Checking...</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <div class="card-header">System Info</div>
                        <div class="card-body">
                            <div class="stats-container">
                                <div class="stat-item">
                                    <div class="stat-icon">⚡</div>
                                    <div class="stat-info">
                                        <div>FPS</div>
                                        <div id="fps-value" class="stat-value">0</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <footer>
                <p>Nicla Vision Plant Monitor &copy; 2023</p>
            </footer>
        </div>

        <script>
            // Function to update plant data
            function updatePlantData() {
                fetch('/data')
                    .then(response => response.json())
                    .then(data => {
                        // Update plant detection status
                        document.getElementById('plant-status').textContent =
                            data.plant_detected ? 'Detected' : 'Not Detected';

                        // Update health
                        const healthValue = Math.round(data.health_ratio);
                        document.getElementById('health-value').textContent = healthValue + '%';

                        const healthBar = document.getElementById('health-bar');
                        healthBar.style.width = healthValue + '%';

                        // Set health bar color based on value
                        if (healthValue >= 70) {
                            healthBar.className = 'health-fill good';
                        } else if (healthValue >= 40) {
                            healthBar.className = 'health-fill warning';
                        } else {
                            healthBar.className = 'health-fill danger';
                        }

                        // Update fruit detection
                        document.getElementById('fruit-status').textContent =
                            data.fruit_detected ? 'Detected' : 'Not Detected';

                        // Update FPS
                        document.getElementById('fps-value').textContent = data.fps.toFixed(1);
                    })
                    .catch(error => console.error('Error fetching data:', error));
            }

            // Update data every 2 seconds
            setInterval(updatePlantData, 2000);

            // Initial update
            updatePlantData();
        </script>
    </body>
    </html>
    """
    return html

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    s.bind([HOST, PORT])
    s.listen(5)
    s.setblocking(True)
    print(f"Server started at http://{network.WLAN(network.STA_IF).ifconfig()[0]}:{PORT}")
    return s

def handle_client(client, addr):
    print("Connected to " + addr[0] + ":" + str(addr[1]))

    # Read request from client
    request = client.recv(1024).decode('utf-8')

    # Parse the request path
    request_line = request.split('\n')[0]
    path = request_line.split(' ')[1]

    # FPS clock
    clock = time.clock()

    # Handle different endpoints
    if path == '/':
        # Serve the HTML page
        response = "HTTP/1.1 200 OK\r\n"
        response += "Content-Type: text/html\r\n\r\n"
        response += generate_html()
        client.sendall(response)

    elif path == '/stream':
        # Stream MJPEG
        client.sendall(
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: multipart/x-mixed-replace;boundary=frame\r\n"
            "Cache-Control: no-cache\r\n"
            "Pragma: no-cache\r\n\r\n"
        )

        try:
            while True:
                clock.tick()
                img = sensor.snapshot()

                # Process image (detect colors, draw rectangles, etc.)
                process_image(img)

                # Convert to JPEG and stream
                cframe = img.to_jpeg(quality=70)
                header = (
                    "\r\n--frame\r\n"
                    "Content-Type: image/jpeg\r\n"
                    "Content-Length: " + str(cframe.size()) + "\r\n\r\n"
                )
                client.sendall(header)
                client.sendall(cframe)
        except Exception as e:
            print("Stream error:", e)

    elif path == '/data':
        # Process a snapshot and return JSON data
        clock.tick()
        img = sensor.snapshot()
        data = process_image(img)
        data['fps'] = clock.fps()

        # Send JSON response
        json_data = json.dumps(data)
        response = "HTTP/1.1 200 OK\r\n"
        response += "Content-Type: application/json\r\n"
        response += "Content-Length: " + str(len(json_data)) + "\r\n\r\n"
        response += json_data

        client.sendall(response)

    else:
        # 404 Not Found
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
        response += "404 Not Found"
        client.sendall(response)

    client.close()

def process_image(img):
    # --- Detect Green (Plant Presence) ---
    green_blobs = img.find_blobs([green_threshold], pixels_threshold=500, area_threshold=500)
    yellow_blobs = img.find_blobs([yellow_threshold], pixels_threshold=300, area_threshold=300)
    red_blobs = img.find_blobs([red_threshold], pixels_threshold=300, area_threshold=300)

    # Process plant detection
    if green_blobs:
        plant_detected = True
        green_area = sum([b.area() for b in green_blobs])
        img.draw_rectangle(green_blobs[0].rect(), color=(0, 255, 0))
    else:
        plant_detected = False
        green_area = 0

    # --- Detect Yellow (Plant Health) ---
    yellow_area = sum([b.area() for b in yellow_blobs]) if yellow_blobs else 0
    if yellow_blobs:
        img.draw_rectangle(yellow_blobs[0].rect(), color=(255, 255, 0))

    # --- Health Calculation ---
    total_plant_area = green_area + yellow_area
    health_ratio = (green_area / total_plant_area) * 100 if total_plant_area > 0 else 0

    # --- Detect Red (Fruits) ---
    fruit_detected = False
    if red_blobs:
        fruit_detected = True
        img.draw_rectangle(red_blobs[0].rect(), color=(255, 0, 0))

    # Return data as dictionary
    return {
        'plant_detected': plant_detected,
        'health_ratio': health_ratio,
        'fruit_detected': fruit_detected,
        'green_area': green_area,
        'yellow_area': yellow_area
    }

# Main Loop
while True:
    if not connect_wifi():
        continue

    try:
        server_socket = start_server()

        while True:
            client, addr = server_socket.accept()
            try:
                handle_client(client, addr)
            except Exception as e:
                print("Client handling error:", e)
                client.close()

    except OSError as e:
        print("Socket error:", e)
        try:
            server_socket.close()
        except:
            pass
        time.sleep(1)
