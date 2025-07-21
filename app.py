from flask import Flask, request, jsonify, session, render_template, send_file
from flask_cors import CORS
import sqlite3, uuid, requests, io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import time # To simulate a slight delay if needed for debugging

app = Flask(__name__)
app.secret_key = "supersecret" # IMPORTANT: Keep this a strong, unique secret in a real application, preferably from an environment variable!
CORS(app, supports_credentials=True) # Enable CORS for all origins, allowing credentials

# Data.gov.in API details for Indian Railways Train Route
# You must obtain your own API key from data.gov.in
API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"
API_BASE_URL = "https://api.data.gov.in/resource/13051d52-05c2-4130-9e7b-891bdde84076"

# A small dictionary for dummy train names (for route search if API doesn't give them)
# In a real app, you'd fetch this or have a more comprehensive DB
train_names_mapping = {
    "12001": "Bhopal Shatabdi Express",
    "12002": "Bhopal Shatabdi Express", # Reverse direction
    "12101": "Jnaneswari Express",
    "12102": "Jnaneswari Express",
    "12301": "Howrah Rajdhani Express",
    "12302": "Howrah Rajdhani Express",
    "12801": "Puri Express",
    "12802": "Puri Express",
    "12401": "Magadh Express",
    "12402": "Magadh Express",
    "12951": "Mumbai Rajdhani Express",
    "12952": "Mumbai Rajdhani Express",
    "12555": "Gorakhdham Express",
    "12556": "Gorakhdham Express",
    "12621": "Tamil Nadu Express",
    "12622": "Tamil Nadu Express",
    "12723": "Telangana Express",
    "12724": "Telangana Express",
    # Add more as you discover them from the API or your own data
}


