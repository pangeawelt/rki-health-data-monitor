-- 1) Aktuelle Werte je Region, alle Altersgruppen
WITH ranked AS (
    SELECT
        r.region_name,
        f.calendar_week,
        f.incidence_value,
        ROW_NUMBER() OVER (
            PARTITION BY r.region_id
            ORDER BY f.calendar_week DESC
        ) AS rn
    FROM fact_are_incidence f
    JOIN dim_region r ON r.region_id = f.region_id
    JOIN dim_age_group a ON a.age_group_id = f.age_group_id
    WHERE a.age_group_code = '00+'
)
SELECT region_name, calendar_week, incidence_value
FROM ranked
WHERE rn = 1
ORDER BY incidence_value DESC;

-- 2) Vorwochenvergleich
SELECT
    f.calendar_week,
    f.incidence_value,
    LAG(f.incidence_value) OVER (ORDER BY f.calendar_week) AS previous_week,
    ROUND(
        100.0 * (f.incidence_value - LAG(f.incidence_value) OVER (ORDER BY f.calendar_week))
        / NULLIF(LAG(f.incidence_value) OVER (ORDER BY f.calendar_week), 0),
        1
    ) AS change_percent
FROM fact_are_incidence f
JOIN dim_region r ON r.region_id = f.region_id
JOIN dim_age_group a ON a.age_group_id = f.age_group_id
WHERE r.region_name = 'Baden-Wuerttemberg'
  AND a.age_group_code = '00+'
ORDER BY f.calendar_week;

-- 3) Vier-Wochen-Mittel
SELECT
    f.calendar_week,
    f.incidence_value,
    ROUND(
        AVG(f.incidence_value) OVER (
            ORDER BY f.calendar_week
            ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
        ), 1
    ) AS moving_average_4w
FROM fact_are_incidence f
JOIN dim_region r ON r.region_id = f.region_id
JOIN dim_age_group a ON a.age_group_id = f.age_group_id
WHERE r.region_name = 'Baden-Wuerttemberg'
  AND a.age_group_code = '00+'
ORDER BY f.calendar_week;

-- 4) Letzte ETL-Läufe
SELECT
    etl_run_id, started_at, finished_at, status, source_type,
    rows_downloaded, rows_valid, rows_rejected, rows_inserted, rows_updated
FROM etl_run
ORDER BY etl_run_id DESC
LIMIT 10;
