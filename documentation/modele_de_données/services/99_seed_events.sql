-- ============================================================================
-- ███████╗███████╗███████╗██████╗     ███████╗██╗   ██╗███████╗███╗   ██╗████████╗███████╗
-- ██╔════╝██╔════╝██╔════╝██╔══██╗    ██╔════╝██║   ██║██╔════╝████╗  ██║╚══██╔══╝██╔════╝
-- ███████╗█████╗  █████╗  ██║  ██║    █████╗  ██║   ██║█████╗  ██╔██╗ ██║   ██║   ███████╗
-- ╚════██║██╔══╝  ██╔══╝  ██║  ██║    ██╔══╝  ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║   ██║   ╚════██║
-- ███████║███████╗███████╗██████╔╝    ███████╗ ╚████╔╝ ███████╗██║ ╚████║   ██║   ███████║
-- ╚══════╝╚══════╝╚══════╝╚═════╝     ╚══════╝  ╚═══╝  ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝
-- SEED DATA: Événements et Inscriptions (données de test)
-- ============================================================================
-- Ce fichier contient des données de test pour les événements et inscriptions.
-- Maximum 10 inscriptions comme demandé.
-- ============================================================================

-- ============================================================================
-- [CONTENT] Événements de test
-- ============================================================================
INSERT INTO events (id, title, slug, description, type, start_date, end_date, venue, city, registration_required, max_attendees, status, created_at) VALUES
-- Événement 1 : Conférence passée (pour tester le statut "présent")
(
    '11111111-1111-1111-1111-111111111101',
    'Conférence inaugurale : L''avenir de la Francophonie en Afrique',
    'conference-inaugurale-francophonie-2025',
    'Une conférence réunissant des experts et décideurs autour des enjeux de la Francophonie pour le développement africain.',
    'conference',
    '2025-01-15 09:00:00+02',
    '2025-01-15 17:00:00+02',
    'Auditorium principal',
    'Alexandrie',
    true,
    200,
    'published',
    '2024-12-01 10:00:00+02'
),
-- Événement 2 : Atelier à venir
(
    '11111111-1111-1111-1111-111111111102',
    'Atelier de formation en leadership et gouvernance',
    'atelier-leadership-gouvernance-2026',
    'Formation intensive de 3 jours sur les techniques de leadership et les bonnes pratiques de gouvernance.',
    'workshop',
    '2026-02-10 09:00:00+02',
    '2026-02-12 17:00:00+02',
    'Salle de conférences B',
    'Alexandrie',
    true,
    30,
    'published',
    '2025-12-15 10:00:00+02'
),
-- Événement 3 : Cérémonie à venir
(
    '11111111-1111-1111-1111-111111111103',
    'Cérémonie de remise des diplômes 2025',
    'ceremonie-diplomes-2025',
    'Cérémonie officielle de remise des diplômes aux lauréats de la promotion 2025.',
    'ceremony',
    '2026-02-28 14:00:00+02',
    '2026-02-28 18:00:00+02',
    'Grand Amphithéâtre',
    'Alexandrie',
    true,
    500,
    'published',
    '2025-11-01 08:00:00+02'
)
ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    slug = EXCLUDED.slug,
    description = EXCLUDED.description,
    type = EXCLUDED.type,
    start_date = EXCLUDED.start_date,
    end_date = EXCLUDED.end_date,
    venue = EXCLUDED.venue,
    city = EXCLUDED.city,
    registration_required = EXCLUDED.registration_required,
    max_attendees = EXCLUDED.max_attendees,
    status = EXCLUDED.status;

