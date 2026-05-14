{{ config(
    materialized='incremental',
    incremental_strategy='append',
    schema='student_schema',
    alias='students_record_target'
) }}

WITH source_dedup AS (

    {{ deduplicate(
        'EDUCATION_ANALYTICS_DB.STUDENT_SCHEMA.STUDENTS_RECORD',
        'STUDENT_ID',
        'CREATED_DATE'
    ) }}

),

existing_current AS (

    {% if is_incremental() %}
        SELECT *
        FROM {{ this }}
        WHERE IS_CURRENT = 'Y'
    {% else %}
        SELECT
            NULL AS STUDENT_ID,
            NULL AS STUDENT_NAME,
            NULL AS COURSE_NAME,
            NULL AS SCORE,
            NULL AS ATTENDANCE_PERCENT,
            NULL AS CREATED_DATE,
            NULL AS IS_CURRENT,
            NULL AS EFFECTIVE_START_DATE,
            NULL AS EFFECTIVE_END_DATE
        WHERE 1=0
    {% endif %}
),

change_detection AS (

    SELECT
        s.STUDENT_ID,
        s.STUDENT_NAME,
        s.COURSE_NAME,
        s.SCORE,
        s.ATTENDANCE_PERCENT,
        s.CREATED_DATE,

        CASE
            WHEN e.STUDENT_ID IS NULL THEN 'I'
            WHEN
                COALESCE(e.SCORE, -1) <> COALESCE(s.SCORE, -1)
             OR COALESCE(e.ATTENDANCE_PERCENT, -1) <> COALESCE(s.ATTENDANCE_PERCENT, -1)
             OR COALESCE(e.COURSE_NAME, '') <> COALESCE(s.COURSE_NAME, '')
             OR COALESCE(e.STUDENT_NAME, '') <> COALESCE(s.STUDENT_NAME, '')
            THEN 'U'
            ELSE NULL
        END AS CHANGE_TYPE_FLAG

    FROM source_dedup s
    LEFT JOIN existing_current e
        ON s.STUDENT_ID = e.STUDENT_ID
),

final_insert AS (

    SELECT
        STUDENT_ID,
        STUDENT_NAME,
        COURSE_NAME,
        SCORE,
        ATTENDANCE_PERCENT,
        CREATED_DATE,
        'Y' AS IS_CURRENT,
        CURRENT_TIMESTAMP AS EFFECTIVE_START_DATE,
        NULL AS EFFECTIVE_END_DATE

    FROM change_detection
    WHERE CHANGE_TYPE_FLAG IN ('I','U')
)

SELECT * FROM final_insert