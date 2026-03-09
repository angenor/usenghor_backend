-- Migration 018: EditorJS vers TOAST UI Editor
-- Renomme les colonnes TEXT contenant du JSON EditorJS en *_legacy
-- Ajoute les nouvelles colonnes *_html (TEXT) et *_md (TEXT)
-- Le script Python migrate_editorjs_to_toastui.py peuplera les nouvelles colonnes
-- Les colonnes *_legacy seront supprimees apres 30 jours de validation

BEGIN;

-- ============================================================
-- events (09_content.sql)
-- ============================================================
ALTER TABLE events RENAME COLUMN content TO content_legacy;
ALTER TABLE events ADD COLUMN content_html TEXT;
ALTER TABLE events ADD COLUMN content_md TEXT;

-- ============================================================
-- news (09_content.sql)
-- ============================================================
ALTER TABLE news RENAME COLUMN content TO content_legacy;
ALTER TABLE news ADD COLUMN content_html TEXT;
ALTER TABLE news ADD COLUMN content_md TEXT;

-- ============================================================
-- projects (10_project.sql)
-- ============================================================
ALTER TABLE projects RENAME COLUMN description TO description_legacy;
ALTER TABLE projects ADD COLUMN description_html TEXT;
ALTER TABLE projects ADD COLUMN description_md TEXT;

ALTER TABLE projects RENAME COLUMN summary TO summary_legacy;
ALTER TABLE projects ADD COLUMN summary_html TEXT;
ALTER TABLE projects ADD COLUMN summary_md TEXT;

-- ============================================================
-- project_calls (10_project.sql)
-- ============================================================
ALTER TABLE project_calls RENAME COLUMN description TO description_legacy;
ALTER TABLE project_calls ADD COLUMN description_html TEXT;
ALTER TABLE project_calls ADD COLUMN description_md TEXT;

ALTER TABLE project_calls RENAME COLUMN conditions TO conditions_legacy;
ALTER TABLE project_calls ADD COLUMN conditions_html TEXT;
ALTER TABLE project_calls ADD COLUMN conditions_md TEXT;

-- ============================================================
-- programs (07_academic.sql)
-- ============================================================
ALTER TABLE programs RENAME COLUMN description TO description_legacy;
ALTER TABLE programs ADD COLUMN description_html TEXT;
ALTER TABLE programs ADD COLUMN description_md TEXT;

ALTER TABLE programs RENAME COLUMN teaching_methods TO teaching_methods_legacy;
ALTER TABLE programs ADD COLUMN teaching_methods_html TEXT;
ALTER TABLE programs ADD COLUMN teaching_methods_md TEXT;

ALTER TABLE programs RENAME COLUMN format TO format_legacy;
ALTER TABLE programs ADD COLUMN format_html TEXT;
ALTER TABLE programs ADD COLUMN format_md TEXT;

ALTER TABLE programs RENAME COLUMN evaluation_methods TO evaluation_methods_legacy;
ALTER TABLE programs ADD COLUMN evaluation_methods_html TEXT;
ALTER TABLE programs ADD COLUMN evaluation_methods_md TEXT;

-- ============================================================
-- application_calls (08_application.sql)
-- ============================================================
ALTER TABLE application_calls RENAME COLUMN description TO description_legacy;
ALTER TABLE application_calls ADD COLUMN description_html TEXT;
ALTER TABLE application_calls ADD COLUMN description_md TEXT;

ALTER TABLE application_calls RENAME COLUMN target_audience TO target_audience_legacy;
ALTER TABLE application_calls ADD COLUMN target_audience_html TEXT;
ALTER TABLE application_calls ADD COLUMN target_audience_md TEXT;

-- ============================================================
-- sectors (04_organization.sql)
-- ============================================================
ALTER TABLE sectors RENAME COLUMN description TO description_legacy;
ALTER TABLE sectors ADD COLUMN description_html TEXT;
ALTER TABLE sectors ADD COLUMN description_md TEXT;

ALTER TABLE sectors RENAME COLUMN mission TO mission_legacy;
ALTER TABLE sectors ADD COLUMN mission_html TEXT;
ALTER TABLE sectors ADD COLUMN mission_md TEXT;

-- ============================================================
-- services (04_organization.sql)
-- ============================================================
ALTER TABLE services RENAME COLUMN description TO description_legacy;
ALTER TABLE services ADD COLUMN description_html TEXT;
ALTER TABLE services ADD COLUMN description_md TEXT;

ALTER TABLE services RENAME COLUMN mission TO mission_legacy;
ALTER TABLE services ADD COLUMN mission_html TEXT;
ALTER TABLE services ADD COLUMN mission_md TEXT;

-- ============================================================
-- service_objectives (04_organization.sql)
-- ============================================================
ALTER TABLE service_objectives RENAME COLUMN description TO description_legacy;
ALTER TABLE service_objectives ADD COLUMN description_html TEXT;
ALTER TABLE service_objectives ADD COLUMN description_md TEXT;

-- ============================================================
-- service_achievements (04_organization.sql)
-- ============================================================
ALTER TABLE service_achievements RENAME COLUMN description TO description_legacy;
ALTER TABLE service_achievements ADD COLUMN description_html TEXT;
ALTER TABLE service_achievements ADD COLUMN description_md TEXT;

-- ============================================================
-- service_projects (04_organization.sql)
-- ============================================================
ALTER TABLE service_projects RENAME COLUMN description TO description_legacy;
ALTER TABLE service_projects ADD COLUMN description_html TEXT;
ALTER TABLE service_projects ADD COLUMN description_md TEXT;

COMMIT;