-- ============================================================================
-- [CONTENT] Inscriptions aux événements (10 inscriptions)
-- ============================================================================
INSERT INTO event_registrations (id, event_id, last_name, first_name, email, phone, organization, status, registered_at) VALUES
-- Conférence inaugurale (5 inscriptions - événement passé)
(
    '22222222-2222-2222-2222-222222222201',
    '11111111-1111-1111-1111-111111111101',
    'Diallo',
    'Fatou',
    'fatou.diallo@gouv.sn',
    '+221 77 123 45 67',
    'Ministère de l''Éducation nationale - Sénégal',
    'attended',
    '2024-12-05 10:30:00+02'
),
(
    '22222222-2222-2222-2222-222222222202',
    '11111111-1111-1111-1111-111111111101',
    'Traoré',
    'Amadou',
    'amadou.traore@univ-bamako.ml',
    '+223 70 234 56 78',
    'Université des Sciences de Bamako',
    'attended',
    '2024-12-06 14:15:00+02'
),
(
    '22222222-2222-2222-2222-222222222203',
    '11111111-1111-1111-1111-111111111101',
    'Kouassi',
    'Marie-Claire',
    'marie.kouassi@cires.ci',
    '+225 07 345 67 89',
    'Centre ivoirien de recherches économiques et sociales',
    'confirmed',
    '2024-12-10 11:00:00+02'
),
(
    '22222222-2222-2222-2222-222222222204',
    '11111111-1111-1111-1111-111111111101',
    'Nzamba',
    'Jean-Pierre',
    'jp.nzamba@ong-developpement.org',
    '+241 66 456 78 90',
    'ONG Développement Durable Gabon',
    'cancelled',
    '2024-12-08 09:45:00+02'
),
(
    '22222222-2222-2222-2222-222222222205',
    '11111111-1111-1111-1111-111111111101',
    'Ben Ali',
    'Aïcha',
    'aicha.benali@isit.tn',
    '+216 20 567 89 01',
    'Institut supérieur des technologies de Tunis',
    'attended',
    '2024-12-12 16:30:00+02'
),

-- Atelier leadership (3 inscriptions - événement à venir)
(
    '22222222-2222-2222-2222-222222222206',
    '11111111-1111-1111-1111-111111111102',
    'Konaté',
    'Ibrahim',
    'ibrahim.konate@finances.bf',
    '+226 70 678 90 12',
    'Ministère des Finances - Burkina Faso',
    'confirmed',
    '2025-12-20 10:00:00+02'
),
(
    '22222222-2222-2222-2222-222222222207',
    '11111111-1111-1111-1111-111111111102',
    'Moukoko',
    'Célestine',
    'celestine.moukoko@beac.ga',
    '+241 77 789 01 23',
    'Banque des États de l''Afrique Centrale',
    'registered',
    '2025-12-22 09:30:00+02'
),
(
    '22222222-2222-2222-2222-222222222208',
    '11111111-1111-1111-1111-111111111102',
    'Camara',
    'Moussa',
    'moussa.camara@ugb.edu.sn',
    '+221 76 890 12 34',
    'Université Gaston Berger de Saint-Louis',
    'confirmed',
    '2025-12-25 11:45:00+02'
),

-- Cérémonie diplômes (2 inscriptions - événement à venir)
(
    '22222222-2222-2222-2222-222222222209',
    '11111111-1111-1111-1111-111111111103',
    'Ouédraogo',
    'Pascaline',
    'pascaline.ouedraogo@gmail.com',
    '+226 78 901 23 45',
    'Diplômée 2025 - Master Gouvernance',
    'confirmed',
    '2025-11-05 08:00:00+02'
),
(
    '22222222-2222-2222-2222-222222222210',
    '11111111-1111-1111-1111-111111111103',
    'Sow',
    'Abdoulaye',
    'abdoulaye.sow@famille.sn',
    '+221 77 012 34 56',
    'Famille du diplômé',
    'registered',
    '2025-11-10 14:20:00+02'
)
ON CONFLICT (id) DO UPDATE SET
    event_id = EXCLUDED.event_id,
    last_name = EXCLUDED.last_name,
    first_name = EXCLUDED.first_name,
    email = EXCLUDED.email,
    phone = EXCLUDED.phone,
    organization = EXCLUDED.organization,
    status = EXCLUDED.status,
    registered_at = EXCLUDED.registered_at;

-- ============================================================================
-- FIN DU FICHIER 99_seed_events.sql
-- ============================================================================
