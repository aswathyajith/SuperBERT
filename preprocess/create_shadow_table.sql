DROP TABLE IF EXISTS shadow;
CREATE TABLE shadow (
    SID  bigserial NOT NULL,
    DOI  varchar(200),
    Titl text DEFAULT '',
    Year char(4) DEFAULT '',
    Lang varchar(50) DEFAULT '',
    Jour text DEFAULT '',
    Key  char(40) DEFAULT '',
    PMID varchar(40) DEFAULT ''
);

