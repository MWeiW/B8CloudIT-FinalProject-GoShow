# Booking Confirmation Handler

This folder contains a standalone serverless-style booking confirmation component for GoShow. It is separate from the Flask website and the notification microservice.

The handler builds a booking confirmation response from a booking event. It does not send real email and does not use an external email provider. It is deployed as an Azure Function at `https://goshow-booking-confirmation-wingwei8.azurewebsites.net/api/booking_confirmation`.

## Input

The main function is `handle(event, context=None)`. It accepts:

- a normal Python dictionary
- a JSON string
- a dictionary with a `body` field
- a `body` field that is either a JSON string or a dictionary

Expected booking fields:

- `customer_name`
- `customer_email`
- `concert_title`
- `tickets`

Missing fields use safe default values.

## Output

The handler returns an HTTP-style response with:

- `statusCode`
- `headers` with `Content-Type: application/json`
- `body` as a JSON string

The response body includes the confirmation status, customer details, concert title, ticket count, and a message.

## Test locally

Run this from the project root:

```bash
python serverless/booking_confirmation/handler.py
```

The local test reads `sample_event.json` and prints the response.
