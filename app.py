@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user['password'], password):
            user_data = {
                "id": user['id'],
                "email": user['email'],
                "name": user['name'],
                "company": user['company']
            }
            db.close()  # ← ДОБАВЛЕНО!
            return jsonify({"message": "Login successful", "user": user_data}), 200
        else:
            db.close()  # ← ДОБАВЛЕНО!
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        db.close()  # ← ДОБАВЛЕНО!
        return jsonify({"error": str(e)}), 500
