CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    message_content TEXT NOT NULL,
    seed TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 以下は将来的な権限管理のために検討できるテーブルの例（現時点では使用しません）
-- CREATE TABLE IF NOT EXISTS users (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     username TEXT NOT NULL UNIQUE,
--     password_hash TEXT NOT NULL,
--     role TEXT NOT NULL DEFAULT '青ID' -- 青ID, スピーカー, マネージャー, モデレーター, サミット, 運営
-- );
-- CREATE TABLE IF NOT EXISTS banned_ips (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     ip_address TEXT NOT NULL UNIQUE,
--     banned_until DATETIME
-- );
-- CREATE TABLE IF NOT EXISTS ng_words (
--     id INTEGER PRIMARY KEY AUTOINCREMENT,
--     word TEXT NOT NULL UNIQUE
-- );
