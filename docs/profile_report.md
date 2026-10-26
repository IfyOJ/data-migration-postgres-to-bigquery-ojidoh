# Source Database Profile (dvdrental)

Tables: 15  |  Total rows: 44,820

## Tables

| table         |   row_count |   columns | primary_key          |
|:--------------|------------:|----------:|:---------------------|
| actor         |         200 |         4 | actor_id             |
| address       |         603 |         8 | address_id           |
| category      |          16 |         3 | category_id          |
| city          |         600 |         4 | city_id              |
| country       |         109 |         3 | country_id           |
| customer      |         599 |        10 | customer_id          |
| film          |        1000 |        13 | film_id              |
| film_actor    |        5462 |         3 | actor_id, film_id    |
| film_category |        1000 |         3 | category_id, film_id |
| inventory     |        4581 |         4 | inventory_id         |
| language      |           6 |         3 | language_id          |
| payment       |       14596 |         6 | payment_id           |
| rental        |       16044 |         7 | rental_id            |
| staff         |           2 |        11 | staff_id             |
| store         |           2 |         4 | store_id             |

## Columns needing special handling

| table   | column           | pg_type                    | bigquery_type   | bigquery_mode   | note                                                                           |
|:--------|:-----------------|:---------------------------|:----------------|:----------------|:-------------------------------------------------------------------------------|
| film    | rating           | USER-DEFINED (mpaa_rating) | STRING          | NULLABLE        | Custom enum types (e.g. film.rating / mpaa_rating) become plain strings.       |
| film    | special_features | ARRAY (_text)              | STRING          | REPEATED        | Arrays (e.g. film.special_features) become REPEATED fields.                    |
| film    | fulltext         | tsvector                   | -               | DROP            | Full-text search vectors (film.fulltext) have no BigQuery equivalent. Dropped. |

## All columns

| table         | column           | pg_type                     | nullable   |   null_count | primary_key   | bigquery_type   | bigquery_mode   | note                                                                           |
|:--------------|:-----------------|:----------------------------|:-----------|-------------:|:--------------|:----------------|:----------------|:-------------------------------------------------------------------------------|
| actor         | actor_id         | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| actor         | first_name       | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| actor         | last_name        | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| actor         | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| address       | address_id       | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| address       | address          | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| address       | address2         | character varying           | YES        |            4 |               | STRING          | NULLABLE        |                                                                                |
| address       | district         | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| address       | city_id          | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| address       | postal_code      | character varying           | YES        |            0 |               | STRING          | NULLABLE        |                                                                                |
| address       | phone            | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| address       | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| category      | category_id      | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| category      | name             | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| category      | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| city          | city_id          | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| city          | city             | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| city          | country_id       | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| city          | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| country       | country_id       | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| country       | country          | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| country       | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| customer      | customer_id      | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| customer      | store_id         | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| customer      | first_name       | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| customer      | last_name        | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| customer      | email            | character varying           | YES        |            0 |               | STRING          | NULLABLE        |                                                                                |
| customer      | address_id       | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| customer      | activebool       | boolean                     | NO         |            0 |               | BOOL            | NULLABLE        |                                                                                |
| customer      | create_date      | date                        | NO         |            0 |               | DATE            | NULLABLE        |                                                                                |
| customer      | last_update      | timestamp without time zone | YES        |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| customer      | active           | integer                     | YES        |            0 |               | INT64           | NULLABLE        |                                                                                |
| film          | film_id          | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| film          | title            | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| film          | description      | text                        | YES        |            0 |               | STRING          | NULLABLE        |                                                                                |
| film          | release_year     | integer                     | YES        |            0 |               | INT64           | NULLABLE        |                                                                                |
| film          | language_id      | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| film          | rental_duration  | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| film          | rental_rate      | numeric                     | NO         |            0 |               | NUMERIC         | NULLABLE        |                                                                                |
| film          | length           | smallint                    | YES        |            0 |               | INT64           | NULLABLE        |                                                                                |
| film          | replacement_cost | numeric                     | NO         |            0 |               | NUMERIC         | NULLABLE        |                                                                                |
| film          | rating           | USER-DEFINED (mpaa_rating)  | YES        |            0 |               | STRING          | NULLABLE        | Custom enum types (e.g. film.rating / mpaa_rating) become plain strings.       |
| film          | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| film          | special_features | ARRAY (_text)               | YES        |            0 |               | STRING          | REPEATED        | Arrays (e.g. film.special_features) become REPEATED fields.                    |
| film          | fulltext         | tsvector                    | NO         |            0 |               | -               | DROP            | Full-text search vectors (film.fulltext) have no BigQuery equivalent. Dropped. |
| film_actor    | actor_id         | smallint                    | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| film_actor    | film_id          | smallint                    | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| film_actor    | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| film_category | film_id          | smallint                    | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| film_category | category_id      | smallint                    | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| film_category | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| inventory     | inventory_id     | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| inventory     | film_id          | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| inventory     | store_id         | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| inventory     | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| language      | language_id      | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| language      | name             | character                   | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| language      | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| payment       | payment_id       | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| payment       | customer_id      | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| payment       | staff_id         | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| payment       | rental_id        | integer                     | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| payment       | amount           | numeric                     | NO         |            0 |               | NUMERIC         | NULLABLE        |                                                                                |
| payment       | payment_date     | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| rental        | rental_id        | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| rental        | rental_date      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| rental        | inventory_id     | integer                     | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| rental        | customer_id      | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| rental        | return_date      | timestamp without time zone | YES        |          183 |               | DATETIME        | NULLABLE        |                                                                                |
| rental        | staff_id         | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| rental        | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| staff         | staff_id         | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| staff         | first_name       | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| staff         | last_name        | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| staff         | address_id       | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| staff         | email            | character varying           | YES        |            0 |               | STRING          | NULLABLE        |                                                                                |
| staff         | store_id         | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| staff         | active           | boolean                     | NO         |            0 |               | BOOL            | NULLABLE        |                                                                                |
| staff         | username         | character varying           | NO         |            0 |               | STRING          | NULLABLE        |                                                                                |
| staff         | password         | character varying           | YES        |            0 |               | STRING          | NULLABLE        |                                                                                |
| staff         | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
| staff         | picture          | bytea                       | YES        |            1 |               | BYTES           | NULLABLE        |                                                                                |
| store         | store_id         | integer                     | NO         |            0 | yes           | INT64           | NULLABLE        |                                                                                |
| store         | manager_staff_id | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| store         | address_id       | smallint                    | NO         |            0 |               | INT64           | NULLABLE        |                                                                                |
| store         | last_update      | timestamp without time zone | NO         |            0 |               | DATETIME        | NULLABLE        |                                                                                |
