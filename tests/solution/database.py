def generate_sql_initialization_code():
    return [
        "CREATE TABLE IF NOT EXISTS User (username VARCHAR(255) PRIMARY KEY, password VARCHAR(255) NOT NULL);"
    ]