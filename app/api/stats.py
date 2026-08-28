from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.stats import SourceStatsRead

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/sources", response_model=list[SourceStatsRead])
async def get_source_stats(
    session: AsyncSession = Depends(get_session),
) -> list[SourceStatsRead]:
    stmt = text("""
        WITH event_stats AS (
            SELECT
                source_id,
                COUNT(*) AS event_count,
                AVG(severity) AS avg_severity,
                MAX(occurred_at) AS last_event_at
            FROM events
            GROUP BY source_id
        ),
        alert_stats AS (
            SELECT
                source_id,
                COUNT(*) AS alert_count
            FROM alerts
            GROUP BY source_id
        )
        SELECT
            s.id AS source_id,
            s.name AS source_name,
            COALESCE(e.event_count, 0) AS event_count,
            COALESCE(a.alert_count, 0) AS alert_count,
            e.avg_severity,
            e.last_event_at,
            CASE
                WHEN SUM(COALESCE(e.event_count, 0)) OVER () = 0
                    THEN 0
                ELSE ROUND(
                    COALESCE(e.event_count, 0)::numeric
                    * 100
                    / SUM(COALESCE(e.event_count, 0)) OVER (),
                    2
                )
            END AS event_share_percent
        FROM sources AS s
        LEFT JOIN event_stats AS e ON e.source_id = s.id
        LEFT JOIN alert_stats AS a ON a.source_id = s.id
        ORDER BY event_count DESC
    """)

    result = await session.execute(stmt)

    return [
        SourceStatsRead(**row)
        for row in result.mappings().all()
    ]
