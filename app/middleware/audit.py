"""
Middleware d'audit automatique
==============================

Intercepte les requêtes d'écriture (POST, PUT, PATCH, DELETE) sur les endpoints
admin et auth pour créer automatiquement des entrées dans le journal d'audit.

Captures :
- L'action (create, update, delete, login, logout)
- La table concernée (déduite de l'URL)
- L'ID de l'enregistrement (extrait de l'URL)
- Les anciennes valeurs (SELECT avant modification)
- Les nouvelles valeurs (corps de la requête)
- L'adresse IP et le user agent du client
"""

import json
import logging
import re
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from sqlalchemy import select, text

from app.core.security import decode_token
from app.database import async_session_maker
from app.models.identity import AuditLog

logger = logging.getLogger(__name__)

# ============================================================================
# Mapping URL prefix → table_name en base de données
# ============================================================================
# Clé : segment d'URL après /api/admin/
# Valeur : nom de la table PostgreSQL

ROUTE_TO_TABLE: dict[str, str] = {
    "users": "users",
    "roles": "roles",
    "permissions": "permissions",
    "countries": "countries",
    "media": "media",
    "albums": "albums",
    "sectors": "sectors",
    "services": "services",
    "news": "news",
    "events": "events",
    "tags": "tags",
    "event-registrations": "event_registrations",
    "campuses": "campuses",
    "campus-team": "campus_team",
    "partners": "partners",
    "partnership-requests": "partnership_requests",
    "programs": "programs",
    "program-semesters": "program_semesters",
    "program-skills": "program_skills",
    "program-fields": "program_fields",
    "career-opportunities": "program_career_opportunities",
    "application-calls": "application_calls",
    "applications": "applications",
    "subscribers": "newsletter_subscribers",
    "campaigns": "newsletter_campaigns",
    "editorial": "editorial_contents",
    "projects": "projects",
}

# Routes à ignorer (lecture seule, dashboard, audit lui-même)
SKIP_PREFIXES = {
    "/api/admin/dashboard",
    "/api/admin/audit-logs",
}

# Mapping méthode HTTP → action d'audit
METHOD_TO_ACTION: dict[str, str] = {
    "POST": "create",
    "PUT": "update",
    "PATCH": "update",
    "DELETE": "delete",
}

# Regex UUID v4
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def _extract_user_id_from_token(request: Request) -> str | None:
    """Extrait le user_id du token JWT Bearer."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return payload.get("sub")
    return None


def _get_client_ip(request: Request) -> str | None:
    """Récupère l'IP du client (supporte les proxies X-Forwarded-For)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


def _parse_admin_route(path: str) -> tuple[str | None, str | None]:
    """
    Parse une URL admin pour extraire table_name et record_id.

    Exemples :
        /api/admin/news          → ("news", None)
        /api/admin/news/abc-123  → ("news", "abc-123")
        /api/admin/application-calls/abc-123/criteria → ("application_calls", "abc-123")

    Returns:
        (table_name, record_id) ou (None, None) si non reconnu.
    """
    # Retirer le préfixe /api/admin/
    prefix = "/api/admin/"
    if not path.startswith(prefix):
        return None, None

    remainder = path[len(prefix):]
    segments = remainder.strip("/").split("/")
    if not segments or not segments[0]:
        return None, None

    route_key = segments[0]
    table_name = ROUTE_TO_TABLE.get(route_key)
    if not table_name:
        return None, None

    # Chercher un UUID dans les segments suivants
    record_id = None
    if len(segments) > 1 and UUID_PATTERN.match(segments[1]):
        record_id = segments[1]

    return table_name, record_id


def _parse_auth_route(path: str, method: str) -> tuple[str, str | None]:
    """
    Parse une URL auth pour identifier login/logout.

    Returns:
        (action, None) ou (None, None) si pas pertinent.
    """
    if method == "POST" and path in ("/api/auth/login", "/api/auth/login/json"):
        return "login", None
    if method == "POST" and path == "/api/auth/logout":
        return "logout", None
    return None, None


async def _fetch_old_values(
    table_name: str, record_id: str
) -> dict | None:
    """Récupère les valeurs actuelles d'un enregistrement avant modification."""
    try:
        async with async_session_maker() as session:
            # Requête SQL brute pour récupérer toutes les colonnes en JSON
            result = await session.execute(
                text(
                    f"SELECT to_jsonb(t.*) FROM {table_name} t WHERE t.id = :id"  # noqa: S608
                ),
                {"id": record_id},
            )
            row = result.scalar_one_or_none()
            if row is not None:
                # to_jsonb retourne un dict directement via psycopg/asyncpg
                return dict(row) if not isinstance(row, dict) else row
    except Exception:
        logger.warning(
            "Impossible de récupérer les anciennes valeurs pour %s/%s",
            table_name,
            record_id,
            exc_info=True,
        )
    return None


