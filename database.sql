-- postgresql

CREATE TABLE post( id SERIAL PRIMARY KEY, profileid INTEGER NOT NULL, datetime DOUBLE PRECISION, post TEXT, replyto INTEGER, yea INTEGER DEFAULT 0, nay INTEGER DEFAULT 0, replies INTEGER DEFAULT 0, stake REAL DEFAULT 0);
CREATE INDEX post_profileid ON post(profileid);
CREATE INDEX post_replyto ON post(replyto);

CREATE TABLE profile( id SERIAL PRIMARY KEY, address TEXT NOT NULL, datetime DOUBLE PRECISION, handle TEXT NOT NULL, name TEXT NOT NULL );
CREATE INDEX profile_address ON profile(address);        
CREATE UNIQUE INDEX profile_handle ON profile(handle);          

CREATE TABLE follow( rowid SERIAL PRIMARY KEY, profileid INTEGER NOT NULL, followid INTEGER NOT NULL);
CREATE INDEX follow_profileid ON follow(profileid);

CREATE TABLE coin( address TEXT NOT NULL, value REAL DEFAULT 0, stake REAL DEFAULT 0);
CREATE UNIQUE INDEX coin_address ON coin(address); 

CREATE TABLE vote( profileid INTEGER NOT NULL, postid INTEGER NOT NULL, vote INTEGER NOT NULL);
CREATE INDEX vote_profileid ON vote(profileid);
CREATE UNIQUE INDEX vote_unique ON vote(profileid,postid);

CREATE TABLE hashtag( id SERIAL PRIMARY KEY, hashtag TEXT NOT NULL );
CREATE UNIQUE INDEX hashtag_hashtag ON hashtag(hashtag);

CREATE TABLE tag( rowid SERIAL PRIMARY KEY, hashtagid INTEGER NOT NULL, postid INTEGER NOT NULL);
CREATE INDEX tag_hashtagid ON tag(hashtagid);

