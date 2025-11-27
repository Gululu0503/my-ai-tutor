import os
import dashscope
from dashscope import Generation
from http import HTTPStatus
import gradio as gr

# ====== 配置 ======
# 尝试从环境变量获取 Key，如果本地没有设置，请确保在 Vercel 面板设置环境变量
# 为了本地运行方便，你可以保留默认值，但在部署时一定要删除或使用环境变量
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "你的Key(本地测试用)")

MODEL_NAME = "qwen-plus"


# ====== 1. 读取教材 (带容错处理) ======
def load_textbook(path="textbook.txt", max_chars=6000):
    if not os.path.exists(path):
        return "（未找到教材文件，模型将基于通用知识回答。）"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[:max_chars]


TEXTBOOK = load_textbook()


# ====== 2. 通用模型调用函数 ======
def call_llm(messages):
    try:
        resp = Generation.call(
            model=MODEL_NAME,
            messages=messages,
            result_format="message"
        )
        if resp.status_code != HTTPStatus.OK:
            return f"[调用错误: {resp.code} - {resp.message}]"
        return resp.output["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"[系统异常: {str(e)}]"


# ====== 3. 智能体逻辑 (保持原逻辑不变) ======
def answer_agent(question):
    system_prompt = f"""
你是【问题回答者】。
你只能使用下面的教材内容回答问题，不允许胡编：
======== 教材内容 ========
{TEXTBOOK}
=========================
要求格式：
1. 直接回答（简短结论）
2. 详细讲解（分点）
3. 举例说明（与教材相关）
"""
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": question}]
    return call_llm(messages)


def checker_agent(question, draft):
    system_prompt = f"""
你是【答案检查者】，你的任务是审查回答者的初稿。
请基于教材内容进行检查：
======== 教材内容 ========
{TEXTBOOK}
=========================
输出格式固定为：
【错误与不足】
- ...
【修改建议】
- ...
【修订后的参考答案】
...
"""
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": f"学生问题：{question}\n\n回答者初稿：\n{draft}"}]
    return call_llm(messages)


def final_answer_agent(question, draft, review):
    system_prompt = f"""
你仍然是【问题回答者】。
你的任务：根据检查者的建议修订你的答案。
保留正确部分，修正错误，使最终答案更清晰、严谨。
下面是你需要参考的内容：
======== 回答者初稿 ========
{draft}
======== 检查者审查意见 ========
{review}
"""
    messages = [{"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请根据检查者意见，给出最终答案。"}]
    return call_llm(messages)


# ====== 4. Gradio 交互逻辑 (核心修改) ======
def process_pipeline(question):
    """
    这是一个生成器函数。
    它会分三次 yield (返回) 结果，分别对应界面的三个阶段更新。
    """
    if not question:
        yield "请输入问题", "", ""
        return

    # --- 阶段 1: 初稿 ---
    draft = "正在生成初稿，请稍候..."
    yield draft, "", ""  # 更新界面

    draft = answer_agent(question)
    yield draft, "正在等待检查者审查...", "等待中..."  # 初稿完成，预告下一阶段

    # --- 阶段 2: 检查 ---
    review = checker_agent(question, draft)
    yield draft, review, "正在根据意见修订最终答案..."  # 检查完成，预告下一阶段

    # --- 阶段 3: 终稿 ---
    final = final_answer_agent(question, draft, review)
    yield draft, review, final  # 全部完成


# ====== 5. 构建界面 ======
with gr.Blocks(title="AI 智能教学辅导系统") as demo:
    gr.Markdown("# 🤖 AI 智能教学辅导系统 (多智能体版)")

    with gr.Row():
        inp = gr.Textbox(placeholder="请输入学生的问题，例如：什么是光合作用？", label="学生问题", lines=2)
        btn = gr.Button("开始辅导", variant="primary")

    gr.Markdown("### 📝 分析过程")

    with gr.Row():
        out_draft = gr.Textbox(label="1. 回答者初稿", interactive=False, lines=10)
        out_check = gr.Textbox(label="2. 检查者意见", interactive=False, lines=10)
        out_final = gr.Textbox(label="3. 最终修订答案", interactive=False, lines=10)

    # 绑定事件
    btn.click(fn=process_pipeline, inputs=inp, outputs=[out_draft, out_check, out_final])

# 启动 (用于本地调试)
if __name__ == "__main__":
    demo.launch()