import taobao  # 导入taobao模块
import sys  # 导入sys模块，提供访问Python解释器使用的系统参数和函数
import os  # 导入os模块，提供与操作系统进行交互的功能，如文件路径、环境变量等
import threading  # 导入threading模块，支持多线程编程
import datetime  # 导入datetime模块，用于处理日期和时间
from PyQt6.QtWidgets import (  # 从PyQt6.QtWidgets导入一些常用的GUI组件
    QApplication,  # 创建应用程序对象
    QMainWindow,  # 创建主窗口
    QWidget,  # 基础的窗口控件
    QVBoxLayout,  # 垂直布局管理器
    QHBoxLayout,  # 水平布局管理器
    QLabel,  # 标签控件
    QLineEdit,  # 单行文本框
    QPushButton,  # 按钮控件
    QTextEdit,  # 多行文本框
    QTabWidget,  # 标签控件，通常用于多标签界面的布局
    QListWidget,  # 列表控件
    QSplitter,  # 用于分割窗口区域的控件
    QMessageBox  # 消息对话框
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject  # Qt用于控制界面元素的行为，pyqtSignal用于自定义信号，QObject是PyQt中所有对象的基类
from PyQt6.QtGui import QFont, QTextCursor  # 从PyQt6.QtGui导入QFont、QTextCursor等，用于控制字体和文本游标
from urllib.parse import urlparse  # 从urllib.parse导入urlparse函数，用于解析URL

# 成功爬取链接历史记录文件
success_crawl_urls = 'success_crawl_urls'


# 创建一个继承自QObject的Stream类
"""
整体工作流程：
1.程序执行print语句 →
2.调用sys.stdout.write() →
3.Stream.write()捕获输出 →
4.发射newText信号携带文本 →
5.update_console槽函数被触发 →
6.在GUI文本框末尾插入文本并滚动显示
"""
class Stream(QObject):
    # 定义一个信号newText，信号类型为字符串
    newText = pyqtSignal(str)

    # 核心功能：重写Python标准输出流的write方法
    # 工作流程：
    # 当Python执行print()或sys.stdout.write()时调用此方法
    # 将接收的文本转换为字符串（确保非字符串类型也能处理）
    # 发射newText信号并携带文本内容
    def write(self, text):
        # 将接收到的文本作为信号发射出去，其他对象可以连接到这个信号并响应
        self.newText.emit(str(text))

    # 定义flush方法，暂时不执行任何操作
    def flush(self):
        # 在这里通常会实现清空缓冲区等操作，但此方法目前为空
        pass


# 保存爬取成功的URL到历史文件中
def save_success_crawl_url(url):
    # 以追加模式 ('a') 打开文件success_crawl_urls，如果文件不存在则创建文件
    with open(success_crawl_urls, 'a') as f:
        # 将传入的url添加到文件中，每个URL后面加上换行符
        f.write(url + "\n")
    # 打印提示信息，表示URL已经保存
    print("urls已保存")


# 加载历史成功爬取的URL文件
def load_success_crawl_url(file_name):
    try:
        # 尝试打开指定的文件file_name，使用只读模式 ('r')
        with open(file_name, 'r') as f:
            # 使用列表推导式读取文件中的每一行，并去掉行末的换行符
            # strip()方法移除每行开头和结尾的空白字符（包括换行符）
            return [line.strip() for line in f]
    except FileNotFoundError:
        # 如果文件不存在，捕获FileNotFoundError异常并返回空列表
        return []
    except Exception as e:
        # 如果发生其他任何异常，打印错误信息
        print(f"Error reading file: {e}")
        return []


# 过滤非淘宝/天猫链接
def filter_taobao_urls(url):
    # 淘宝和天猫的域名集合，用于检查URL是否属于这两个站点
    TAOBAO_DOMAINS = {'tmall.com', 'taobao.com'}
    # 定义有效商品详情页的域名和路径匹配规则
    VALID_DETAIL_PAGES = {
        'item.taobao.com': '/item.htm',  # 淘宝商品详情页路径
        'detail.tmall.com': '/item.htm'  # 天猫商品详情页路径
    }
    try:
        # 使用urlparse解析URL，解析出域名、路径等信息
        parsed = urlparse(url)
        domain = parsed.netloc.lower()  # 获取域名并转为小写，便于匹配

        # 检查URL的域名是否属于淘宝或天猫
        if not any(domain.endswith(taobao_domain) for taobao_domain in TAOBAO_DOMAINS):
            # 如果不是淘宝/天猫的域名，打印过滤信息并跳过该URL,return False
            # print(f"过滤非淘宝链接: {url}")
            return False
        # 检查是否为有效的商品详情页
        for valid_domain, valid_path in VALID_DETAIL_PAGES.items():
            # 如果URL域名匹配且路径为有效的商品详情页路径，return True
            if valid_domain in domain and parsed.path == valid_path:
                return True
        # 如果不是有效的商品详情页，打印过滤信息，return False
        # print(f"过滤非商品详情页链接: {url} (域名: {domain}, 路径: {parsed.path})")
        return False
    except Exception as e:
        # 捕获并打印URL解析错误的异常信息,return False
        print(f"URL解析错误: {url} - {str(e)}")
        return False


class CrawlerUI(QMainWindow):
    def __init__(self):
        # 调用父类QMainWindow的构造函数初始化
        super().__init__()
        # 初始化UI界面
        self.initUI()
        # 初始化爬虫线程为None，后续可以用来启动和控制线程
        self.crawler_thread = None
        # 设置爬虫是否运行的标志，初始时设置为False
        self.running = False
        # 将Python的sys.stdout替换为自定义Stream实例
        # 创建Stream对象时绑定信号处理函数
        # newText信号自动连接到update_console方法
        sys.stdout = Stream(newText=self.update_console)

    # 实时输入验证
    def validate_input(self, text):
        # 分割输入的文本，按逗号分隔，去除每个网址的前后空白字符
        # 只有非空的网址会被保留在列表中
        urls = [url.strip() for url in text.split(',') if url.strip()]
        # 如果没有输入有效的网址（即列表为空），清除验证信息
        if not urls:
            self.validation_label.setText("")  # 清空验证标签的文本
            # 设置输入框的样式为默认状态
            self.url_input.setStyleSheet(
                "background-color: #34495e;"  # 背景颜色
                "color: #ecf0f1;"  # 字体颜色
                "border: 2px solid #3498db;"  # 边框颜色
                "border-radius: 5px;"  # 边框圆角
                "padding: 8px;"  # 内边距
            )
            return  # 结束函数，不继续执行后续代码
        # 初始化错误信息和有效网址列表
        correct_url = 0  # 计数有效的网址数量
        wrong_url = 0  # 计数无效的网址数量
        # 遍历每个输入的网址
        for url in urls:
            # 调用filter_taobao_urls函数验证网址是否有效
            signal = filter_taobao_urls(url)
            if signal:  # 如果网址有效
                correct_url += 1  # 增加有效网址计数
            else:  # 如果网址无效
                wrong_url += 1  # 增加无效网址计数
        # 构建错误信息字符串，显示总链接数、有效链接数和无效链接数
        error = f"总链接数为{len(urls)},已识别到{correct_url}个链接,未识别{wrong_url}个链接"
        # 在验证标签上显示错误信息
        self.validation_label.setText(error)
        # 如果输入链接全部有效
        if correct_url == len(urls):
            # 设置验证标签的样式，使用绿色字体和加粗
            self.validation_label.setStyleSheet("color: #2ecc71; font-weight: bold;")
            # 设置输入框的样式，显示提示
            self.url_input.setStyleSheet(
                "background-color: #34495e;"
                "color: #ecf0f1;"
                "border: 2px solid #2ecc71;"
                "border-radius: 5px;"
                "padding: 8px;"
            )
        else:
            # 设置验证标签的样式，使用红色字体和加粗
            self.validation_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
            # 设置输入框的样式，显示错误提示
            self.url_input.setStyleSheet(
                "background-color: #34495e;"  # 背景颜色
                "color: #ecf0f1;"  # 字体颜色
                "border: 2px solid #e74c3c;"  # 红色边框
                "border-radius: 5px;"  # 边框圆角
                "padding: 8px;"  # 内边距
            )

    def initUI(self):
        # 设置窗口标题为 '淘宝手机价格查询'
        self.setWindowTitle('淘宝手机价格查询')
        # 设置窗口的初始位置和大小，位置为 (300, 300)，宽度为 1000，高度为 700
        self.setGeometry(300, 300, 1000, 700)
        # 创建一个 QWidget 作为主部件，用于承载界面元素
        central_widget = QWidget()
        # 设置刚创建的 QWidget 为主窗口的中心部件
        self.setCentralWidget(central_widget)
        # 创建一个垂直布局 (QVBoxLayout)，并将其设置为中央部件的布局管理器
        main_layout = QVBoxLayout(central_widget)
        # 设置布局管理器中的组件之间的间隔为 10 像素
        main_layout.setSpacing(10)

        # 输入区域
        input_layout = QHBoxLayout()  # 创建一个水平布局，用于排列输入框和按钮
        # 创建标签，显示“商品链接:”
        url_label = QLabel('商品链接:')
        url_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))  # 设置标签的字体为 Arial，大小为 10，加粗
        # 创建一个 QLineEdit 输入框，供用户输入商品链接
        self.url_input = QLineEdit()
        # 设置输入框的提示文本，当没有输入内容时会显示提示
        self.url_input.setPlaceholderText('输入商品链接（多个链接用逗号分隔）')
        # 设置输入框的最小高度为 25 像素
        self.url_input.setMinimumHeight(25)
        # 将输入框的 textChanged 信号与验证输入的槽函数 connect，实时检查输入的内容
        self.url_input.textChanged.connect(self.validate_input)
        # 创建一个按钮，显示“开始爬取”
        self.start_button = QPushButton('开始爬取')
        # 设置按钮的固定大小为 100x35 像素
        self.start_button.setFixedSize(100, 35)
        # 设置按钮的样式表，定义按钮的外观及状态样式
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;  # 正常状态下按钮的背景色为绿色
                color: white;  # 字体颜色为白色
                border-radius: 5px;  # 设置按钮的圆角为5px
                font-weight: bold;  # 设置字体为加粗
            }
            QPushButton:hover {
                background-color: #45a049;  # 当鼠标悬停时，按钮的背景色变为较深的绿色
            }
            QPushButton:disabled {
                background-color: #cccccc;  # 当按钮不可用时，背景色变为灰色
            }
        """)
        # 将按钮的点击事件与 start_crawling 函数连接，点击按钮时启动爬取
        self.start_button.clicked.connect(self.start_crawling)
        # 将标签、输入框和按钮添加到布局中，设置输入框占用 5 份空间，按钮占用 1 份空间
        input_layout.addWidget(url_label)
        input_layout.addWidget(self.url_input, 5)
        input_layout.addWidget(self.start_button, 1)

        # 验证信息标签，用于显示提示信息或验证结果
        self.validation_label = QLabel("")  # 创建一个空的标签控件
        self.validation_label.setFont(QFont("Arial", 8))  # 设置标签的字体为 Arial，大小为 8
        self.validation_label.setWordWrap(True)  # 允许文本换行，避免超出标签边界
        self.validation_label.setMinimumHeight(10)  # 设置最小高度，防止布局调整时标签高度变化导致界面抖动

        # 标签页区域，用于创建并管理不同的标签页
        self.tab_widget = QTabWidget()  # 创建一个标签页控件
        self.tab_widget.setFont(QFont('Arial', 9))  # 设置标签页字体为 Arial，大小为 9
        # 控制台输出标签页
        console_tab = QWidget()  # 创建一个新的标签页控件
        console_layout = QVBoxLayout(console_tab)  # 创建一个垂直布局，并将其设置为控制台标签页的布局
        console_label = QLabel('爬虫控制台输出:')  # 创建一个标签，用于显示控制台的标题
        console_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))  # 设置标签字体为 Arial，大小为 10，加粗
        # 创建一个只读文本框，显示爬虫的控制台输出
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)  # 设置文本框为只读模式，防止用户编辑
        self.console_output.setFont(QFont('Consolas', 9))  # 设置文本框字体为 Consolas，大小为 9
        # 设置文本框的样式，背景为深色，文字为浅色，并添加边框和圆角效果
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;  # 深色背景
                color: #d4d4d4;  # 浅色文字
                border: 1px solid #3c3c3c;  # 边框颜色为深灰色
                border-radius: 4px;  # 设置圆角边框
            }
        """)
        # 将控件添加到布局中
        console_layout.addWidget(console_label)  # 添加标签
        console_layout.addWidget(self.console_output)  # 添加只读文本框

        # 爬取链接标签页，用于显示成功爬取的链接列表
        links_tab = QWidget()  # 创建一个新的标签页控件
        links_layout = QVBoxLayout(links_tab)  # 创建一个垂直布局，并将其设置为链接标签页的布局
        # 创建一个标签，用于显示链接列表的标题
        links_label = QLabel('成功爬取的链接:')
        links_label.setFont(QFont('Arial', 10, QFont.Weight.Bold))  # 设置标签字体为 Arial，大小为 10，加粗
        # 创建一个列表控件，用于显示爬取的链接
        self.crawled_links = QListWidget()
        self.crawled_links.setFont(QFont('Arial', 9))  # 设置列表控件字体为 Arial，大小为 9
        # 设置列表控件的样式，背景为浅色，边框为浅灰色，添加圆角效果
        self.crawled_links.setStyleSheet("""
            QListWidget {
                background-color: #f8f8f8;  # 浅色背景
                border: 1px solid #cccccc;  # 浅灰色边框
                border-radius: 4px;  # 设置圆角边框
            }
        """)
        # 加载历史爬取链接，urls为列表形式
        urls = load_success_crawl_url(success_crawl_urls)
        # 如果urls为非空列表
        if urls:
            # 循环取出每个链接
            for url in urls:
                # 添加至成功爬取的链接
                self.crawled_links.addItem(url)
        # 将控件添加到布局中
        links_layout.addWidget(links_label)  # 添加标题标签
        links_layout.addWidget(self.crawled_links)  # 添加链接列表控件
        # 添加标签页，将控制台输出标签页和爬取链接标签页添加到标签控件中
        self.tab_widget.addTab(console_tab, "控制台输出")  # 添加控制台输出标签页，并设置其名称为“控制台输出”
        self.tab_widget.addTab(links_tab, "爬取链接")  # 添加爬取链接标签页，并设置其名称为“爬取链接”

        # 底部状态栏，显示程序的当前状态信息
        self.status_bar = self.statusBar()  # 获取底部状态栏控件
        self.status_bar.setFont(QFont('Arial', 9))  # 设置状态栏字体为 Arial，大小为 9
        # 设置程序启动时初始状态，更新状态栏显示信息
        self.update_status("就绪 - 等待输入链接")  # 设置状态栏文本为“就绪 - 等待输入链接”

        # 将控件添加到主布局中
        main_layout.addLayout(input_layout)  # 将输入布局添加到主布局
        main_layout.addWidget(self.validation_label)  # 添加验证标签到主布局
        main_layout.addWidget(self.tab_widget)  # 将标签控件添加到主布局

    # 更新控制台输出
    def update_console(self, text):
        # 将光标移动到文本框的末尾，以便插入新的文本
        self.console_output.moveCursor(QTextCursor.MoveOperation.End)
        # 在控制台文本框中插入新的文本
        self.console_output.insertPlainText(text)
        # 确保光标位置可见，滚动到最新的文本位置
        self.console_output.ensureCursorVisible()

    # 为状态栏添加信息
    def update_status(self, message):
        # 获取当前时间并将其格式化为时:分:秒形式
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        # 在状态栏显示消息，消息格式为 [时间戳] 消息内容
        self.status_bar.showMessage(f"[{timestamp}] {message}")

    # 开始爬取按钮点击事件
    def start_crawling(self):
        # 检查爬虫是否正在运行，如果正在运行，更新状态并返回
        if self.running:
            self.update_status("爬虫已在运行中...")  # 更新状态栏显示爬虫正在运行
            return
        # 获取用户输入的商品链接并去除前后空格
        content = self.url_input.text().strip()
        # 如果没有输入链接，弹出警告框提醒用户
        if not content:
            QMessageBox.warning(self, "输入错误", "请输入商品链接！")
            return
        # 分割多个链接并去除每个链接的两端空白字符，只保留有效的链接
        url_list = [url.strip() for url in content.split(',') if url.strip()]
        valid_urls = []
        # 遍历每个链接，检查是否为有效的淘宝网址
        for url in url_list:
            signal = filter_taobao_urls(url)  # 调用函数过滤有效的淘宝链接
            if signal:
                valid_urls.append(url)
        # 如果没有有效链接，弹出警告框提醒用户
        if not valid_urls:
            QMessageBox.warning(self, "输入错误", "无有效淘宝网址")
            return
        # 更新状态栏，显示正在开始爬取链接的信息
        self.update_status(f"开始爬取 {len(valid_urls)} 个商品链接...")
        self.running = True  # 设置爬虫运行状态为 True
        self.start_button.setEnabled(False)  # 禁用开始按钮，避免重复点击
        self.start_button.setText("运行中...")  # 更新按钮文字，提示爬虫正在运行
        # 启动一个新的线程来运行爬虫，确保爬虫操作不会阻塞主线程
        self.crawler_thread = threading.Thread(
            target=self.run_crawler,  # 线程执行的目标函数
            args=(valid_urls,),  # 将有效链接作为参数传递给目标函数
            daemon=True  # 设置线程为守护线程，程序退出时线程会自动结束
        )
        self.crawler_thread.start()  # 启动线程

    def run_crawler(self, urls):
        """运行爬虫程序"""
        try:
            print(f"开始爬取 {len(urls)} 个链接...")
            taobao.crawl_taobao(urls)
            print("爬取完成！")

            # 在主线程更新UI
            self.url_input.setText("")  # 清空输入框
            self.validation_label.setText("")  # 清空验证信息

            # 添加爬取成功的链接
            for url in urls:
                # 保存成功的链接
                save_success_crawl_url(url)

        except Exception as e:
            print(f"爬虫运行出错: {str(e)}")
        finally:
            self.running = False
            # 在主线程更新UI
            self.start_button.setEnabled(True)
            self.start_button.setText("开始爬取")
            self.update_status("爬取任务完成")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.running:
            reply = QMessageBox.question(
                self, '确认关闭',
                '爬虫仍在运行中，确定要关闭吗？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # 恢复标准输出
        sys.stdout = sys.__stdout__
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    font = QFont("Arial", 10)
    app.setFont(font)

    window = CrawlerUI()
    window.show()
    sys.exit(app.exec())
