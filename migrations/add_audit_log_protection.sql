-- SQL міграція для захисту журналу аудиту від змін та видалення
-- Це забезпечує незмінність записів на рівні бази даних

-- Заборона UPDATE для таблиці event_log
CREATE OR REPLACE FUNCTION prevent_event_log_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Event log entries cannot be modified. This is an audit log.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_event_log_update_trigger
    BEFORE UPDATE ON event_log
    FOR EACH ROW
    EXECUTE FUNCTION prevent_event_log_update();

-- Заборона DELETE для таблиці event_log
CREATE OR REPLACE FUNCTION prevent_event_log_delete()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Event log entries cannot be deleted. This is an audit log.';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_event_log_delete_trigger
    BEFORE DELETE ON event_log
    FOR EACH ROW
    EXECUTE FUNCTION prevent_event_log_delete();

-- Створення індексів для швидкого пошуку
CREATE INDEX IF NOT EXISTS idx_event_log_user_id ON event_log(user_id);
CREATE INDEX IF NOT EXISTS idx_event_log_entity_type_id ON event_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_event_log_action_type ON event_log(action_type);
CREATE INDEX IF NOT EXISTS idx_event_log_timestamp ON event_log(timestamp DESC);
-- GIN індекс для JSONB (створюється тільки якщо поле має тип JSONB)
-- Спочатку перевіряємо тип колонки
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'event_log' 
        AND column_name = 'event_metadata' 
        AND data_type = 'jsonb'
    ) THEN
        CREATE INDEX IF NOT EXISTS idx_event_log_metadata ON event_log USING GIN (event_metadata);
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'event_log' 
        AND column_name = 'event_metadata' 
        AND data_type = 'json'
    ) THEN
        -- Якщо колонка має тип JSON, конвертуємо її в JSONB та створюємо індекс
        ALTER TABLE event_log ALTER COLUMN event_metadata TYPE jsonb USING event_metadata::jsonb;
        CREATE INDEX IF NOT EXISTS idx_event_log_metadata ON event_log USING GIN (event_metadata);
    END IF;
END $$;

