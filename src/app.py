import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from tortoise.contrib.fastapi import register_tortoise

from api.router import router
from config.db_config import TORTOISE_ORM
from scripts.init_db import modify_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await modify_db()
        yield
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")


app = FastAPI(title="CityBrain API", lifespan=lifespan, docs_url=None)

# 加载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")


# 自定义 Swagger 文档路由
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


# 自定义 OpenAPI 文档路由
@app.get("/openapi.json", include_in_schema=False)
async def get_openapi_json():
    return app.openapi()


app.include_router(router, prefix="/api")

register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)
