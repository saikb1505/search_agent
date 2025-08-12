CREATE TABLE salesql_enriched_people (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    search_id INT UNSIGNED NOT NULL,
    google_result_id INT UNSIGNED NULL,

    person_uuid VARCHAR(64) NULL,
    full_name VARCHAR(255) NULL,
    first_name VARCHAR(255) NULL,
    last_name VARCHAR(255) NULL,
    linkedin_url VARCHAR(512) NOT NULL,
    title VARCHAR(255) NULL,
    headline VARCHAR(512) NULL,
    person_industry VARCHAR(255) NULL,
    image_url VARCHAR(1024) NULL,

    person_city VARCHAR(255) NULL,
    person_state VARCHAR(255) NULL,
    person_country_code VARCHAR(8) NULL,
    person_country VARCHAR(255) NULL,
    person_region VARCHAR(255) NULL,

    org_uuid VARCHAR(64) NULL,
    org_name VARCHAR(255) NULL,
    org_website VARCHAR(512) NULL,
    org_domain VARCHAR(255) NULL,
    org_linkedin_url VARCHAR(512) NULL,
    org_employees INT UNSIGNED NULL,
    org_industry VARCHAR(255) NULL,

    org_city VARCHAR(255) NULL,
    org_state VARCHAR(255) NULL,
    org_country_code VARCHAR(8) NULL,
    org_country VARCHAR(255) NULL,
    org_region VARCHAR(255) NULL,

    emails_json JSON NULL,
    phones_json JSON NULL,
    raw_json JSON NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
