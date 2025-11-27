from main import demo
import os

# Vercel 将寻找 app 变量作为入口
app = demo.app

# 确保 API Key 存在 (这是为了安全检查)
if __name__ == "__main__":
    demo.launch()