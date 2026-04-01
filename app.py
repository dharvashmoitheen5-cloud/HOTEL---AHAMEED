from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
from dotenv import load_dotenv
from flask_mail import Mail, Message
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "luxury_secret_key"

# ---------------- OPENAI CLIENT ----------------
api_key = os.getenv("OPENAI_API_KEY")
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("ERROR: OPENAI_API_KEY not found in .env file")

client_ai = OpenAI(api_key=api_key)

# ---------------- MAIL CONFIG ----------------
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "botsalman78@gmail.com"
app.config["MAIL_PASSWORD"] = "aqct ojpm bwqk igxg"

mail = Mail(app)

# ---------------- MONGODB CONNECTION ----------------
client = MongoClient("mongodb://localhost:27017/")
db = client["luxury_restaurant"]

# Collections
users_collection = db["users"]
bookings_collection = db["bookings"]
reviews_collection = db["reviews"]
menu_collection = db["menu"]

# ---------------- HOME ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- MENU ----------------
@app.route("/menu")
def menu():
    return render_template("menu.html")

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "role": "user"
        })

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = users_collection.find_one({"email": email})

        if user and check_password_hash(user["password"], password):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            session["role"] = user.get("role", "user")

            flash("Login successful!", "success")

            if session["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("home"))
        else:
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))

