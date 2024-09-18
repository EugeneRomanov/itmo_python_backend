import json
from math import factorial as math_factorial
from statistics import mean as calc_mean

# ASGI app function
async def app(scope, receive, send):
    if scope["type"] != "http":
        return

    method = scope["method"]
    path = scope["path"]

    if method == "GET" and path == "/factorial":
        await handle_factorial(scope, receive, send)
    elif method == "GET" and path.startswith("/fibonacci/"):
        await handle_fibonacci(scope, receive, send)
    elif method == "GET" and path == "/mean":
        await handle_mean(scope, receive, send)
    else:
        await send_404(send)

async def handle_factorial(scope, receive, send):
    query_string = scope.get('query_string', b'').decode('utf-8')
    query_params = dict(qc.split('=') for qc in query_string.split('&') if '=' in qc)

    if 'n' not in query_params:
        await send_422(send)
        return

    try:
        n = int(query_params['n'])
        if n < 0:
            await send_400(send)
            return
    except ValueError:
        await send_422(send)
        return

    result = math_factorial(n)
    await send_json(send, {"result": result})

async def handle_fibonacci(scope, receive, send):
    path_params = scope["path"].split("/")
    if len(path_params) != 3:
        await send_422(send)
        return

    # Handle the case where the parameter is not a digit
    param = path_params[2]
    if not param.isdigit() and not (param.startswith('-') and param[1:].isdigit()):
        await send_422(send)
        return

    try:
        n = int(param)
    except ValueError:
        await send_422(send)
        return

    if n < 0:
        await send_400(send)
        return

    result = fibonacci(n)
    await send_json(send, {"result": result})

async def handle_mean(scope, receive, send):
    query_string = scope.get('query_string', b'').decode('utf-8')
    body = await receive_body(receive)

    # Parse JSON from the body
    try:
        if body:
            numbers = json.loads(body)
        else:
            numbers = None
    except json.JSONDecodeError:
        numbers = None

    # If there is no data or the data is incorrect
    if numbers is None:
        await send_422(send)
        return

    # Check that numbers is a list
    if not isinstance(numbers, list) or not all(isinstance(x, (int, float)) for x in numbers):
        await send_422(send)
        return

    # If the list is empty
    if len(numbers) == 0:
        await send_400(send)
        return

    # Calculate the mean
    result = calc_mean(numbers)
    await send_json(send, {"result": result})

# Utility functions

async def receive_body(receive):
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body

def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

async def send_json(send, data, status=200):
    response = json.dumps(data).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [(b"content-type", b"application/json")],
    })
    await send({
        "type": "http.response.body",
        "body": response,
    })

async def send_400(send):
    await send_json(send, {"error": "Bad Request"}, status=400)

async def send_422(send):
    await send_json(send, {"error": "Unprocessable Entity"}, status=422)

async def send_404(send):
    await send_json(send, {"error": "Not Found"}, status=404)
