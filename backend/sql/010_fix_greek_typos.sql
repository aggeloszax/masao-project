-- Fixes Greek typos in menu data that was already seeded.
-- 002 shipped the Tiramisu description with "κέμα" instead of "κρέμα".
-- The update only touches the row while it still holds the typo, so a
-- description already edited from the admin panel stays as it is.

begin;

update menu_item_translations mit
set description = replace(mit.description, 'κέμα', 'κρέμα'),
    updated_at = now()
from menu_items mi
where mit.menu_item_id = mi.id
  and mi.external_id = 'DE003'
  and mit.language_code = 'el'
  and mit.description like '%κέμα%';

commit;
