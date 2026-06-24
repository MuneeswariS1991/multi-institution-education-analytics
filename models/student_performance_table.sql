{{ config(
    materialized='incremental',
    unique_key='student_id',
    schema='student_schema',
    alias='student_performance_table'
) }}

SELECT
    STUDENT_ID,
    STUDENT_NAME,
    COURSE_NAME,
    SCORE,
    ATTENDANCE_PERCENT,
    CREATED_DATE
FROM EDUCATION_ANALYTICS_DB.STUDENT_SCHEMA.STUDENT_PERFORMANCES

{% if is_incremental() %}
WHERE CREATED_DATE > (
    SELECT COALESCE(MAX(CREATED_DATE), '1900-01-01'::TIMESTAMP)
    FROM {{ this }}
)
{% endif %}
