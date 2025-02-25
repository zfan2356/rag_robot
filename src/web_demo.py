import concurrent.futures
import queue
from typing import Any, Dict, List, Tuple

import gradio as gr

from src.utils import process_stream_resp

executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)


def show_lang_info(language):
    info = {
        "Python": "1991年诞生,广泛用于Web开发和数据科学",
        "JavaScript": "浏览器脚本语言，支持前端开发",
        "Java": "跨平台的企业级应用语言",
    }
    return info.get(language, "未知语言")


def user(
    history: List[Dict[str, Any]],
    input_message: str,
) -> Tuple[List[Dict[str, Any]], str]:
    history.append(
        {
            "role": "user",
            "content": input_message,
        }
    )
    history.append(
        {
            "role": "assistant",
            "content": "",
        }
    )
    input_message = ""
    return history, input_message


def query_model_thread(
    q: queue.Queue,
    history: List[Dict[str, Any]],
    model_type: str,
):
    async def run():
        async for data in process_stream_resp(
            model_name=model_type, payload={"input": history}
        ):
            ...

    ...


def bot(model_type: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    q = queue.Queue()
    executor.submit(query_model_thread, q, history.copy(), model_type)


def launch_demo():
    with gr.Blocks(title="RAG BOT", fill_height=True) as demo:
        chatbot = gr.Chatbot(
            elem_id="chatbot",
            bubble_full_width=False,
            type="messages",
            scale=1,
        )
        dropdown = gr.Dropdown(
            choices=["Python", "JavaScript", "Java", "C++"],
            label="选择编程语言",
            interactive=True,
            filterable=True,  # 启用搜索过滤
        )
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(
                    label="INPUT QUESTION",
                    placeholder="input your questions...",
                    lines=1,
                    visible=True,
                    submit_btn=True,
                )
            with gr.Column():
                submit_btn = gr.Button("SUBMIT")
                reset_btn = gr.Button("CLEAR")

        # 输出组件
        output = gr.Textbox(label="语言信息")
        # 事件绑定
        dropdown.change(fn=show_lang_info, inputs=dropdown, outputs=output)

        components = [chatbot, text_input]

        submit_btn.click(
            user,
            [chatbot, text_input],
            [chatbot, text_input],
        ).then(bot, [dropdown, chatbot], [chatbot])

    demo.launch()


if __name__ == "__main__":
    launch_demo()
