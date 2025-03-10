USE rag_robot;

-- 创建提示词模板表
CREATE TABLE IF NOT EXISTS prompt_templates (
    template_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description VARCHAR(500),
    template_content TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 可以添加其他表
-- CREATE TABLE IF NOT EXISTS other_table (...);

-- 可以添加一些初始数据
INSERT INTO prompt_templates (template_id, name, description, template_content)
VALUES (
    'default',
    '默认对话模板',
    '通用对话模板',
    '[["system", "你是一个专业的AI助手，擅长回答各类问题。"], ["human", "{input}"], ["placeholder", "{chat_history}"]]'
) ON DUPLICATE KEY UPDATE template_id=template_id;
