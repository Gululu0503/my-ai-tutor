# 这是模拟后端，等组长写好真的逻辑后，直接覆盖这个文件即可
import time


def run_collaboration(question):
    """
    文档规定的接口：
    输入：question (str)
    输出：draft (str), review (str), final (str)
    """

    # 模拟网络延迟
    time.sleep(1)

    # 模拟 A同学生成的初稿
    draft = f"""
    【模拟初稿】关于“{question}”：
    根据教材，这是一个重要的概念。它是指......(此处省略 A同学生成的 500 字)
    """

    # 模拟 B同学的检查意见
    review = """
    【检查意见】：
    1. 第一点概念解释有误。
    2. 缺少具体案例。
    建议：补充实际应用场景。
    """

    # 模拟 C同学生成的最终答案
    final = f"""
    【最终精修答案】
    关于 {question}，我们可以这样理解：

    1. 核心定义：......
    2. 详细解析：......

    (这是经过润色后的完美答案)
    """

    return draft, review, final