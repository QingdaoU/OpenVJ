CREATE DATABASE IF NOT EXISTS openvj DEFAULT CHARACTER SET utf8;
use openvj;


CREATE TABLE IF NOT EXISTS oj (
  id VARCHAR(40) PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  status SMALLINT DEFAULT 1 NOT NULL
);


CREATE TABLE IF NOT EXISTS robot_user(
  id VARCHAR(40) PRIMARY KEY,
  oj_id VARCHAR(40) NOT NULL,
  username VARCHAR(50) NOT NULL,
  password VARCHAR(50) NOT NULL,
  status SMALLINT NOT NULL,
  last_login_time DATETIME NOT NULL,
  FOREIGN KEY (oj_id) REFERENCES oj(id),
  UNIQUE KEY oj_username (oj_id, username)
);


CREATE TABLE IF NOT EXISTS robot_status(
  name VARCHAR(40) NOT NULL,
  status SMALLINT NOT NULL,
  info TEXT NOT NULL,
  oj_id VARCHAR(40) NOT NULL,
  robot_user_id VARCHAR(40) NOT NULL,
  FOREIGN KEY (oj_id) REFERENCES oj(id),
  FOREIGN KEY (robot_user_id) REFERENCES robot_user(id)
);


CREATE TABLE IF NOT EXISTS apikey (
  apikey VARCHAR(40) PRIMARY KEY,
  name VARCHAR(50) NOT NULL ,
  create_time DATETIME DEFAULT NOW() NOT NULL,
  is_valid SMALLINT DEFAULT 1 NOT NULL
);


CREATE TABLE IF NOT EXISTS problem (
  id VARCHAR(40) PRIMARY KEY,
  oj_id VARCHAR(40) NOT NULL,
  spj SMALLINT NOT NULL,
  url VARCHAR(200) NOT NULL,
  submit_url VARCHAR(200) NOT NULL,
  title VARCHAR(100) NOT NULL,
  description TEXT NOT NULL,
  time_limit INTEGER NOT NULL,
  memory_limit INTEGER NOT NULL,
  input_description TEXT NOT NULL,
  output_desription TEXT NOT NULL,
  samples TEXT NOT NULL,
  is_valid SMALLINT DEFAULT 1 NOT NULL,
  /* 可能是分为正在爬取 爬取完成 爬取失败等状态 */
  status SMALLINT NOT NULL,
  FOREIGN KEY (oj_id) REFERENCES oj(id)
);


CREATE TABLE IF NOT EXISTS submission (
  id VARCHAR(40) PRIMARY KEY,
  problem_id VARCHAR(40) NOT NULL,
  result SMALLINT NOT NULL,
  cpu_time INTEGER,
  memory INTEGER,
  info TEXT,
  user_id VARCHAR(40) NOT NULL,
  FOREIGN KEY (problem_id) REFERENCES problem(id),
  FOREIGN KEY (user_id) REFERENCES robot_user(id)
);