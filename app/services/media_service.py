"""
Service Media
==============

Logique métier pour la gestion des médias (upload, albums).
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import ConflictException, NotFoundException, ValidationException
from app.models.base import MediaType, PublicationStatus
from app.models.media import Album, AlbumMedia, Media


# Mapping des extensions vers les types de médias
EXTENSION_TO_MEDIA_TYPE: dict[str, MediaType] = {
    # Images
    ".jpg": MediaType.IMAGE,
    ".jpeg": MediaType.IMAGE,
    ".png": MediaType.IMAGE,
    ".gif": MediaType.IMAGE,
    ".webp": MediaType.IMAGE,
    ".svg": MediaType.IMAGE,
    ".bmp": MediaType.IMAGE,
    ".ico": MediaType.IMAGE,
    # Vidéos
    ".mp4": MediaType.VIDEO,
    ".webm": MediaType.VIDEO,
    ".avi": MediaType.VIDEO,
    ".mov": MediaType.VIDEO,
    ".mkv": MediaType.VIDEO,
    ".wmv": MediaType.VIDEO,
    # Audio
    ".mp3": MediaType.AUDIO,
    ".wav": MediaType.AUDIO,
    ".ogg": MediaType.AUDIO,
    ".flac": MediaType.AUDIO,
    ".aac": MediaType.AUDIO,
    # Documents
    ".pdf": MediaType.DOCUMENT,
    ".doc": MediaType.DOCUMENT,
    ".docx": MediaType.DOCUMENT,
    ".xls": MediaType.DOCUMENT,
    ".xlsx": MediaType.DOCUMENT,
    ".ppt": MediaType.DOCUMENT,
    ".pptx": MediaType.DOCUMENT,
    ".txt": MediaType.DOCUMENT,
    ".csv": MediaType.DOCUMENT,
    ".zip": MediaType.DOCUMENT,
    ".rar": MediaType.DOCUMENT,
}

# Types MIME autorisés
ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/bmp",
    "image/x-icon",
    # Vidéos
    "video/mp4",
    "video/webm",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-matroska",
    "video/x-ms-wmv",
    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",
    "audio/flac",
    "audio/aac",
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "application/zip",
    "application/x-rar-compressed",
}

# Taille maximale par défaut (50 Mo)
MAX_FILE_SIZE = 50 * 1024 * 1024


class MediaService:
    """Service pour la gestion des médias."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.storage_path = Path(settings.storage_path)

    def _ensure_storage_dir(self, folder: str = "general") -> Path:
        """Crée le répertoire de stockage si nécessaire."""
        upload_dir = self.storage_path / folder
        upload_dir.mkdir(parents=True, exist_ok=True)
        return upload_dir

    def _get_media_type_from_extension(self, filename: str) -> MediaType:
        """Détermine le type de média à partir de l'extension."""
        ext = Path(filename).suffix.lower()
        return EXTENSION_TO_MEDIA_TYPE.get(ext, MediaType.DOCUMENT)

    def _generate_unique_filename(self, original_filename: str) -> str:
        """Génère un nom de fichier unique."""
        ext = Path(original_filename).suffix.lower()
        unique_id = str(uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(c for c in Path(original_filename).stem if c.isalnum() or c in "-_")[:50]
        return f"{timestamp}_{safe_name}_{unique_id}{ext}"

    # =========================================================================
    # MEDIA
    # =========================================================================

    async def get_media_list(
        self,
        search: str | None = None,
        media_type: MediaType | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> select:
        """
        Construit une requête pour lister les médias.

        Args:
            search: Recherche sur nom ou description.
            media_type: Filtrer par type de média.
            date_from: Date de début (upload).
            date_to: Date de fin (upload).
            sort_by: Champ de tri (created_at, name, size_bytes).
            sort_order: Ordre de tri (asc, desc).

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Media)

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Media.name.ilike(search_filter),
                    Media.description.ilike(search_filter),
                    Media.alt_text.ilike(search_filter),
                )
            )

        if media_type:
            query = query.where(Media.type == media_type)

        if date_from:
            query = query.where(Media.created_at >= date_from)

        if date_to:
            query = query.where(Media.created_at <= date_to)

        # Tri
        sort_column = getattr(Media, sort_by, Media.created_at)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        return query

    async def get_media_by_id(self, media_id: str) -> Media | None:
        """Récupère un média par son ID."""
        result = await self.db.execute(
            select(Media).where(Media.id == media_id)
        )
        return result.scalar_one_or_none()

    async def upload_file(
        self,
        file: UploadFile,
        folder: str = "general",
        alt_text: str | None = None,
        credits: str | None = None,
    ) -> Media:
        """
        Upload un fichier et crée l'entrée média correspondante.

        Args:
            file: Fichier uploadé.
            folder: Dossier de destination.
            alt_text: Texte alternatif.
            credits: Crédits.

        Returns:
            Média créé.

        Raises:
            ValidationException: Si le fichier n'est pas valide.
        """
        # Vérifier le type MIME
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                f"Type de fichier non autorisé: {file.content_type}"
            )

        # Lire le contenu pour vérifier la taille
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ValidationException(
                f"Fichier trop volumineux. Maximum: {MAX_FILE_SIZE // (1024*1024)} Mo"
            )

        # Générer un nom unique
        original_filename = file.filename or "unnamed"
        unique_filename = self._generate_unique_filename(original_filename)

        # Créer le répertoire et sauvegarder le fichier
        upload_dir = self._ensure_storage_dir(folder)
        file_path = upload_dir / unique_filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Déterminer le type de média
        media_type = self._get_media_type_from_extension(original_filename)

        # Créer l'entrée en base
        media = Media(
            id=str(uuid4()),
            name=original_filename,
            type=media_type,
            url=f"/uploads/{folder}/{unique_filename}",
            is_external_url=False,
            size_bytes=len(content),
            mime_type=file.content_type,
            alt_text=alt_text,
            credits=credits,
        )

        # TODO: Extraire les dimensions pour les images/vidéos avec Pillow

        self.db.add(media)
        await self.db.flush()
        return media

    async def upload_multiple_files(
        self,
        files: list[UploadFile],
        folder: str = "general",
    ) -> list[Media]:
        """
        Upload plusieurs fichiers.

        Args:
            files: Liste des fichiers.
            folder: Dossier de destination.

        Returns:
            Liste des médias créés.
        """
        results = []
        for file in files:
            try:
                media = await self.upload_file(file, folder)
                results.append(media)
            except ValidationException:
                # Ignorer les fichiers invalides dans un upload multiple
                continue
        return results

    async def create_external_media(
        self,
        name: str,
        url: str,
        media_type: MediaType,
        **kwargs,
    ) -> Media:
        """
        Crée une entrée pour un média externe (URL).

        Args:
            name: Nom du média.
            url: URL externe.
            media_type: Type de média.
            **kwargs: Autres champs optionnels.

        Returns:
            Média créé.
        """
        media = Media(
            id=str(uuid4()),
            name=name,
            type=media_type,
            url=url,
            is_external_url=True,
            **kwargs,
        )
        self.db.add(media)
        await self.db.flush()
        return media

    async def update_media(self, media_id: str, **kwargs) -> Media:
        """
        Met à jour un média.

        Args:
            media_id: ID du média.
            **kwargs: Champs à mettre à jour.

        Returns:
            Média mis à jour.

        Raises:
            NotFoundException: Si le média n'existe pas.
        """
        media = await self.get_media_by_id(media_id)
        if not media:
            raise NotFoundException("Média non trouvé")

        await self.db.execute(
            update(Media).where(Media.id == media_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_media_by_id(media_id)

    async def delete_media(self, media_id: str) -> None:
        """
        Supprime un média.

        Args:
            media_id: ID du média.

        Raises:
            NotFoundException: Si le média n'existe pas.
        """
        media = await self.get_media_by_id(media_id)
        if not media:
            raise NotFoundException("Média non trouvé")

        # Supprimer le fichier physique si local
        if not media.is_external_url and media.url.startswith("/uploads/"):
            file_path = self.storage_path.parent / media.url.lstrip("/")
            if file_path.exists():
                file_path.unlink()

        await self.db.execute(delete(Media).where(Media.id == media_id))

    async def bulk_delete_media(self, media_ids: list[str]) -> int:
        """
        Supprime plusieurs médias.

        Args:
            media_ids: Liste des IDs.

        Returns:
            Nombre de médias supprimés.
        """
        count = 0
        for media_id in media_ids:
            try:
                await self.delete_media(media_id)
                count += 1
            except NotFoundException:
                continue
        return count

    async def get_media_statistics(self) -> dict:
        """Récupère les statistiques des médias."""
        # Total par type
        types_result = await self.db.execute(
            select(Media.type, func.count(Media.id))
            .group_by(Media.type)
        )
        by_type = {t.value: c for t, c in types_result.all()}

        # Total
        total_result = await self.db.execute(select(func.count(Media.id)))
        total = total_result.scalar() or 0

        # Taille totale
        size_result = await self.db.execute(
            select(func.sum(Media.size_bytes))
            .where(Media.size_bytes.isnot(None))
        )
        total_size = size_result.scalar() or 0

        return {
            "total": total,
            "by_type": by_type,
            "total_size_bytes": total_size,
        }

    # =========================================================================
    # ALBUMS
    # =========================================================================

    async def get_albums(
        self,
        search: str | None = None,
        status: PublicationStatus | None = None,
    ) -> select:
        """
        Construit une requête pour lister les albums.

        Args:
            search: Recherche sur titre ou description.
            status: Filtrer par statut.

        Returns:
            Requête SQLAlchemy Select.
        """
        query = select(Album).options(selectinload(Album.media_items))

        if search:
            search_filter = f"%{search}%"
            query = query.where(
                or_(
                    Album.title.ilike(search_filter),
                    Album.description.ilike(search_filter),
                )
            )

        if status:
            query = query.where(Album.status == status)

        return query

    async def get_album_by_id(self, album_id: str) -> Album | None:
        """Récupère un album par son ID."""
        result = await self.db.execute(
            select(Album)
            .options(selectinload(Album.media_items))
            .where(Album.id == album_id)
        )
        return result.scalar_one_or_none()

    async def create_album(
        self,
        title: str,
        description: str | None = None,
        status: PublicationStatus = PublicationStatus.DRAFT,
    ) -> Album:
        """
        Crée un nouvel album.

        Args:
            title: Titre de l'album.
            description: Description.
            status: Statut de publication.

        Returns:
            Album créé.
        """
        album = Album(
            id=str(uuid4()),
            title=title,
            description=description,
            status=status,
        )
        self.db.add(album)
        await self.db.flush()
        return album

    async def update_album(self, album_id: str, **kwargs) -> Album:
        """
        Met à jour un album.

        Args:
            album_id: ID de l'album.
            **kwargs: Champs à mettre à jour.

        Returns:
            Album mis à jour.

        Raises:
            NotFoundException: Si l'album n'existe pas.
        """
        album = await self.get_album_by_id(album_id)
        if not album:
            raise NotFoundException("Album non trouvé")

        await self.db.execute(
            update(Album).where(Album.id == album_id).values(**kwargs)
        )
        await self.db.flush()
        return await self.get_album_by_id(album_id)

    async def delete_album(self, album_id: str) -> None:
        """
        Supprime un album.

        Args:
            album_id: ID de l'album.

        Raises:
            NotFoundException: Si l'album n'existe pas.
        """
        album = await self.get_album_by_id(album_id)
        if not album:
            raise NotFoundException("Album non trouvé")

        await self.db.execute(delete(Album).where(Album.id == album_id))

    async def add_media_to_album(
        self, album_id: str, media_ids: list[str]
    ) -> Album:
        """
        Ajoute des médias à un album.

        Args:
            album_id: ID de l'album.
            media_ids: Liste des IDs médias.

        Returns:
            Album mis à jour.

        Raises:
            NotFoundException: Si l'album ou un média n'existe pas.
        """
        album = await self.get_album_by_id(album_id)
        if not album:
            raise NotFoundException("Album non trouvé")

        # Récupérer l'ordre actuel maximum
        result = await self.db.execute(
            select(func.max(AlbumMedia.display_order))
            .where(AlbumMedia.album_id == album_id)
        )
        max_order = result.scalar() or 0

        for i, media_id in enumerate(media_ids):
            media = await self.get_media_by_id(media_id)
            if not media:
                raise NotFoundException(f"Média {media_id} non trouvé")

            # Vérifier si déjà dans l'album
            existing = await self.db.execute(
                select(AlbumMedia).where(
                    AlbumMedia.album_id == album_id,
                    AlbumMedia.media_id == media_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            album_media = AlbumMedia(
                album_id=album_id,
                media_id=media_id,
                display_order=max_order + i + 1,
            )
            self.db.add(album_media)

        await self.db.flush()
        return await self.get_album_by_id(album_id)

    async def remove_media_from_album(
        self, album_id: str, media_id: str
    ) -> Album:
        """
        Retire un média d'un album.

        Args:
            album_id: ID de l'album.
            media_id: ID du média.

        Returns:
            Album mis à jour.

        Raises:
            NotFoundException: Si l'album n'existe pas.
        """
        album = await self.get_album_by_id(album_id)
        if not album:
            raise NotFoundException("Album non trouvé")

        await self.db.execute(
            delete(AlbumMedia).where(
                AlbumMedia.album_id == album_id,
                AlbumMedia.media_id == media_id,
            )
        )
        await self.db.flush()
        return await self.get_album_by_id(album_id)

    async def reorder_album_media(
        self, album_id: str, media_order: list[str]
    ) -> Album:
        """
        Réordonne les médias d'un album.

        Args:
            album_id: ID de l'album.
            media_order: Liste des IDs médias dans le nouvel ordre.

        Returns:
            Album mis à jour.

        Raises:
            NotFoundException: Si l'album n'existe pas.
        """
        album = await self.get_album_by_id(album_id)
        if not album:
            raise NotFoundException("Album non trouvé")

        for i, media_id in enumerate(media_order):
            await self.db.execute(
                update(AlbumMedia)
                .where(
                    AlbumMedia.album_id == album_id,
                    AlbumMedia.media_id == media_id,
                )
                .values(display_order=i)
            )

        await self.db.flush()
        return await self.get_album_by_id(album_id)
