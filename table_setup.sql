CREATE SCHEMA preddb;
CREATE TABLE preddb.registry(id INT PRIMARY KEY, type VARCHAR(100), url VARCHAR(200));
CREATE TABLE preddb.table_index(tableid INT PRIMARY KEY, tablename VARCHAR(100), numsamples INT, uploadtime TIMESTAMP, analyzetime TIMESTAMP);
CREATE TABLE preddb.models(tableid INT PRIMARY KEY, xl TEXT, latent TEXT);