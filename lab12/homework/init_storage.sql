CREATE TABLE IF NOT EXISTS model_training_log (
    id SERIAL PRIMARY KEY,
    training_date TIMESTAMP,
    model_name VARCHAR(100),
    training_set_size INTEGER,
    test_mae FLOAT,
    is_best BOOLEAN
);
