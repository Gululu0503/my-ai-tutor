import os
import gradio as gr
import dashscope
from dashscope import Generation
from http import HTTPStatus

# ====== 1. 配置区域 ======
# 让助教用便宜快模型，教授用昂贵强模型
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "")

MODEL_TEACHER = "qwen-turbo"  # 助教模型：速度快
MODEL_PROFESSOR = "qwen-plus"  # 教授模型：能力强


# ====== 2. 教材加载 ======
def load_textbook(path="textbook.txt", max_chars=6000):
    if not os.path.exists(path):
        return "（未找到教材文件，将基于通用知识回答）"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()[:max_chars]


TEXTBOOK = load_textbook()


# ====== 3. 定义智能体类 (Agent Class) ======
class AI_Agent:
    def __init__(self, name, model_name, role_prompt):
        self.name = name
        self.model_name = model_name
        self.role_prompt = role_prompt

    def generate(self, user_content):
        """
        发送请求给 LLM
        """
        messages = [
            {"role": "system", "content": self.role_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            # 这里调用 DashScope API
            resp = Generation.call(
                model=self.model_name,
                messages=messages,
                result_format="message"
            )

            if resp.status_code == HTTPStatus.OK:
                return resp.output["choices"][0]["message"]["content"].strip()
            else:
                return f"Error: {resp.message}"
        except Exception as e:
            return f"Exception: {str(e)}"


# ====== 4. 初始化两个不同的智能体 ======

# 智能体 A：助教 (负责直接回答)
tutor_prompt = f"""
你是一名【实习助教】。
你需要根据以下教材内容回答学生的问题。
教材内容：
{TEXTBOOK}
要求：
1. 语言通俗易懂。
2. 如果教材没提到的内容，诚实说不知道。
"""
tutor_agent = AI_Agent("实习助教", MODEL_TEACHER, tutor_prompt)

# 智能体 B：严厉教授 (负责评分和补充)
professor_prompt = f"""
你是一名【严厉的教授】。
你的任务是审查“实习助教”给出的答案。
教材内容：
{TEXTBOOK}
请输出以下内容：
1. 【评分】：0-100分。
2. 【存在的问题】：指出助教回答中的错误或遗漏。
3. 【教授的补充】：如果助教说得不对，请你给出标准解释。
"""
critic_agent = AI_Agent("严厉教授", MODEL_PROFESSOR, professor_prompt)


# ====== 5. Gradio 交互逻辑 (双流输出) ======
def run_debate(question):
    if not question:
        yield "请输入问题", ""
        return

    # --- 第一步：助教回答 ---
    tutor_output = "🤖 助教正在翻阅教材思考中..."
    critic_output = "⏳ 等待助教提交答案..."
    yield tutor_output, critic_output

    # 获取助教的真实回复
    answer_content = tutor_agent.generate(question)
    tutor_output = answer_content  # 更新助教的内容
    critic_output = "👀 教授正在推眼镜，准备审查助教的答案..."
    yield tutor_output, critic_output

    # --- 第二步：教授评审 ---
    # 教授的输入包含：学生问题 + 助教的回答
    critic_input = f"学生的问题：{question}\n\n助教的回答：{answer_content}"

    review_content = critic_agent.generate(critic_input)
    critic_output = review_content

    # 完成
    yield tutor_output, critic_output


# ====== 6. 构建界面 ======
# 使用 Blocks 构建左右布局
with gr.Blocks(title="双师课堂：助教与教授") as demo:
    gr.Markdown("# 🎓 双模互动：助教答题 & 教授评分")
    gr.Markdown("本系统由两个独立的 AI 模型驱动。左侧是 `Qwen-Turbo` (实习助教)，右侧是 `Qwen-Plus` (严厉教授)。")

    with gr.Row():
        inp = gr.Textbox(placeholder="请输入问题...", label="学生提问", scale=4)
        btn = gr.Button("开始提问", variant="primary", scale=1)

    # 左右两栏布局
    with gr.Row():
        with gr.Column(variant="panel"):
            gr.Markdown("### 🧑‍🏫 实习助教 (快速回答)")
            out_tutor = gr.Markdown("等待提问...")

        with gr.Column(variant="panel"):
            gr.Markdown("### 👨‍🦳 严厉教授 (评分 & 补充)")
            out_critic = gr.Markdown("等待审查...")

    # 绑定事件
    btn.click(fn=run_debate, inputs=inp, outputs=[out_tutor, out_critic])

if __name__ == "__main__":
    demo.launch()
