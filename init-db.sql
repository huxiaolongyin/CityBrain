-- 创建城市大脑应用数据库
-- CREATE DATABASE city_brain;
-- 创建设备管理用户
CREATE USER city_brain
WITH
    PASSWORD 'city_brain123';

GRANT ALL PRIVILEGES ON DATABASE city_brain TO city_brain;

-- 创建airflow调度数据库
CREATE DATABASE airflow;

-- 创建设备管理用户
CREATE USER airflow
WITH
    PASSWORD 'airflow@1313123';

GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- 创建采集数据库
CREATE DATABASE ods;

-- 创建指标数据库
CREATE DATABASE ads;