-- SUPERSEDED / NO-OP: Hebrew ('he') is a supported language again.
-- This migration used to delete Hebrew rows and narrow the language check
-- constraints while Hebrew support was withdrawn. Its destructive body has
-- been removed so that running the sql/ directory in filename order can
-- never wipe Hebrew data. The original statements are preserved in git
-- history (see this file before commit "Add Turkish (tr) as a supported
-- language"). Databases that ran the old version of this file are repaired
-- by 005_add_hebrew_translations.sql plus the 002 seed (or 007-style language migrations).

-- Intentionally empty.
