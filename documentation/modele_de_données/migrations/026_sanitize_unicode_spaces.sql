-- Migration 026: Nettoyage des caractères de contrôle et espaces Unicode problématiques
-- Remplace les caractères de contrôle ASCII (0x00-0x1F sauf newline/CR, 0x7F)
-- et les espaces Unicode exotiques par des espaces normaux.
-- Ces caractères s'affichent comme des blocs cassés sur certains navigateurs mobiles.

BEGIN;

-- Events : title, description, venue, city
UPDATE events SET
    title = regexp_replace(title, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g'),
    description = regexp_replace(description, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g'),
    venue = regexp_replace(venue, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g'),
    city = regexp_replace(city, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g')
WHERE
    title ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]'
    OR description ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]'
    OR venue ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]'
    OR city ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]';

-- News : title, summary
UPDATE news SET
    title = regexp_replace(title, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g'),
    summary = regexp_replace(summary, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g')
WHERE
    title ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]'
    OR summary ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]';

-- Application calls : title
UPDATE application_calls SET
    title = regexp_replace(title, E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]', ' ', 'g')
WHERE
    title ~ E'[\\x00-\\x09\\x0B\\x0C\\x0E-\\x1F\\x7F\\u00A0\\u202F\\u2007\\u2009\\u200A\\u200B\\u2060\\uFEFF]';

COMMIT;
