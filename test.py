from tkinter import *
from tkinter.ttk import *

class Window:
    def __init__(self):
        self.win = Tk()
        self.create()

    def close(self, event=None):
        self.win.destroy()

    def create(self):
        self.win.title('破译单表加密密文')
        self.win.geometry("1000x800")
        self.win.minsize(600, 400)

        # 主容器分为上下两部分
        main_container = Frame(self.win)
        main_container.pack(fill=BOTH, expand=True)

        # 上半部分容器（占1/3高度）
        top_container = Frame(main_container)
        top_container.pack(fill=BOTH, expand=False, pady=10)  # 上半部分容器

        # 下半部分容器（占2/3高度）
        bottom_container = Frame(main_container)
        bottom_container.pack(fill=BOTH, expand=True)  # 下半部分容器

        # 配置上半部分网格布局（1行2列）
        top_container.grid_columnconfigure(0, weight=1)  # 左列1/3
        top_container.grid_columnconfigure(1, weight=2)  # 右列2/3
        top_container.grid_rowconfigure(0, weight=1)

        # 左侧标签
        left_label = Label(top_container, 
                         text="右侧为当前密文", 
                         font=("Arial", 12),
                         anchor=CENTER)
        left_label.grid(row=0, column=0, sticky="nsew")

        # 右侧文本区域容器
        text_frame = Frame(top_container)
        text_frame.grid(row=0, column=1, sticky="nsew")

        # 配置文本区域内部布局
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)

        # 创建文本组件
        self.text = Text(text_frame, wrap=WORD)
        self.text.grid(row=0, column=0, sticky="nsew")

        # 创建滚动条
        scrollbar = Scrollbar(text_frame, command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.config(yscrollcommand=scrollbar.set)

        # 底部容器示例内容)

        # 绑定关闭事件
        self.win.bind('<Escape>', self.close)

# 创建并启动窗口
window = Window()
window.win.mainloop()
