-- ============================================================================
-- ██╗   ██╗██╗███████╗██╗    ██╗███████╗
-- ██║   ██║██║██╔════╝██║    ██║██╔════╝
-- ██║   ██║██║█████╗  ██║ █╗ ██║███████╗
-- ╚██╗ ██╔╝██║██╔══╝  ██║███╗██║╚════██║
--  ╚████╔╝ ██║███████╗╚███╔███╔╝███████║
--   ╚═══╝  ╚═╝╚══════╝ ╚══╝╚══╝ ╚══════╝
-- VUES UTILES
-- ============================================================================
-- Note: Ces vues devront être adaptées en microservices car elles font
-- des jointures inter-services. En microservices, utiliser des API calls.
-- ============================================================================

-- ============================================================================
-- Vue des formations avec leurs campus (nécessite jointure ACADEMIC + CAMPUS)
-- En microservices: Appel API pour récupérer les noms des campus
-- ============================================================================
CREATE VIEW v_programs_overview AS
SELECT
    p.*,
    ARRAY_AGG(DISTINCT pc.campus_external_id) FILTER (WHERE pc.campus_external_id IS NOT NULL) as campus_ids
FROM programs p
LEFT JOIN program_campuses pc ON p.id = pc.program_id
GROUP BY p.id;

-- ============================================================================
-- Vue des événements à venir (SERVICE: CONTENT uniquement)
-- ============================================================================
CREATE VIEW v_upcoming_events AS
SELECT *
FROM events
WHERE status = 'published'
AND start_date >= NOW()
ORDER BY start_date ASC;

-- ============================================================================
-- Vue des actualités publiées (SERVICE: CONTENT uniquement)
-- ============================================================================
CREATE VIEW v_published_news AS
SELECT *
FROM news
WHERE status = 'published'
AND (visible_from IS NULL OR visible_from <= NOW())
ORDER BY published_at DESC;

-- ============================================================================
-- Vue statistiques des candidatures par appel (SERVICE: APPLICATION uniquement)
-- ============================================================================
CREATE VIEW v_application_statistics AS
SELECT
    ac.id as call_id,
    ac.title as call_title,
    COUNT(a.id) as total_applications,
    COUNT(CASE WHEN a.status = 'submitted' THEN 1 END) as submitted,
    COUNT(CASE WHEN a.status = 'under_review' THEN 1 END) as under_review,
    COUNT(CASE WHEN a.status = 'accepted' THEN 1 END) as accepted,
    COUNT(CASE WHEN a.status = 'rejected' THEN 1 END) as rejected,
    COUNT(CASE WHEN a.status = 'waitlisted' THEN 1 END) as waitlisted
FROM application_calls ac
LEFT JOIN applications a ON ac.id = a.call_id
GROUP BY ac.id, ac.title;

-- ============================================================================
-- FIN DU FICHIER 99_views.sql
-- ============================================================================