# ---------------- BOOKING ----------------
@app.route("/booking", methods=["GET", "POST"])
def booking():
    if "user_id" not in session:
        flash("Please login to book a table.", "error")
        return redirect(url_for("login"))

    # Table limits
    table_limits = {
        "Couple Table": 10,
        "Family Table": 8,
        "VIP Table": 5
    }

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        date = request.form["date"]
        time = request.form["time"]
        guests = request.form["guests"]
        table_type = request.form["table_type"]
        special_request = request.form["special_request"]

        # Count already booked tables for same date + time + table type
        existing_bookings = bookings_collection.count_documents({
            "date": date,
            "time": time,
            "table_type": table_type,
            "status": "Confirmed"
        })

        max_tables = table_limits.get(table_type, 0)

        if existing_bookings >= max_tables:
            flash(f"Sorry, no {table_type} available for {date} at {time}. Please choose another slot.", "error")
            return redirect(url_for("booking"))

        bookings_collection.insert_one({
            "user_id": session["user_id"],
            "name": name,
            "email": email,
            "phone": phone,
            "date": date,
            "time": time,
            "guests": guests,
            "table_type": table_type,
            "special_request": special_request,
            "status": "Confirmed"
        })

        # ---------------- SEND EMAIL ----------------
        try:
            msg = Message(
                subject="Luxury Restaurant - Booking Confirmation",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = f"""
Hello {name},

Your table has been booked successfully at Luxury Restaurant.

Booking Details:
Date: {date}
Time: {time}
Guests: {guests}
Table Type: {table_type}
Special Request: {special_request}

We look forward to serving you.

Thank you,
Luxury Restaurant
            """

            mail.send(msg)

        except Exception as e:
            print("MAIL ERROR:", e)

        flash("Table booked successfully! Confirmation email sent.", "success")
        return redirect(url_for("booking_history"))

    return render_template("booking.html")

# ---------------- BOOKING HISTORY ----------------
@app.route("/history")
def booking_history():
    if "user_id" not in session:
        flash("Please login first.", "error")
        return redirect(url_for("login"))

    user_bookings = list(bookings_collection.find({"user_id": session["user_id"]}))
    return render_template("history.html", bookings=user_bookings)

# ---------------- REVIEWS ----------------
@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    if request.method == "POST":
        if "user_id" not in session:
            flash("Please login to submit a review.", "error")
            return redirect(url_for("login"))

        rating = request.form["rating"]
        message = request.form["message"]

        reviews_collection.insert_one({
            "user_id": session["user_id"],
            "name": session["user_name"],
            "rating": rating,
            "message": message
        })

        flash("Review submitted successfully!", "success")
        return redirect(url_for("reviews"))

    all_reviews = list(reviews_collection.find().sort("_id", -1))
    return render_template("reviews.html", reviews=all_reviews)

# ---------------- HELP ----------------
@app.route("/help")
def help_page():
    return render_template("help.html")

# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin")
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        flash("Access denied. Admins only.", "error")
        return redirect(url_for("login"))

    all_users = list(users_collection.find())
    all_bookings = list(bookings_collection.find().sort("_id", -1))
    all_reviews = list(reviews_collection.find().sort("_id", -1))

    total_users = users_collection.count_documents({})
    total_bookings = bookings_collection.count_documents({})
    total_reviews = reviews_collection.count_documents({})

    return render_template(
        "admin_dashboard.html",
        users=all_users,
        bookings=all_bookings,
        reviews=all_reviews,
        total_users=total_users,
        total_bookings=total_bookings,
        total_reviews=total_reviews
    )

# ---------------- AI CHATBOT ----------------
@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_message = request.json.get("message", "").strip()
    language = request.json.get("language", "English")

    if not user_message:
        return jsonify({"reply": "Please type a message."})

    def fallback_bot(msg, lang):
        msg = msg.lower()

        if lang == "Tamil":
            if "hello" in msg or "hi" in msg:
                return "வணக்கம் 👋 Luxury Restaurant-க்கு வரவேற்கிறோம்! எப்படி உதவலாம்?"
            elif "menu" in msg:
                return "எங்கள் மெனுவில் Chicken Biryani, Grilled Chicken, Shawarma Plate, BBQ Wings மற்றும் Dessert உள்ளன 🍽️"
            elif "booking" in msg or "book" in msg:
                return "நீங்கள் Booking page மூலம் table reserve செய்யலாம் 📅"
            elif "timing" in msg or "open" in msg:
                return "நாங்கள் தினமும் காலை 11:00 முதல் இரவு 11:00 வரை திறந்திருப்போம் 🕒"
            else:
                return "நான் உங்கள் Luxury Restaurant உதவியாளர் 🤖 Menu, booking, timings பற்றி கேளுங்கள்!"

        elif lang == "Arabic":
            if "hello" in msg or "hi" in msg:
                return "مرحباً 👋 أهلاً بك في Luxury Restaurant! كيف يمكنني مساعدتك؟"
            elif "menu" in msg:
                return "لدينا في القائمة Chicken Biryani و Grilled Chicken و Shawarma Plate و BBQ Wings والحلويات 🍽️"
            elif "booking" in msg or "book" in msg:
                return "يمكنك حجز طاولة من صفحة الحجز 📅"
            elif "timing" in msg or "open" in msg:
                return "نحن مفتوحون يومياً من 11:00 صباحاً حتى 11:00 مساءً 🕒"
            else:
                return "أنا مساعد مطعمك الذكي 🤖 اسألني عن القائمة أو الحجز أو المواعيد!"

        elif lang == "Hindi":
            if "hello" in msg or "hi" in msg:
                return "नमस्ते 👋 Luxury Restaurant में आपका स्वागत है! मैं आपकी कैसे मदद कर सकता हूँ?"
            elif "menu" in msg:
                return "हमारे मेनू में Chicken Biryani, Grilled Chicken, Shawarma Plate, BBQ Wings और Dessert शामिल हैं 🍽️"
            elif "booking" in msg or "book" in msg:
                return "आप Booking page से टेबल बुक कर सकते हैं 📅"
            elif "timing" in msg or "open" in msg:
                return "हम रोज़ाना सुबह 11:00 बजे से रात 11:00 बजे तक खुले रहते हैं 🕒"
            else:
                return "मैं आपका Luxury Restaurant सहायक हूँ 🤖 Menu, booking और timings के बारे में पूछें!"

        else:
            if "hello" in msg or "hi" in msg:
                return "Hello 👋 Welcome to Luxury Restaurant! How can I help you today?"
            elif "menu" in msg:
                return "Our menu includes Chicken Biryani, Grilled Chicken, Shawarma Plate, BBQ Wings, Fresh Lime, and Chocolate Dessert 🍽️"
            elif "booking" in msg or "book" in msg:
                return "You can reserve your table from the Booking page 📅"
            elif "timing" in msg or "open" in msg:
                return "We are open daily from 11:00 AM to 11:00 PM 🕒"
            else:
                return "I'm your Luxury Restaurant assistant 🤖 Ask me about menu, booking, timings, or specials!"

    try:
        if api_key:
            response = client_ai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""
You are a smart AI assistant for a luxury restaurant in Chennai.

Your job is to help customers with:
- menu suggestions
- booking guidance
- restaurant timings
- vegetarian/non-veg options
- today's specials
- desserts
- reviews/help
- location/contact

Rules:
- Reply in {language}
- Be friendly, short, and helpful
- Keep answers simple and restaurant-related
- Sound premium and professional
                        """
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                temperature=0.7,
                max_tokens=180
            )

            reply = response.choices[0].message.content.strip()
            return jsonify({"reply": reply})

        else:
            return jsonify({"reply": fallback_bot(user_message, language)})

    except Exception as e:
        print("AI ERROR:", e)
        return jsonify({"reply": fallback_bot(user_message, language)})

if __name__ == "__main__":
    app.run(debug=True)