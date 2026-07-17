-- Masao Restaurant Chatbot MVP schema for Supabase/PostgreSQL.
-- Production-oriented schema: canonical menu rows plus normalized translations.

create extension if not exists pgcrypto;

create table if not exists menu_categories (
    id serial primary key,
    name varchar(120) not null unique,
    slug varchar(160),
    display_order int not null default 0,
    created_at timestamp with time zone not null default now()
);

create table if not exists menu_items (
    id serial primary key,
    external_id varchar(32),
    category_id int not null references menu_categories(id) on delete restrict,
    name varchar(160) not null,
    description text not null default '',
    price decimal(10, 2) not null check (price >= 0),
    tags text[] not null default '{}',
    is_available boolean not null default true,
    display_order int not null default 0,
    created_at timestamp with time zone not null default now()
);

create table if not exists menu_category_translations (
    id serial primary key,
    category_id int not null references menu_categories(id) on delete cascade,
    language_code varchar(8) not null,
    name varchar(160) not null,
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    constraint uq_menu_category_translations_language unique (category_id, language_code),
    constraint ck_menu_category_translations_language check (language_code in ('el', 'en', 'de', 'it', 'sv'))
);

create table if not exists menu_item_translations (
    id serial primary key,
    menu_item_id int not null references menu_items(id) on delete cascade,
    language_code varchar(8) not null,
    name varchar(160) not null,
    description text not null default '',
    created_at timestamp with time zone not null default now(),
    updated_at timestamp with time zone not null default now(),
    constraint uq_menu_item_translations_language unique (menu_item_id, language_code),
    constraint ck_menu_item_translations_language check (language_code in ('el', 'en', 'de', 'it', 'sv'))
);

create table if not exists chat_sessions (
    id uuid primary key default gen_random_uuid(),
    device_id varchar(128) not null,
    table_number int not null check (table_number > 0),
    created_at timestamp with time zone not null default now(),
    is_active boolean not null default true
);

create table if not exists chat_messages (
    id serial primary key,
    session_id uuid not null references chat_sessions(id) on delete cascade,
    role varchar(16) not null check (role in ('user', 'assistant', 'system')),
    content text not null check (length(trim(content)) > 0),
    created_at timestamp with time zone not null default now()
);

-- Backward-compatible additions if an earlier MVP schema already exists.
alter table menu_categories add column if not exists slug varchar(160);
alter table menu_items add column if not exists external_id varchar(32);
alter table menu_items add column if not exists display_order int not null default 0;

create index if not exists idx_menu_categories_display_order
    on menu_categories(display_order, id);

create unique index if not exists uq_menu_categories_slug
    on menu_categories(slug)
    where slug is not null;

create index if not exists idx_menu_items_category_available
    on menu_items(category_id, is_available, display_order);

create index if not exists idx_menu_items_tags_gin
    on menu_items using gin(tags);

create unique index if not exists uq_menu_items_external_id
    on menu_items(external_id)
    where external_id is not null;

create index if not exists idx_menu_category_translations_language
    on menu_category_translations(language_code, category_id);

create index if not exists idx_menu_item_translations_language
    on menu_item_translations(language_code, menu_item_id);

-- One active session per mobile device per physical table.
create unique index if not exists uq_chat_sessions_active_device_table
    on chat_sessions(device_id, table_number)
    where is_active = true;

create index if not exists idx_chat_messages_session_created
    on chat_messages(session_id, created_at, id);

create index if not exists idx_chat_sessions_created_at
    on chat_sessions(created_at);
