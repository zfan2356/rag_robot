import logging
import threading
import time
import traceback
from typing import Dict, Generator, List, Optional, Tuple

import gradio as gr

from src.config import ModelConfigManager
from src.dao.documents import DocumentDAO
from src.llm.context import ContextManager
from src.llm.llm import LocalBaseLLM, RagRobotLLM
from src.llm.prompt import PromptManager
from src.rag.document_store import DocumentStore
from src.rag.rag_chain import RagChain
from src.rag.retriever import DocumentRetriever

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

rag_robot_llm = None
current_template = None
current_model = None
rag_chain = None


def get_all_templates() -> List[Dict]:
    """获取所有提示词模板

    Returns:
        List[Dict]: 模板列表
    """
    try:
        templates = PromptManager().list_templates()
        logger.debug(f"获取到 {len(templates)} 个提示词模板")
        return templates
    except Exception as e:
        logger.error(f"获取提示词模板时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def get_template_choices() -> Tuple[List[Tuple[str, str]], Optional[str]]:
    """获取提示词模板选项和默认选项

    Returns:
        Tuple[List[Tuple[str, str]], Optional[str]]: 模板选项列表和默认选项
    """
    templates = get_all_templates()
    if not templates:
        return [], None

    # 使用元组列表格式 [(显示文本, 值), ...]
    choices = [
        (
            f"{template['id']}: {template['name']}",
            f"{template['id']}: {template['name']}",
        )
        for template in templates
    ]

    # 找出ID最小的模板作为默认选项
    min_id_template = min(templates, key=lambda x: x["id"])
    default_choice = f"{min_id_template['id']}: {min_id_template['name']}"

    return choices, default_choice


def get_all_models() -> List[Dict]:
    """获取所有模型配置

    Returns:
        List[Dict]: 模型列表
    """
    try:
        model_config_manager = ModelConfigManager()
        model_config_manager.load()
        models = model_config_manager.models
        logger.debug(f"获取到 {len(models)} 个模型配置")
        return models
    except Exception as e:
        logger.error(f"获取模型配置时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def get_model_choices() -> Tuple[List[Tuple[str, str]], Optional[str]]:
    """获取模型选项和默认选项

    Returns:
        Tuple[List[Tuple[str, str]], Optional[str]]: 模型选项列表和默认选项
    """
    models = get_all_models()
    if not models:
        return [], None

    # 使用元组列表格式 [(显示文本, 值), ...]
    choices = [(model.name, model.name) for model in models]

    # 默认选择llama3.2模型，如果没有则选择第一个
    default_choice = next(
        (choice[0] for choice in choices if "llama3.2" in choice[0].lower()),
        choices[0][0] if choices else None,
    )

    return choices, default_choice


def create_rag_robot_llm(
    template_id: int = 1, model_name: str = "llama3.2:latest"
) -> RagRobotLLM:
    """创建RagRobotLLM实例

    Args:
        template_id: 提示词模板ID，默认为1
        model_name: 模型名称，默认为llama3.2:latest

    Returns:
        RagRobotLLM: RagRobotLLM实例
    """
    try:
        # 获取模型配置
        logger.info("正在获取模型配置...")
        model_config_manager = ModelConfigManager()
        model_config_manager.load()
        model_config = model_config_manager.get_model(model_name)

        if not model_config:
            logger.error(f"未找到模型配置: {model_name}")
            raise ValueError(f"No model configuration found for {model_name}")

        logger.info(f"使用模型: {model_config.name}")

        # 创建LLM实例
        logger.info("正在创建LLM实例...")
        llm = LocalBaseLLM(model=model_config)

        # 创建上下文管理器
        logger.info(f"正在创建上下文管理器，使用模板ID: {template_id}...")
        context_manager = ContextManager(
            prompt_manager=PromptManager(),
            template_id=template_id,
            max_history_length=10,
        )

        # 创建RagRobotLLM实例
        logger.info("正在创建RagRobotLLM实例...")
        return RagRobotLLM(context_manager=context_manager, llm=llm)
    except Exception as e:
        logger.error(f"创建RagRobotLLM实例时出错: {str(e)}")
        logger.error(traceback.format_exc())
        raise


def create_rag_chain(template_id: int = 1, model_name: str = "llama3.2:latest"):
    """创建RAG链"""
    retriever = DocumentRetriever(DocumentStore())
    rag_chain = RagChain(
        retriever=retriever, template_id=template_id, model_name=model_name
    )
    return rag_chain


def stream_chat(message: str, history, docs_retriever):
    """流式对话函数

    Args:
        message: 用户输入的消息
        history: 对话历史

    Returns:
        Generator: 生成器，用于流式返回响应
    """
    global rag_robot_llm, rag_chain
    try:
        logger.info(f"用户输入: {message}")

        # 生成响应
        partial_message = ""
        par_docs_message = ""
        ok = False
        for chunk in rag_chain.stream(message):
            if chunk == "[end]":
                ok = True
                continue
            if not ok:
                partial_message += chunk
                history[-1][1] = partial_message
                yield history, docs_retriever
            else:
                par_docs_message += chunk
                docs_retriever = par_docs_message
                yield history, docs_retriever

        logger.info(f"AI响应完成: {partial_message[:100]}...")
    except Exception as e:
        logger.error(f"流式对话时出错: {str(e)}")
        logger.error(traceback.format_exc())
        history[-1][1] = f"对话出错: {str(e)}"
        yield history, docs_retriever


def clear_history():
    """清除对话历史

    Returns:
        list: 空的聊天历史列表
    """
    global rag_robot_llm
    try:
        logger.info("清除对话历史")
        rag_robot_llm.clear_history()
        return [], ""
    except Exception as e:
        logger.error(f"清除对话历史时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return [], ""


def change_template(template_choice: str):
    """更改提示词模板

    Args:
        template_choice: 模板选项，格式为"id: name"

    Returns:
        list: 空的聊天历史列表，因为更换模板后需要清除历史
    """
    global rag_robot_llm, current_template, current_model
    try:
        if not template_choice or template_choice == current_template:
            return []

        # 从选项中提取模板ID
        template_id = int(template_choice.split(":")[0])
        logger.info(f"更改提示词模板为ID: {template_id}")

        # 更新RagRobotLLM实例的模板
        rag_robot_llm.context_manager.change_template(template_id)

        # 更新当前模板
        current_template = template_choice

        # 清除历史记录
        return []
    except Exception as e:
        logger.error(f"更改提示词模板时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def change_model(model_choice: str):
    """更改模型

    Args:
        model_choice: 模型选项，即模型名称

    Returns:
        list: 空的聊天历史列表，因为更换模型后需要清除历史
    """
    global rag_robot_llm, current_model, current_template
    try:
        if not model_choice or model_choice == current_model:
            return []

        # 更新当前模型
        logger.info(f"更改模型为: {model_choice}")

        # 提取当前模板ID
        template_id = 1
        if current_template and ":" in current_template:
            template_id = int(current_template.split(":")[0])

        # 重新创建RagRobotLLM实例
        rag_robot_llm = create_rag_robot_llm(
            template_id=template_id, model_name=model_choice
        )
        current_model = model_choice

        # 清除历史记录
        return []
    except Exception as e:
        logger.error(f"更改模型时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []


def update_template_dropdown():
    """更新模板下拉菜单"""
    templates = get_all_templates()
    choices = [
        (
            f"{template['id']}: {template['name']}",
            f"{template['id']}: {template['name']}",
        )
        for template in templates
    ]
    return gr.Dropdown(choices=choices)


def update_model_dropdown():
    """更新模型下拉菜单"""
    models = get_all_models()
    choices = [(model.name, model.name) for model in models]
    return gr.Dropdown(choices=choices)


def main():
    """主函数"""
    global rag_robot_llm, current_template, current_model, rag_chain
    try:
        logger.info("启动RAG Robot对话系统...")

        # 创建提示词管理器
        logger.info("正在创建提示词管理器...")

        # 获取初始模板选项
        template_choices, default_template = get_template_choices()
        current_template = default_template

        # 获取初始模型选项
        model_choices, default_model = get_model_choices()
        current_model = default_model

        # 创建RagRobotLLM实例，使用默认模板ID
        logger.info("正在创建RagRobotLLM实例...")
        default_template_id = (
            int(current_template.split(":")[0]) if current_template else 1
        )
        model_name = "llama3.2:latest"  # 默认模型
        if current_model:
            model_name = current_model
        rag_robot_llm = create_rag_robot_llm(
            template_id=default_template_id, model_name=model_name
        )
        rag_chain = create_rag_chain(
            template_id=default_template_id, model_name=model_name
        )

        # 创建Gradio界面
        logger.info("正在创建Gradio界面...")
        with gr.Blocks(title="RAG Robot 对话系统", theme=gr.themes.Soft()) as demo:
            gr.Markdown("# RAG Robot 对话系统")
            gr.Markdown("这是一个基于RAG技术的对话系统，可以进行流式对话。")

            # 添加模型和文档选择下拉菜单
            with gr.Row():
                template_dropdown = gr.Dropdown(
                    label="选择提示词模板",
                    choices=template_choices,
                    value=current_template,
                    interactive=True,
                )
                model_dropdown = gr.Dropdown(
                    label="选择模型",
                    choices=model_choices,
                    value=current_model,
                    interactive=True,
                    scale=1,
                )

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
                refresh_btn = gr.Button("刷新下拉菜单")

            with gr.Row():
                docs_retriever = gr.Markdown()

            # 设置事件处理
            logger.info("正在设置事件处理...")
            msg2 = gr.Textbox(visible=False)
            submit_btn.click(
                fn=lambda message, history: (
                    "",
                    history + [[message, ""]],
                    message,
                    "",
                ),
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, msg2, docs_retriever],
                queue=False,
            ).then(
                fn=stream_chat,
                inputs=[msg2, chatbot, docs_retriever],
                outputs=[chatbot, docs_retriever],
                queue=True,
            )

            msg.submit(
                fn=lambda message, history: (
                    "",
                    history + [[message, ""]],
                    message,
                    "",
                ),
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, msg2, docs_retriever],
                queue=False,
            ).then(
                fn=stream_chat,
                inputs=[msg2, chatbot, docs_retriever],
                outputs=[chatbot, docs_retriever],
                queue=True,
            )

            clear_btn.click(
                fn=clear_history,
                inputs=[],
                outputs=[chatbot, docs_retriever],
                queue=False,
            )

            # 添加模板选择事件处理
            template_dropdown.change(
                fn=change_template,
                inputs=[template_dropdown],
                outputs=[chatbot],
                queue=False,
            )

            # 添加模型选择事件处理
            model_dropdown.change(
                fn=change_model,
                inputs=[model_dropdown],
                outputs=[chatbot],
                queue=False,
            )

            # 添加刷新按钮事件处理
            refresh_btn.click(
                fn=update_template_dropdown,
                inputs=[],
                outputs=[template_dropdown],
                queue=False,
            ).then(
                fn=update_model_dropdown,
                inputs=[],
                outputs=[model_dropdown],
                queue=False,
            )

            # # 设置定时刷新
            # demo.load(
            #     fn=update_template_dropdown,
            #     inputs=[],
            #     outputs=[template_dropdown],
            #     every=0.1  # 每10秒刷新一次
            # )

            # demo.load(
            #     fn=update_model_dropdown,
            #     inputs=[],
            #     outputs=[model_dropdown],
            #     every=0.1  # 每10秒刷新一次
            # )

            # 在应用关闭时停止刷新管理器
            def on_close():
                logger.info("正在关闭RefreshManager...")

            demo.close = on_close

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
