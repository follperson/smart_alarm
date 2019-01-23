DROP TABLE IF EXISTS alarms;
DROP TABLE IF EXISTS color_profiles;
DROP TABLE IF EXISTS sound_profiles;
DROP TABLE IF EXISTS songs;
DROP TABLE IF EXISTS playlists;
DROP TABLE IF EXISTS playlist;


CREATE TABLE alarms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  name TEXT NOT NULL,
  alarm_time TIME NOT NULL,
  active BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_monday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_tuesday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_wednesday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_thursday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_friday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_saturday BOOLEAN NOT NULL DEFAULT FALSE,
  repeat_sunday BOOLEAN NOT NULL DEFAULT FALSE,
  sound_profile INTEGER NOT NULL DEFAULT 1,
  color_profile INTEGER NOT NULL DEFAULT 1,
  FOREIGN KEY (sound_profile) REFERENCES sound_profiles(id),
  FOREIGN KEY (color_profile) REFERENCES color_profiles(id)
);

CREATE TABLE color_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_span INTEGER NOT NULL,
  name TEXT NOT NULL
);

CREATE TABLE sound_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time_span INTEGER NOT NULL,
  name TEXT NOT NULL,
  playlist_id integer not null,
  foreign key (playlist_id) references playlists(id)
);

CREATE TABLE audio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filepath TEXT NOT NULL,
  filename TEXT NOT NULL,
  name TEXT NOT NULL,
  album TEXT,
  artist TEXT,
  hash TEXT KEY not null,
  duration FlOAT NOT NULL
);

CREATE TABLE playlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
);

CREATE TABLE playlist (
  playlist_id INTEGER PRIMARY KEY not null,
  audio_id integer,
  audio_start integer,
  audio_end integer,
  playlist_order integer,
  foreign key (playlist_id) references playlists(id),
  foreign key (audio_id) references audio(id)
);
