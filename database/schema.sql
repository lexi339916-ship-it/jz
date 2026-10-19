-- 智能记账与生活便签一体化管理系统 —— MySQL 8.x 初始化脚本
-- 用法：mysql -u root -p < database/schema.sql
-- 说明：与 backend/app/models.py 保持一致；开发时后端也可用 SQLite 自动建表。

CREATE DATABASE IF NOT EXISTS smart_life CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE smart_life;

-- 用户表：密码只存 PBKDF2 哈希，不存明文
CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(50) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  nickname VARCHAR(50) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 收支分类表：user_id 为 NULL 表示系统预置分类；非空表示用户自定义
CREATE TABLE IF NOT EXISTS bill_categories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NULL,
  name VARCHAR(40) NOT NULL,
  type ENUM('income','expense') NOT NULL,
  UNIQUE KEY uq_category_user_name_type (user_id, name, type),
  CONSTRAINT fk_category_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- 账单表：source 标记数据来源（manual 手动 / ai 智能解析确认后保存），满足可追溯要求
CREATE TABLE IF NOT EXISTS bills (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  category_id BIGINT NULL,
  type ENUM('income','expense') NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  bill_date DATE NOT NULL,
  remark VARCHAR(200) NOT NULL DEFAULT '',
  source VARCHAR(10) NOT NULL DEFAULT 'manual',
  pay_channel VARCHAR(20) NOT NULL DEFAULT '',
  funding_account VARCHAR(40) NOT NULL DEFAULT '',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_bill_user_date (user_id, bill_date),
  CONSTRAINT fk_bill_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_bill_category FOREIGN KEY (category_id) REFERENCES bill_categories(id)
) ENGINE=InnoDB;

-- 便签与任务表：note_type 区分便签/待办；priority 优先级；pinned 置顶；due_at 截止时间
CREATE TABLE IF NOT EXISTS notes (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  title VARCHAR(100) NOT NULL,
  content TEXT,
  note_type ENUM('note','todo') NOT NULL DEFAULT 'note',
  status ENUM('open','done') NOT NULL DEFAULT 'open',
  due_at DATETIME NULL,
  priority VARCHAR(10) NOT NULL DEFAULT 'medium',
  pinned TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_note_user_status (user_id, status),
  CONSTRAINT fk_note_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- 月度预算表：每用户每月一条
CREATE TABLE IF NOT EXISTS budgets (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  month CHAR(7) NOT NULL,
  amount DECIMAL(12,2) NOT NULL,
  UNIQUE KEY uq_budget_user_month (user_id, month),
  CONSTRAINT fk_budget_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- AI 调用日志表：记录功能、提示词版本、模型、耗时与结果，满足可复现与审计要求
CREATE TABLE IF NOT EXISTS ai_call_logs (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  feature VARCHAR(30) NOT NULL,
  prompt_version VARCHAR(10) NOT NULL,
  model VARCHAR(60) NOT NULL,
  status VARCHAR(20) NOT NULL,
  latency_ms INT NOT NULL DEFAULT 0,
  error_msg VARCHAR(255) NOT NULL DEFAULT '',
  input_chars INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ai_log_user_date (user_id, created_at),
  CONSTRAINT fk_ai_log_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- 储蓄目标表：目标金额与已存入金额；预计完成时间由后端按月均结余计算
CREATE TABLE IF NOT EXISTS savings_goals (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  name VARCHAR(50) NOT NULL,
  target_amount DECIMAL(12,2) NOT NULL,
  saved_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_goal_user FOREIGN KEY (user_id) REFERENCES users(id)
) ENGINE=InnoDB;

-- 生活挑战表：周期内某分类支出不超过上限；进度与上期对比由后端统计
CREATE TABLE IF NOT EXISTS challenges (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  name VARCHAR(60) NOT NULL,
  category_id BIGINT NULL,
  period_days INT NOT NULL DEFAULT 7,
  target_amount DECIMAL(12,2) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_challenge_user FOREIGN KEY (user_id) REFERENCES users(id),
  CONSTRAINT fk_challenge_category FOREIGN KEY (category_id) REFERENCES bill_categories(id)
) ENGINE=InnoDB;

-- 系统预置分类（与后端 app/main.py 的 DEFAULT_CATEGORIES 一致）
INSERT INTO bill_categories(user_id, name, type) VALUES
  (NULL, '餐饮', 'expense'), (NULL, '交通', 'expense'), (NULL, '购物', 'expense'),
  (NULL, '住房', 'expense'), (NULL, '学习', 'expense'), (NULL, '娱乐', 'expense'),
  (NULL, '医疗', 'expense'), (NULL, '通讯', 'expense'), (NULL, '其他', 'expense'),
  (NULL, '工资', 'income'), (NULL, '兼职', 'income'), (NULL, '理财', 'income'),
  (NULL, '红包', 'income'), (NULL, '退款', 'income'), (NULL, '其他收入', 'income');
