import asyncio

from loguru import logger


async def runner_worker(name, runner):
    logger.info(f"{name} Runner starting")
    task = asyncio.create_task(runner.execute())
    try:
        return await asyncio.wait_for(task, timeout=runner.timeout)
    except asyncio.TimeoutError:
        task.cancel()
        logger.error(f"{name} Runner timed out after {runner.timeout}s")
        raise


async def engine_worker(name, engine, uuid):
    logger.info(f"[{name}] engine id={uuid} starting")
    result = await engine.initialize()
    logger.info(f"[{name}] engine id={uuid} finished")
    return result
