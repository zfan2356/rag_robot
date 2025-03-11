USE rag_robot;

-- 创建提示词模板表
CREATE TABLE IF NOT EXISTS prompt_template_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    system_prompt TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    name VARCHAR(100) DEFAULT NULL,    -- 模板名称
    description VARCHAR(500) DEFAULT NULL, -- 模板描述
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建文档表
CREATE TABLE IF NOT EXISTS document_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    doc LONGTEXT NOT NULL,             -- 使用LONGTEXT存储大文本
    title VARCHAR(255) DEFAULT NULL,   -- 文档标题
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    INDEX idx_title (title)
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 添加提示词模板初始数据
INSERT INTO prompt_template_table (system_prompt, name, description) VALUES
('你是一个专业的AI助手，擅长回答各类问题。请保持友好和专业的态度，给出准确和有帮助的回答。', '默认助手模板', '通用对话场景的默认系统提示词'),
('你是一个专业的编程助手，擅长解决各种编程问题和代码优化。请提供清晰的代码示例和详细的解释。', '代码助手模板', '专门用于编程和代码相关问题的系统提示词');

-- 添加文档初始数据
INSERT INTO document_table (doc, title) VALUES
('# Python 快速入门指南\n\n## 1. 安装Python\n首先，从官方网站下载并安装Python。\n\n## 2. 基础语法\nPython使用缩进来表示代码块。', 'Python快速入门指南'),
('# RAG机器人产品说明书\n\n## 产品概述\nRAG机器人是一款基于检索增强生成技术的智能问答系统。\n\n## 主要功能\n1. 智能问答\n2. 文档管理', 'RAG机器人产品说明书');
