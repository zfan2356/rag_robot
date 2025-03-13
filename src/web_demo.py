import logging
import traceback
from typing import Generator

import gradio as gr

from src.config import ModelConfigManager
from src.llm.context import ContextManager
from src.llm.llm import LocalBaseLLM, RagRobotLLM
from src.llm.prompt import PromptManager

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROMPT_TEMPLATE_ID = 1
# 全局变量，存储RagRobotLLM实例
rag_robot_llm = None


def create_rag_robot_llm(template_id: int = 1) -> RagRobotLLM:
    """创建RagRobotLLM实例

    Args:
        template_id: 提示词模板ID，默认为1

    Returns:
        RagRobotLLM: RagRobotLLM实例
    """
    try:
        # 获取模型配置
        logger.info("正在获取模型配置...")
        model_config_manager = ModelConfigManager()
        model_config_manager.load()
        model_config = model_config_manager.get_model("llama3.2:latest")

        if not model_config:
            logger.error("未找到模型配置")
            raise ValueError("No model configuration found")

        logger.info(f"使用模型: {model_config.name}")

        # 创建LLM实例
        logger.info("正在创建LLM实例...")
        llm = LocalBaseLLM(model=model_config)

        # 创建提示词管理器
        logger.info("正在创建提示词管理器...")
        prompt_manager = PromptManager()

        # 创建上下文管理器
        logger.info(f"正在创建上下文管理器，使用模板ID: {PROMPT_TEMPLATE_ID}...")
        context_manager = ContextManager(
            prompt_manager=prompt_manager,
            template_id=PROMPT_TEMPLATE_ID,
            max_history_length=10,
        )

        # 创建RagRobotLLM实例
        logger.info("正在创建RagRobotLLM实例...")
        return RagRobotLLM(context_manager=context_manager, llm=llm)
    except Exception as e:
        logger.error(f"创建RagRobotLLM实例时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def stream_chat(message: str, history) -> Generator:
    """流式对话函数

    Args:
        message: 用户输入的消息
        history: 对话历史

    Returns:
        Generator: 生成器，用于流式返回响应
    """
    global rag_robot_llm
    try:
        logger.info(f"用户输入: {message}")
        partial_message = ""
        for chunk in rag_robot_llm.stream_generate(message):
            partial_message += chunk
            # 更新历史记录中最后一条消息的回复部分
            history[-1][1] = partial_message
            yield history
        logger.info(f"AI响应完成: {partial_message[:100]}...")
    except Exception as e:
        logger.error(f"流式对话时出错: {str(e)}")
        logger.error(traceback.format_exc())
        history[-1][1] = f"对话出错: {str(e)}"
        yield history


def clear_history():
    """清除对话历史

    Returns:
        list: 空的聊天历史列表
    """
    global rag_robot_llm
    try:
        logger.info("清除对话历史")
        rag_robot_llm.clear_history()
        return []
    except Exception as e:
        logger.error(f"清除对话历史时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def main():
    """主函数"""
    global rag_robot_llm
    try:
        logger.info("启动RAG Robot对话系统...")

        # 创建RagRobotLLM实例
        logger.info("正在创建RagRobotLLM实例...")
        rag_robot_llm = create_rag_robot_llm()

        # 创建Gradio界面
        logger.info("正在创建Gradio界面...")
        with gr.Blocks(title="RAG Robot 对话系统", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# RAG Robot 对话系统")
            gr.Markdown("这是一个基于RAG技术的对话系统，可以进行流式对话。")

            chatbot = gr.Chatbot(
                height=600,
                show_copy_button=True,
                # avatar_images=[(None, "👤"), (None, "🤖")],
                bubble_full_width=False,
            )

            with gr.Row():
                msg = gr.Textbox(
                    placeholder="请输入您的问题...",
                    container=False,
                    scale=9,
                    autofocus=True,
                )
                submit_btn = gr.Button("发送", scale=1, variant="primary")

            with gr.Row():
                clear_btn = gr.Button("清除对话历史")
                template_dropdown = gr.Dropdown(
                    label="选择提示词模板",
                    choices=["默认模板"],
                    value="默认模板",
                    interactive=True,
                )

            # 设置事件处理
            logger.info("正在设置事件处理...")
            submit_btn.click(
                fn=lambda message, history: ("", history + [[message, ""]]),
                inputs=[msg, chatbot],
                outputs=[msg, chatbot],
                queue=False,
            ).then(
                fn=stream_chat,
                inputs=[msg, chatbot],
                outputs=chatbot,
                queue=True,
            )

            msg.submit(
                fn=lambda message, history: ("", history + [[message, ""]]),
                inputs=[msg, chatbot],
                outputs=[msg, chatbot],
                queue=False,
            ).then(
                fn=stream_chat,
                inputs=[msg, chatbot],
                outputs=chatbot,
                queue=True,
            )

            clear_btn.click(
                fn=clear_history,
                inputs=[],
                outputs=chatbot,
                queue=False,
            )

        # 启动Gradio应用
        logger.info("正在启动Gradio应用...")
        demo.queue()
        demo.launch(server_name="0.0.0.0", share=False)
        logger.info("Gradio应用已启动")
    except Exception as e:
        logger.error(f"启动RAG Robot对话系统时出错: {str(e)}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
