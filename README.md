<img width="1920" height="1080" alt="Screenshot (165)" src="https://github.com/user-attachments/assets/fe201929-eb31-4c72-8242-b77438cb0185" />
<img width="1920" height="1080" alt="Screenshot (164)" src="https://github.com/user-attachments/assets/42751ffb-f49d-4e33-ab20-6913ac771115" />
# 🚆 WOOK Train Ticket Booking System

A **full-stack train ticket booking platform** built with **Flask**, **SQLite**, and **Bootstrap**, seamlessly integrated with the official **Indian Railways API** for real-time train route and schedule data. This project simulates a working online ticketing system — complete with user authentication, PNR management, ticket generation, and booking history.

## 📌 Features

- 🔐 **User Authentication**: Secure registration and login with session management.
- 🚂 **Train Search by Number**: Get full train route details via Indian Railways API.
- 🧭 **Source-Destination Search**: Find all trains between two stations.
- 🎫 **Ticket Booking**: Book Sleeper/AC tickets with real-time quota logic and generate unique PNRs.
- 📄 **Downloadable PDF Tickets**: Professionally styled tickets using ReportLab.
- 📜 **PNR Status Check**: Lookup detailed booking information by PNR.
- 🕒 **Booking History**: View all past bookings for the logged-in user.
- 📍 **Live Location Simulation**: Track dummy coordinates and train status for a live feel.
- 🎨 **Modern UI**: Responsive, interactive interface using Bootstrap 5 and FontAwesome.

## 🧰 Tech Stack

| Layer        | Technology |
|--------------|------------|
| **Frontend** | HTML5, CSS3, Bootstrap 5, JavaScript |
| **Backend**  | Python (Flask), SQLite |
| **API**      | [data.gov.in](https://data.gov.in) Indian Railways Train Route API |
| **PDF**      | ReportLab |
| **Extras**   | Flask-CORS, UUID for PNRs |

## 🚀 Setup Instructions

1. **Clone the repo**:
   ```bash
   git clone https://github.com/eddyfdev/wook-train-booking.git
   cd wook-train-booking
   ```

2. **Install dependencies**:
   ```bash
   pip install Flask Flask-CORS requests reportlab
   ```

3. **Run the app**:
   ```bash
   python app.py
   ```

4. Open your browser and visit:  
   `http://127.0.0.1:5000`

## 🔒 Sample Credentials

Use the app by registering any username and password. No real train data is booked — this is a simulation.

## 📷 Screenshots

> ✅ Add actual snapshots here for Login, Search, Booking, PNR, PDF, etc.

## 🧠 Highlights

- **Real-time API Integration** for fetching live train routes.
- **Dynamic PNR system** using Python’s `uuid4`.
- **PDF Ticket Generator** using ReportLab — customizable, printable output.
- **Fully Responsive Interface** built with modern design principles.

## 💡 Inspiration

This project was created as part of a **college assignment** focused on building real-world, production-grade systems with public APIs. The goal was to simulate a **IRCTC-like booking platform** with educational purpose.

## 🛠️ Future Improvements

- Add **email notification** on booking.
- Extend to support **multi-user admin dashboard**.
- Add **train availability status** from a more granular API.
- Implement **payment gateway simulation**.

## 📄 License

MIT License – feel free to fork, modify, and deploy for learning purposes!

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

## 👨‍💻 Author

Developed by **Eddy F.**  
*Final-year MCA student | Full-stack developer | AI Enthusiast*

> Want a similar project? Let's connect on [LinkedIn](https://linkedin.com/in/yourprofile)
