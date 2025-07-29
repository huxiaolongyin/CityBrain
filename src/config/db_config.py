import os

# 从环境变量获取数据库主机，如果未设置则默认为 localhost
# TODO: 放入 env 及 config 管理
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5555")

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": DB_HOST,
                "port": DB_PORT,
                "user": "city_brain",
                "password": "city_brain123",
                "database": "city_brain",
            },
        },
    },
    "apps": {
        "app_system": {
            "models": [
                "aerich.models",
                "models.database",
                "models.collect",
                "models.security_audit",
                "models.metric",
            ],
            "default_connection": "default",
        }
    },
}