def init_db():
    """Initializes the SQLite database tables if they don't exist."""
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pnr TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        passenger TEXT NOT NULL,
        age INTEGER NOT NULL,
        berth TEXT NOT NULL,
        train_no TEXT NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (username) REFERENCES users (username)
    )''')
    con.commit()
    con.close()

# Ensure the database is initialized when the application starts
with app.app_context():
    init_db()

@app.route("/")
def index():
    """Serves the main HTML file."""
    # Assuming your HTML file is in a 'templates' folder or the same directory as app.py
    # If not, you might need to adjust the path or copy index.html to 'templates'
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    """Handles user registration."""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        con = sqlite3.connect("users.db")
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        con.commit()
        return jsonify({"message": "Registered successfully!"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists. Please choose another."}), 409 # 409 Conflict
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({"error": "An error occurred during registration."}), 500
    finally:
        if con:
            con.close()

@app.route("/login", methods=["POST"])
def login():
    """Handles user login."""
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    con = sqlite3.connect("users.db")
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    con.close()

    if user:
        session["user"] = username
        return jsonify({"message": "Login successful"})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route("/logout")
def logout():
    """Handles user logout."""
    session.pop("user", None)
    return jsonify({"message": "Logged out successfully"})

@app.route("/me")
def me():
    """Returns the current logged-in user's username."""
    return jsonify({"user": session.get("user")})

@app.route("/route")
def get_route():
    """Fetches and returns the route for a specific train number from the external API."""
    train_no = request.args.get("train_no")
    if not train_no:
        return jsonify({"error": "Train number is required"}), 400

    print(f"Fetching route for train: {train_no}")
    # API call to get route for a specific train number
    url = f"{API_BASE_URL}?api-key={API_KEY}&format=json&filters[train_no]={train_no}"
    
    try:
        res = requests.get(url, timeout=10) # Add a timeout for safety
        res.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        records = res.json().get("records", [])

        if not records:
            print(f"No records found for train {train_no} from API.")
            return jsonify([]) # Return empty list if no records found for this train

        route = []
        for r in records:
            # Ensure all required keys exist and handle potential type errors
            try:
                route.append({
                    "seq": int(r.get("seq", 0)),
                    "station_code": r.get("station_code", "N/A"),
                    "station_name": r.get("station_name", "N/A"),
                    "arrival_time": r.get("arrival_time", "-"),
                    "departure_time": r.get("departure_time", "-"),
                    "distance_km": float(r.get("_distance", 0.0)) # Use float for distance
                })
            except (ValueError, TypeError) as e:
                print(f"Skipping record due to data parsing error: {r} - {e}")
                continue # Skip malformed records

        # Sort by sequence number
        return jsonify(sorted(route, key=lambda x: x["seq"]))
    except requests.exceptions.RequestException as e:
        print(f"Error fetching train route for {train_no}: {e}")
        return jsonify({"error": "Failed to fetch train route from external API"}), 500
    except ValueError as e:
        print(f"Error parsing JSON for train route {train_no}: {e}")
        return jsonify({"error": "Invalid data received from external API"}), 500


@app.route("/search")
def search_trains():
    """
    Searches for trains between a given source and destination station using the external API.
    This endpoint now actively filters the full API data to find routes.
    """
    source = request.args.get('source', '').strip().lower()
    destination = request.args.get('destination', '').strip().lower()

    if not source or not destination:
        return jsonify({"error": "Source and destination stations are required"}), 400

    print(f"\n--- Backend Search Request ---")
    print(f"Searching from: '{source}' to: '{destination}'")

    # Set a very high limit to try and get all relevant data.
    # The API might still cap it, but this is the best we can do.
    # In a real system, you'd handle pagination or use a more efficient data source.
    url = f"{API_BASE_URL}?api-key={API_KEY}&format=json&limit=50000" # Increased limit
    
    try:
        res = requests.get(url, timeout=30) # Increased timeout for large data fetch
        res.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        
        raw_records = res.json().get("records", [])
        print(f"Received {len(raw_records)} records from data.gov.in API for route search.")

        # Process records to build train routes
        # Key: train_no, Value: {"name": str, "stops": [(station_name, seq)]}
        trains_data = {} 
        for r in raw_records:
            train_no = r.get("train_no")
            station_name = r.get("station_name", "").strip().lower()
            seq_num = r.get("seq")
            train_name = r.get("train_name")

            if not train_no or not station_name or seq_num is None:
                # Skip records that don't have essential information
                continue
            
            try:
                seq_num = int(seq_num)
            except ValueError:
                # Skip records with invalid sequence numbers
                continue

            if train_no not in trains_data:
                # Use mapping if train_name is missing from API record
                trains_data[train_no] = {
                    "name": train_name if train_name else train_names_mapping.get(train_no, f"Train {train_no}"),
                    "stops": []
                }
            trains_data[train_no]["stops"].append((station_name, seq_num))

        print(f"Parsed data for {len(trains_data)} unique trains.")

        matched_trains = []
        for train_no, info in trains_data.items():
            stops = sorted(info["stops"], key=lambda x: x[1]) # Ensure stops are sorted by sequence
            
            src_seq = -1
            dst_seq = -1
            
            # Find the sequence numbers for source and destination
            for station, seq in stops:
                if station == source:
                    src_seq = seq
                if station == destination:
                    dst_seq = seq
            
            # Check if both stations were found and if source comes before destination
            if src_seq != -1 and dst_seq != -1 and src_seq < dst_seq:
                matched_trains.append({
                    "train_no": train_no,
                    "name": info["name"]
                })
        
        print(f"Found {len(matched_trains)} matching trains.")
        print(f"Matched trains: {matched_trains}")
        print(f"--- End Search Request ---")
        return jsonify(matched_trains)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from external API for search: {e}")
        return jsonify({"error": "Failed to fetch train data from external API. Please try again later."}), 500
    except ValueError as e:
        print(f"Error parsing JSON response from API during search: {e}")
        return jsonify({"error": "Invalid data format received from external API."}), 500
    except Exception as e:
        print(f"An unexpected error occurred during search: {e}")
        return jsonify({"error": "An unexpected server error occurred."}), 500


@app.route("/book", methods=["POST"])
def book_ticket():
    """Handles ticket booking and generates PNR."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    passenger = data.get("passenger")
    age = data.get("age")
    berth = data.get("berth")
    train_no = data.get("train_no")
    date = data.get("date")

    if not all([passenger, age, berth, train_no, date]):
        return jsonify({"error": "All booking details are required."}), 400

    con = sqlite3.connect("users.db")
    cur = con.cursor()
    
    # Check current bookings for this train, date, and berth type
    # This is a very simplistic seat allocation. In a real system, you'd have
    # more sophisticated seat management.
    cur.execute("SELECT COUNT(*) FROM bookings WHERE train_no=? AND date=? AND berth=?", (train_no, date, berth))
    current_bookings_count = cur.fetchone()[0]
    
    seat_limit = 50 if berth.lower() == "sleeper" else 20
    
    status = "Confirmed" if current_bookings_count < seat_limit else f"Waiting List {current_bookings_count - seat_limit + 1}"
    
    pnr = str(uuid.uuid4())[:10].upper() # Generate a unique PNR

    try:
        cur.execute("""INSERT INTO bookings (pnr, username, passenger, age, berth, train_no, date, status)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (pnr, session["user"], passenger, age, berth, train_no, date, status))
        con.commit()
    except sqlite3.Error as e:
        con.rollback()
        print(f"Database error during booking: {e}")
        return jsonify({"error": "Failed to book ticket due to a database error."}), 500
    finally:
        if con:
            con.close()

    return jsonify({
        "pnr": pnr,
        "passenger": passenger,
        "age": age,
        "berth": berth,
        "train_no": train_no,
        "date": date,
        "status": status
    })

@app.route("/pnr/<pnr_number>")
def get_pnr(pnr_number):
    """Retrieves PNR status for a given PNR number and logged-in user."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    try:
        # Ensure only the logged-in user can see their own PNR
        cur.execute("SELECT * FROM bookings WHERE pnr=? AND username=?", (pnr_number, session["user"]))
        row = cur.fetchone()
        con.close()

        if row:
            # Unpack the tuple: id, pnr, username, passenger, age, berth, train_no, date, status
            _, pnr, _, passenger, age, berth, train_no, date, status = row
            return jsonify({
                "pnr": pnr,
                "passenger": passenger,
                "age": age,
                "berth": berth,
                "train_no": train_no,
                "date": date,
                "status": status,
                # Dummy coach data (not stored in DB, so just for display)
                "coach": "S1" if berth.lower() == "sleeper" else "A1" 
            })
        return jsonify({"error": "PNR not found or does not belong to your account"}), 404
    except Exception as e:
        print(f"Error fetching PNR {pnr_number}: {e}")
        return jsonify({"error": "An error occurred while fetching PNR status."}), 500
    finally:
        if con:
            con.close()


@app.route("/history")
def get_booking_history():
    """Retrieves all booking history for the logged-in user."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session["user"]
    con = sqlite3.connect("users.db")
    cur = con.cursor()
    try:
        cur.execute("SELECT pnr, passenger, age, berth, train_no, date, status FROM bookings WHERE username=? ORDER BY date DESC, id DESC", (username,))
        bookings = cur.fetchall()
        
        history_list = []
        for booking in bookings:
            # Match the order of SELECT statement
            history_list.append({
                "pnr": booking[0],
                "passenger": booking[1],
                "age": booking[2],
                "berth": booking[3],
                "train_no": booking[4],
                "date": booking[5],
                "status": booking[6]
            })
        print(f"Fetched {len(history_list)} bookings for user {username}")
        return jsonify(history_list)
    except Exception as e:
        print(f"Error fetching booking history for {username}: {e}")
        return jsonify({"error": "Failed to retrieve booking history."}), 500
    finally:
        if con:
            con.close()


@app.route("/download/<pnr_number>")
def download_ticket(pnr_number):
    """Generates and downloads a PDF ticket for a given PNR."""
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    con = sqlite3.connect("users.db")
    cur = con.cursor()
    try:
        cur.execute("SELECT * FROM bookings WHERE pnr=? AND username=?", (pnr_number, session["user"]))
        row = cur.fetchone()
        
        if not row:
            print(f"Ticket {pnr_number} not found or unauthorized access for user {session['user']}")
            return jsonify({"error": "Ticket not found or unauthorized access"}), 404

        # Unpack the tuple: id, pnr, username, passenger, age, berth, train_no, date, status
        _, pnr, _, passenger, age, berth, train_no, date, status = row

        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        p.setFillColorRGB(0.95, 0.42, 0.13) # WOOK orange color
        p.setFont("Helvetica-Bold", 24)
        p.drawString(50, 750, "WOOK Train Ticket")
        
        p.setFillColorRGB(0, 0, 0) # Black
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, 710, "Booking Details:")

        p.setFont("Helvetica", 12)
        p.drawString(70, 680, f"PNR Number: {pnr}")
        p.drawString(70, 660, f"Passenger Name: {passenger}")
        p.drawString(70, 640, f"Age: {age}")
        p.drawString(70, 620, f"Train Number: {train_no}")
        p.drawString(70, 600, f"Berth Type: {berth}")
        p.drawString(70, 580, f"Date of Travel: {date}")
        p.drawString(70, 560, f"Booking Status: {status}")

        # Add a footer or logo (optional)
        p.setFont("Helvetica-Oblique", 10)
        p.drawString(50, 50, "Thank you for booking with WOOK!")

        p.showPage()
        p.save()
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name=f"WOOK_Ticket_{pnr}.pdf", mimetype='application/pdf')
    except Exception as e:
        print(f"Error generating PDF for PNR {pnr_number}: {e}")
        return jsonify({"error": "An error occurred while generating the ticket PDF."}), 500
    finally:
        if con:
            con.close()


if __name__ == "__main__":
    init_db() # Ensure DB is initialized before running the app
    # Set debug=True for development. Disable in production.
    # In production, use a WSGI server like Gunicorn/Waitress.
    app.run(debug=True, host='127.0.0.1', port=5000)