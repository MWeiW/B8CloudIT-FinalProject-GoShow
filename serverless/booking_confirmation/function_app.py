import azure.functions as func

from handler import handle


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="booking_confirmation", methods=["GET", "POST"])
def booking_confirmation(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "POST":
        try:
            booking_data = req.get_json()
        except ValueError:
            booking_data = {}
    else:
        booking_data = {
            "customer_name": req.params.get("customer_name", "Customer"),
            "customer_email": req.params.get(
                "customer_email",
                "not-provided@example.com",
            ),
            "concert_title": req.params.get(
                "concert_title",
                "your selected concert",
            ),
            "tickets": req.params.get("tickets", 1),
        }

    result = handle(booking_data)

    return func.HttpResponse(
        result["body"],
        status_code=result.get("statusCode", 200),
        mimetype="application/json",
    )
