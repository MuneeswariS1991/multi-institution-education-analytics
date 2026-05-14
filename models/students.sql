{{ config(
    materialized='incremental',
    unique_key='student_id',
    schema='student_schema',
    alias='students'
) }}

WITH source_data AS (

    SELECT
        STUDENT_ID,
        STUDENT_NAME,
        COURSE_NAME,
        SCORE,
        ATTENDANCE_PERCENT,
        CREATED_DATE
    FROM EDUCATION_ANALYTICS_DB.STUDENT_SCHEMA.STUDENT_PERFORMANCE

),

existing_data AS (

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
            NULL AS CHANGE_TYPE_FLAG,
            NULL AS IS_CURRENT,
            NULL AS EFFECTIVE_START_DATE,
            NULL AS EFFECTIVE_END_DATE
        WHERE 1=0
    {% endif %}

),

final_data AS (

    SELECT
        s.STUDENT_ID,
        s.STUDENT_NAME,
        s.COURSE_NAME,
        s.SCORE,
        s.ATTENDANCE_PERCENT,
        s.CREATED_DATE,

        CASE
            WHEN e.STUDENT_ID IS NULL THEN 'I'
            WHEN e.SCORE <> s.SCORE
              OR e.ATTENDANCE_PERCENT <> s.ATTENDANCE_PERCENT
              OR e.COURSE_NAME <> s.COURSE_NAME
              OR e.STUDENT_NAME <> s.STUDENT_NAME
            THEN 'U'
            ELSE 'I'
        END AS CHANGE_TYPE_FLAG,

        'Y' AS IS_CURRENT,
        CURRENT_TIMESTAMP AS EFFECTIVE_START_DATE,
        NULL AS EFFECTIVE_END_DATE

    FROM source_data s
    LEFT JOIN existing_data e
        ON s.STUDENT_ID = e.STUDENT_ID
)

SELECT * FROM final_data