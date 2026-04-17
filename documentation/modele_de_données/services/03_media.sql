-- ============================================================================
-- ███╗   ███╗███████╗██████╗ ██╗ █████╗
-- ████╗ ████║██╔════╝██╔══██╗██║██╔══██╗
-- ██╔████╔██║█████╗  ██║  ██║██║███████║
-- ██║╚██╔╝██║██╔══╝  ██║  ██║██║██╔══██║
-- ██║ ╚═╝ ██║███████╗██████╔╝██║██║  ██║
-- ╚═╝     ╚═╝╚══════╝╚═════╝ ╚═╝╚═╝  ╚═╝
-- SERVICE: MEDIA (Gestion des médias)
-- ============================================================================
-- Tables: media, albums, album_media
-- Dépendances externes: Aucune
-- Utilisé par: Tous les autres services
-- ============================================================================

-- Table centralisée des médias
CREATE TABLE media (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type media_type NOT NULL,
    url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500), -- URL de la vignette / couverture, utile pour documents et vidéos
    is_external_url BOOLEAN DEFAULT FALSE,
    size_bytes BIGINT,
    mime_type VARCHAR(100),
    width INT,
    height INT,
    duration_seconds INT,
    alt_text VARCHAR(255),
    credits VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_media_type ON media(type);

-- Albums (regroupement de médias)
CREATE TABLE albums (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    slug VARCHAR(300) UNIQUE NOT NULL,
    status publication_status DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_albums_slug ON albums(slug);

-- Relation albums <-> médias
CREATE TABLE album_media (
    album_id UUID REFERENCES albums(id) ON DELETE CASCADE,
    media_id UUID REFERENCES media(id) ON DELETE CASCADE,
    display_order INT DEFAULT 0,
    PRIMARY KEY (album_id, media_id)
);

COMMENT ON TABLE media IS '[MEDIA] Fichiers médias centralisés (images, vidéos, documents)';
COMMENT ON TABLE albums IS '[MEDIA] Albums regroupant des médias';

-- ============================================================================
-- FIN DU SERVICE MEDIA
-- ============================================================================
