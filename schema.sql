SET TIME ZONE 'UTC';

CREATE TABLE authorizations (
	user_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	secret BYTEA,
	description TEXT NOT NULL
);

-- an image is one or more tiled designs
CREATE TABLE images (
	image_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
	author_id INTEGER NOT NULL REFERENCES authorizations ON DELETE SET NULL,
	author_name TEXT,
	image_name TEXT,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
	width SMALLINT,
	height SMALLINT,
	layers BYTEA[] NOT NULL,
	pro BOOLEAN GENERATED ALWAYS AS (array_length(layers, 1) > 1) STORED,

	type_code SMALLINT NOT NULL,

	-- if one is provided, both must be
	CHECK ((pro AND width IS NULL AND height IS NULL) OR (not pro AND width IS NOT NULL AND height IS NOT NULL))
);

CREATE INDEX latest_images ON images (created_at DESC);

-- a design is a single small image uploaded to ACNH servers.
CREATE TABLE designs (
	design_id BIGINT NOT NULL PRIMARY KEY,
	-- no ON DELETE CASCADE because these should be deleted
	image_id INTEGER NOT NULL REFERENCES images,
	-- what position is it in in the original image?
	position SMALLINT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
	pro BOOLEAN NOT NULL
);

CREATE INDEX design_sequence_idx ON designs (image_id, position);
-- lets us find which ones to garbage collect
CREATE INDEX oldest_designs ON designs (pro, created_at);

