from flask import Flask, jsonify, request


app = Flask(__name__)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "notification-service"})


@app.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON request"}), 400

    customer_name = str(data.get("customer_name") or "Customer").strip()
    customer_email = str(data.get("customer_email") or "not provided").strip()
    concert_title = str(data.get("concert_title") or "your concert").strip()
    tickets = data.get("tickets", 1)

    message = (
        f"Booking confirmation simulated for {customer_name}: "
        f"{tickets} ticket(s) for {concert_title}."
    )
    print(f"Simulated booking confirmation for {tickets} ticket(s) to {concert_title}.")

    return jsonify(
        {
            "status": "simulated",
            "recipient": customer_email,
            "message": message,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