async def _save_audit_log(
    user_id: str | None,
    action: str,
    table_name: str | None,
    record_id: str | None,
    old_values: dict | None,
    new_values: dict | None,
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    """Persiste une entrée d'audit dans une session dédiée."""
    try:
        async with async_session_maker() as session:
            log = AuditLog(
                id=str(uuid4()),
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_values=old_values,
                new_values=new_values,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            session.add(log)
            await session.commit()
    except Exception:
        logger.error(
            "Erreur lors de la sauvegarde du log d'audit: %s %s/%s",
            action,
            table_name,
            record_id,
            exc_info=True,
        )


def _sanitize_body(body: dict | None) -> dict | None:
    """Retire les champs sensibles du corps de requête avant de les stocker."""
    if not body:
        return body
    sensitive_keys = {"password", "password_hash", "token", "refresh_token", "secret"}
    return {k: "***" if k in sensitive_keys else v for k, v in body.items()}


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware qui enregistre automatiquement les opérations d'écriture
    dans le journal d'audit.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        method = request.method
        path = request.url.path

        # ----------------------------------------------------------------
        # Filtrage rapide : ignorer les lectures et les routes non concernées
        # ----------------------------------------------------------------
        if method in ("GET", "HEAD", "OPTIONS"):
            return await call_next(request)

        is_admin = path.startswith("/api/admin/")
        is_auth = path.startswith("/api/auth/")

        if not is_admin and not is_auth:
            return await call_next(request)

        # Ignorer les routes skip (dashboard, audit-logs)
        for skip in SKIP_PREFIXES:
            if path.startswith(skip):
                return await call_next(request)

        # ----------------------------------------------------------------
        # Déterminer l'action, la table et le record_id
        # ----------------------------------------------------------------
        action = None
        table_name = None
        record_id = None

        if is_auth:
            action, _ = _parse_auth_route(path, method)
            if not action:
                return await call_next(request)
        else:
            table_name, record_id = _parse_admin_route(path)
            if not table_name:
                return await call_next(request)
            action = METHOD_TO_ACTION.get(method)
            if not action:
                return await call_next(request)

        # ----------------------------------------------------------------
        # Capturer les métadonnées de la requête
        # ----------------------------------------------------------------
        user_id = _extract_user_id_from_token(request)
        ip_address = _get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        # Lire le corps de la requête (pour new_values)
        request_body = None
        if method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    request_body = json.loads(body_bytes)
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # ----------------------------------------------------------------
        # Capturer les anciennes valeurs avant la modification
        # ----------------------------------------------------------------
        old_values = None
        if action in ("update", "delete") and record_id:
            old_values = await _fetch_old_values(table_name, record_id)

        # ----------------------------------------------------------------
        # Exécuter la requête originale
        # ----------------------------------------------------------------
        response = await call_next(request)

        # ----------------------------------------------------------------
        # Enregistrer le log d'audit uniquement si la requête a réussi
        # ----------------------------------------------------------------
        if 200 <= response.status_code < 300:
            # Pour login, extraire le user_id depuis le corps de la requête
            if action == "login" and not user_id:
                user_id = await self._extract_login_user_id(request_body)

            await _save_audit_log(
                user_id=user_id,
                action=action,
                table_name=table_name,
                record_id=record_id,
                old_values=_sanitize_body(old_values),
                new_values=_sanitize_body(request_body),
                ip_address=ip_address,
                user_agent=user_agent,
            )

        return response

    async def _extract_login_user_id(self, body: dict | None) -> str | None:
        """Récupère le user_id depuis l'email fourni au login."""
        if not body:
            return None
        email = body.get("username") or body.get("email")
        if not email:
            return None
        try:
            from app.models.identity import User

            async with async_session_maker() as session:
                result = await session.execute(
                    select(User.id).where(
                        User.email == email.lower().strip()
                    )
                )
                user_id = result.scalar_one_or_none()
                return str(user_id) if user_id else None
        except Exception:
            logger.warning("Impossible de résoudre l'email pour le login audit")
            return None
