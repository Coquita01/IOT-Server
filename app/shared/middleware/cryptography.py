from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json
from app.shared.services.cryptography.aes import create_aes_cryptography
from app.shared.services.cryptography.base import CryptoKey

excluded_paths = ["/docs", "/openapi.json"]
excluded_prefixes = ["/login/"]

crypto = create_aes_cryptography()


# Middleware de Descifrado (para las solicitudes entrantes)
class DecryptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in excluded_paths or any(
            request.url.path.startswith(prefix) for prefix in excluded_prefixes
        ):
            return await call_next(request)

        if request.method not in ["POST", "PUT", "PATCH"]:
            return await call_next(request)

        # token = request.headers.get("x-algo")  # Modificar esto
        # para el login
        key = CryptoKey(secret="me_tienes_que_cambiar_2026")
        if not key:
            return Response(content="Session not found or expired", status_code=401)

        body = await request.body()
        if not body:
            return await call_next(request)

        try:
            body_json = json.loads(body.decode())
            encrypted_body = body_json.get("pl")
            if not encrypted_body:
                raise Exception("Missing 'pl' field in request body")

            json_data = crypto.decrypt(encrypted_body, key)
            request._body = json.dumps(json_data).encode()
        except Exception as e:
            return Response(content=f"Decryption error: {str(e)}", status_code=400)

        return await call_next(request)


# Middleware de Cifrado (para las respuestas salientes)
class EncryptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if response.status_code >= 400:
            return response

        if request.url.path in excluded_paths or any(
            request.url.path.startswith(prefix) for prefix in excluded_prefixes
        ):
            return response

        # token = request.headers.get("x-algo")  # Modificar esto
        key = CryptoKey(secret="me_tienes_que_cambiar_2026")
        try:
            response_body = [chunk async for chunk in response.body_iterator]
            response_body = b"".join(response_body)

            if not response_body:
                return response

            json_response = json.loads(response_body.decode())

            final_response = crypto.encrypt(json_response, key).model_dump()

            return Response(
                content=json.dumps(final_response),
                status_code=response.status_code,
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            return Response(content=f"Encryption error: {str(e)}", status_code=500)
