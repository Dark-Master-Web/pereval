-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    fam VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    otc VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица координат
CREATE TABLE IF NOT EXISTS coords (
    id SERIAL PRIMARY KEY,
    latitude DECIMAL NOT NULL,
    longitude DECIMAL NOT NULL,
    height INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица перевалов
CREATE TABLE IF NOT EXISTS pereval_added (
    id SERIAL PRIMARY KEY,
    beauty_title VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    other_titles VARCHAR(255),
    connect TEXT,
    add_time TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    user_id INTEGER NOT NULL REFERENCES users(id),
    coord_id INTEGER NOT NULL REFERENCES coords(id),
    status VARCHAR(20) DEFAULT 'new' CHECK (status IN ('new', 'pending', 'accepted', 'rejected')),
    reject_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица уровней сложности
CREATE TABLE IF NOT EXISTS pereval_levels (
    id SERIAL PRIMARY KEY,
    pereval_id INTEGER NOT NULL REFERENCES pereval_added(id) ON DELETE CASCADE,
    winter VARCHAR(10),
    summer VARCHAR(10),
    autumn VARCHAR(10),
    spring VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица изображений
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    data BYTEA,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Связующая таблица для перевалов и изображений
CREATE TABLE IF NOT EXISTS pereval_images (
    id SERIAL PRIMARY KEY,
    pereval_id INTEGER NOT NULL REFERENCES pereval_added(id) ON DELETE CASCADE,
    image_id INTEGER NOT NULL REFERENCES images(id) ON DELETE CASCADE,
    UNIQUE(pereval_id, image_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица модераторов
CREATE TABLE IF NOT EXISTS moderators (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица логов изменений статусов
CREATE TABLE IF NOT EXISTS status_logs (
    id SERIAL PRIMARY KEY,
    pereval_id INTEGER NOT NULL REFERENCES pereval_added(id) ON DELETE CASCADE,
    old_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    moderator_id INTEGER REFERENCES moderators(id),
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);

-- Индексы для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_pereval_added_user_id ON pereval_added(user_id);
CREATE INDEX IF NOT EXISTS idx_pereval_added_status ON pereval_added(status);
CREATE INDEX IF NOT EXISTS idx_pereval_added_coord_id ON pereval_added(coord_id);
CREATE INDEX IF NOT EXISTS idx_pereval_levels_pereval_id ON pereval_levels(pereval_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_status_logs_pereval_id ON status_logs(pereval_id);
CREATE INDEX IF NOT EXISTS idx_status_logs_changed_at ON status_logs(changed_at);
CREATE INDEX IF NOT EXISTS idx_moderators_email ON moderators(email);