{{ config(
    materialized='incremental',
    unique_key='student_id',
    schema='student_schema',
    alias='students_target'
) }}

WITH source_data AS (

    SELECT
        STUDENT_ID,
        STUDENT_NAME,
        COURSE_NAME,
        SCORE AS STUDENT_SCORE,          -- ✅ rename here
        ATTENDANCE_PERCENT,
        CREATED_DATE
    FROM EDUCATION_ANALYTICS_DB.STUDENT_SCHEMA.STUDENTS_RECORD

),

-- ✅ deduplicate to avoid merge errors
source_dedup AS (

    SELECT *
    FROM (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY STUDENT_ID
                   ORDER BY CREATED_DATE DESC
               ) rn
        FROM source_data
    )
    WHERE rn = 1
)

SELECT
    STUDENT_ID,
    STUDENT_NAME,
    COURSE_NAME,
    STUDENT_SCORE,
    ATTENDANCE_PERCENT,
    CREATED_DATE

FROM source_dedup

{% if is_incremental() %}

-- ✅ only process new/changed data (optional optimization)
WHERE CREATED_DATE >= (
    SELECT COALESCE(MAX(CREATED_DATE), '1900-01-01')
    FROM {{ this }}
)

{% endif %}