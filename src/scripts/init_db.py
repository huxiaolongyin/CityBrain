from aerich import Command

from config.db_config import TORTOISE_ORM
from utils.logger import get_logger

logger = get_logger(__name__)


async def modify_db(config=None):
    """
    初始化数据库
    """
    if config is None:
        config = TORTOISE_ORM
    command = Command(tortoise_config=config, app="app_system")
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    logger.debug("数据库连接初始化完成")
    await command.migrate()
    logger.debug("数据库迁移完成")
    await command.upgrade(run_in_transaction=True)
    logger.debug("数据库升级完成")
