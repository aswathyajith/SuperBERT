CREATE INDEX key_idx ON shadow (key);
-- CREATE INDEX doi_idx  ON shadow (doi);
-- CREATE INDEX year_idx ON shadow (year);
-- CREATE INDEX pmid_idx ON shadow (pmid);
-- CREATE INDEX lang_idx ON shadow (lang);
-- CREATE INDEX titl_idx ON shadow USING gin(to_tsvector('pg_catalog.english', titl));
-- CREATE INDEX jour_idx ON shadow USING gin(to_tsvector('pg_catalog.english', jour));
