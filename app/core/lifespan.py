from contextlib import asynccontextmanager
import logging
from time import perf_counter

from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import get_logger, log_event
from app.db.session import initialize_database
from app.db.session import get_session_factory
from app.graph.db import initialize_graph_database
from app.services.auth_service import AuthService
from app.services.graph_service import GraphService
from app.services.runtime_status_service import runtime_status_service

logger = get_logger(__name__)
graph_service = GraphService()

@asynccontextmanager
async def lifespan(_: FastAPI):
    start = perf_counter()
    runtime_status_service.reset()

    try:
        config_summary = settings.runtime_config_summary()
        runtime_status_service.mark_config_loaded()
        log_event(
            logger,
            logging.INFO,
            "settings_init",
            "success",
            app_env=settings.APP_ENV,
            app_name=settings.APP_NAME,
            port=settings.PORT,
            instance_id=settings.GRAPH_INSTANCE_ID,
            config_summary=config_summary,
        )

        try:
            initialize_database()
        except Exception as exc:
            runtime_status_service.record_error(error_type="sqlite_init_error", detail=str(exc))
            log_event(
                logger,
                logging.ERROR,
                "sqlite_init",
                "failed",
                error_type="sqlite_init_error",
                detail=str(exc),
                path=settings.SQLITE_PATH,
            )
            raise
        runtime_status_service.mark_sqlite_ready()
        log_event(
            logger,
            logging.INFO,
            "sqlite_init",
            "success",
            path=settings.SQLITE_PATH,
            instance_id=settings.GRAPH_INSTANCE_ID,
        )
        runtime_status_service.mark_migration_ready()
        log_event(
            logger,
            logging.INFO,
            "migration_init",
            "success",
            path=settings.SQLITE_PATH,
            instance_id=settings.GRAPH_INSTANCE_ID,
        )

        if settings.GRAPH_ENABLED:
            log_event(
                logger,
                logging.INFO,
                "graph_module_check",
                "enabled",
                instance_id=settings.GRAPH_INSTANCE_ID,
                path=str(settings.graph_instance_path),
            )
            try:
                initialize_graph_database()
            except Exception as exc:
                runtime_status_service.record_error(error_type="migration_error", detail=str(exc))
                log_event(
                    logger,
                    logging.ERROR,
                    "graph_path_check",
                    "failed",
                    error_type="migration_error",
                    detail=str(exc),
                    instance_id=settings.GRAPH_INSTANCE_ID,
                    path=str(settings.graph_instance_path),
                )
                raise
            log_event(
                logger,
                logging.INFO,
                "graph_path_check",
                "success",
                instance_id=settings.GRAPH_INSTANCE_ID,
                path=str(settings.graph_instance_path),
            )
            if settings.GRAPH_RELOAD_ON_START:
                log_event(
                    logger,
                    logging.INFO,
                    "graph_load_start",
                    "started",
                    instance_id=settings.GRAPH_INSTANCE_ID,
                    path=str(settings.graph_instance_path),
                )
                try:
                    summary = graph_service.reload_graph()
                except Exception as exc:
                    runtime_status_service.record_error(error_type="graph_load_error", detail=str(exc))
                    log_event(
                        logger,
                        logging.ERROR,
                        "graph_load_complete",
                        "failed",
                        instance_id=settings.GRAPH_INSTANCE_ID,
                        error_type="graph_load_error",
                        detail=str(exc),
                    )
                    raise
                runtime_status_service.mark_graph_status(
                    loaded=summary["loaded"],
                    node_count=summary["node_count"],
                    edge_count=summary["edge_count"],
                    loaded_at=summary["last_loaded_at"],
                )
                log_event(
                    logger,
                    logging.INFO,
                    "graph_load_complete",
                    "success",
                    instance_id=settings.GRAPH_INSTANCE_ID,
                    node_count=summary["node_count"],
                    edge_count=summary["edge_count"],
                    duration_ms=round((perf_counter() - start) * 1000, 2),
                )
            else:
                runtime_status_service.mark_graph_status(loaded=False)
        else:
            log_event(
                logger,
                logging.INFO,
                "graph_module_check",
                "disabled",
                instance_id=settings.GRAPH_INSTANCE_ID,
            )

        log_event(
            logger,
            logging.INFO,
            "csv_export_dir_check",
            "success",
            instance_id=settings.GRAPH_INSTANCE_ID,
            path=settings.CSV_EXPORT_DIR,
        )

        admin_password = settings.resolved_initial_admin_password
        if settings.INITIAL_ADMIN_USERNAME and admin_password:
            session = get_session_factory()()
            try:
                AuthService().ensure_admin_account(
                    session,
                    username=settings.INITIAL_ADMIN_USERNAME,
                    password=admin_password,
                )
            finally:
                session.close()

        log_event(
            logger,
            logging.INFO,
            "startup_complete",
            "success",
            instance_id=settings.GRAPH_INSTANCE_ID,
            port=settings.PORT,
            duration_ms=round((perf_counter() - start) * 1000, 2),
        )
        yield
    except ValueError as exc:
        runtime_status_service.record_error(error_type="config_error", detail=str(exc))
        log_event(logger, logging.ERROR, "startup_error", "failed", error_type="config_error", detail=str(exc))
        raise
    except Exception as exc:
        log_event(logger, logging.ERROR, "startup_error", "failed", detail=str(exc))
        raise
