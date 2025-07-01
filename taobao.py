from selenium import webdriver  # 主浏览器控制模块
from selenium.webdriver.chrome.options import Options  # Chrome浏览器配置选项
from selenium.webdriver.chrome.service import Service  # ChromeDriver服务管理
from selenium.webdriver.common.by import By  # 元素定位策略
from selenium.webdriver.support.ui import WebDriverWait  # 帮助在浏览器加载网页时进行等待，直到某个条件满足再继续执行代码。
from selenium.webdriver.support import expected_conditions as EC  # 用于在 Selenium 中进行显式等待时判断网页元素是否满足某些条件。
import time  # 时间控制（等待/延迟）
import random  # 生成随机数（模拟人类操作）
import json  # 处理JSON格式的Cookie文件
import os  # 文件/路径操作
from itertools import product  # 生成输入可迭代对象的笛卡尔积，也就是所有输入集合的排列组合。
import pandas as pd  # 用于处理表格数据
import datetime  # 处理日期和时间的标准库
import re  # 用于处理正则表达式的标准库
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import numpy as np

class crawl_taobao:
    # 创建品牌列表
    brand = {'小米': ['小米15Ultra', '小米15Pro', '小米15'],
             'OPPO': ['一加13', 'OPPOFindX8'],
             '华为': ['华为mate70']}
    # 全局常量定义
    COOKIE_FILE = 'taobao_cookies.json'
    MAX_RETRIES = 3  # 最大重试次数
    RETRY_DELAY = 2  # 重试延迟（秒）

    # 保存当前会话的Cookie到文件
    def save_cookies(self,driver):
        # 获取浏览器所有Cookie（列表形式）
        cookies = driver.get_cookies()
        # 使用上下文管理器写入文件
        with open(self.COOKIE_FILE, 'w') as f:
            json.dump(cookies, f)  # 序列化Cookie到JSON文件
        print("Cookies已保存")

    # 从文件加载Cookie到浏览器
    def load_cookies(self,driver):
        # 读取本地Cookie文件
        with open(self.COOKIE_FILE, 'r') as f:
            cookies = json.load(f)  # 反序列化JSON数据
        # 必须先访问目标域名（淘宝主页），否则无法添加Cookie
        driver.get('https://www.taobao.com')
        # 遍历所有Cookie条目
        for cookie in cookies:
             if 'taobao.com' not in cookie['domain']:
                 cookie['domain'] = '.taobao.com'  # 统一设置为顶级域名
             try:
                 driver.add_cookie(cookie)  # 逐个添加Cookie到浏览器
             except Exception as e:
                # 处理无效Cookie（如过期或格式错误）
                print(f"跳过无效Cookie: {cookie['name']}")
        print("Cookies已加载")
        driver.refresh()  # 必须刷新页面使Cookie生效

    # 检查登录状态：通过查找登录按钮是否存在
    def is_logged_in(self,driver):
        try:
            # 尝试定位登录按钮元素（CSS选择器）
            driver.find_element(By.CSS_SELECTOR, 'div.site-nav-sign a.h')
            return False  # 找到元素 → 未登录状态
        except:
            return True  # 找不到元素 → 已登录状态

    # 模拟人类输入行为（避免被检测为机器人）
    def human_typing(self,element, text, typing_speed=0.1):
        for char in text:
            element.send_keys(char)  # 逐个字符输入
            # 随机延迟：基础0.1秒 + 0~0.2秒浮动
            time.sleep(random.uniform(typing_speed, typing_speed + 0.2))

    # 手动登录流程（首次使用或Cookie失效时调用）
    def manual_login(self,driver):
        # 打开淘宝主页
        driver.get('https://www.taobao.com')
        try:
            # 使用 WebDriverWait 等待，最长等待 10 秒，直到元素变得可点击
            login_button = WebDriverWait(driver, 10).until(
                # 定位到登录按钮，使用 CSS 选择器
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.site-nav-sign a.h')))
            # 如果元素可点击，则点击登录按钮
            login_button.click()
        except TimeoutException:
            # 如果在指定时间内无法找到登录按钮，抛出 TimeoutException 异常
            print("登录按钮未找到，尝试直接访问登录页")
            # 跳转到登录页面的 URL
            driver.get('https://login.taobao.com/')
        time.sleep(3)
        try:
            account_input_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'fm-login-id')))
            self.human_typing(account_input_element, '')
            time.sleep(2)
            password_input_element = driver.find_element(By.ID, "fm-login-password")
            self.human_typing(password_input_element, '')
            input("请手动完成登录，登录成功后按回车继续...")
            self.save_cookies(driver)
            print("手动登录成功")
        except TimeoutException:
            print("登录表单未加载，可能需要手动处理验证码")

    # 安全点击元素，处理可能的异常
    def safe_click(self,element):
        try:
            element.click()
            return True
        except Exception as e:
            print(f"点击元素失败: {e}")
            return False

    # 获取商品名称
    def get_product_name(self,driver):
        try:
            # 使用ID选择器
            title_element = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#tbpc-detail-item-title h1"))
            )
            # 获取商品名称文本
            product_name = title_element.text.replace(" ", "")
            product_name = self.replace_product_name(product_name, self.brand)
            print("商品名称:", product_name)
            return product_name
        except Exception as e:
            print("获取商品名称失败:", e)

    # 根据品牌字典替换商品名称
    def replace_product_name(self,text, brand_dict, case_insensitive=True):
        """
        根据品牌字典替换商品名称
        参数:
        text: 原始商品名称文本
        brand_dict: 品牌字典 {品牌: [商品名称1, 商品名称2, ...]}
        case_insensitive: 是否忽略大小写 (默认True)
        返回:
        匹配替换后的文本
        """
    # 遍历品牌字典的键（品牌名称）
        for brand, products in brand_dict.items():
            # 检查文本中是否包含当前品牌
            if re.search(brand, text):
                # 遍历该品牌下的所有产品名称
                for product in products:
                    # 检查文本中是否包含当前产品
                    if re.search(product, text):
                        # 匹配成功，返回产品名称
                        return product
        # 没有匹配到任何品牌或产品，返回原始文本
        return text

    # 获取商品规格信息
    def get_specifications(self,driver):
        specs = {}  # 创建一个空字典，用于存储商品规格信息
        try:
            # 使用WebDriverWait等待页面加载，直到找到所有包含"skuItem"的元素
            sku_items = WebDriverWait(driver, 15).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='skuItem']"))
            )
            # 遍历所有找到的商品规格项
            for item in sku_items:
                try:
                    # 查找包含"labelText"类的元素，获取规格标签
                    label = item.find_element(By.CSS_SELECTOR, "[class*='labelText']")
                    item_label = label.text
                    # 如果该标签不存在于字典中，则将其添加为新键，并初始化一个空列表
                    if item_label not in specs:
                        specs[item_label] = []
                    # 查找包含"valueItemText"类的元素，获取规格的值
                    values = item.find_elements(By.CSS_SELECTOR, "[class*='valueItemText']")
                    for value in values:
                        # 将每个值添加到对应标签的列表中
                        specs[item_label].append(value.text)
                except StaleElementReferenceException:
                    # 如果元素状态过期，打印提示并继续查找下一个元素
                    print("元素状态过期，重新查找...")
                    continue
                except Exception as e:
                    # 发生其他异常时，打印错误信息
                    print(f"获取规格时出错: {e}")
        except TimeoutException:
            # 如果超时未加载规格元素，打印超时错误信息
            print("规格元素加载超时")
        except Exception as e:
            # 发生其他异常时，打印错误信息
            print(f"获取规格时发生错误: {e}")
        return specs  # 返回存储商品规格信息的字典


    # 取消所有已选中的选项
    def deselect_all_options(self,driver):
        try:
            # 查找页面中所有符合指定CSS选择器（已选中的选项）的元素
            selected_items = driver.find_elements(By.CSS_SELECTOR, "[class*='isSelected']")
            # 遍历每一个已选中的选项
            for item in selected_items:
                try:
                    # 点击选中的项以取消选中
                    item.click()
                    # 等待0.5秒，确保点击动作完成并给页面一些时间更新状态
                    time.sleep(0.5)
                except Exception:
                    # 如果点击操作发生异常，跳过当前项，继续执行后续项
                    continue
        except Exception as e:
            # 如果在查找或操作过程中发生异常，捕获并打印错误信息
            print(f"取消选中选项时出错: {e}")


    # 判断该规格组合是否售罄
    def judge_is_sold_out(self,driver, combination):
        # 初始化一个变量，标记是否当前组合已经售罄
        sold_out = False
        # 遍历当前组合中的每个选项
        # option_value为每种规格组合的组成项
        for i, option_value in enumerate(combination):
            # 重试次数循环，最多尝试MAX_RETRIES次
            for attempt in range(self.MAX_RETRIES):
                try:
                    # 使用WebDriverWait等待选项元素可点击
                    option_element = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, f"//span[@title='{option_value}']"))
                    )
                    print(f"正在选择：{option_element.text}")
                    # 检查选项是否不可选（判断类名中是否含有 'isDisabled'）
                    disabled = self.get_disabled_options(driver)
                    for key, value in disabled.items():
                        if value == option_element.text:
                            print(f"选项 '{option_value}' 不可选（无货）")
                            sold_out = True
                            break
                            # 如果无货，跳出循环
                    if sold_out:
                        break
                    if self.safe_click(option_element):
                        print(f"已选择: {option_value}")
                        time.sleep(1.5)  # 等待价格更新
                        break
                    else:
                        print(f"点击选项 '{option_value}' 失败，重试 {attempt + 1}/{self.MAX_RETRIES}")
                        time.sleep(self.RETRY_DELAY)
                except TimeoutException:
                    print(f"选项 '{option_value}' 定位超时，重试 {attempt + 1}/{self.MAX_RETRIES}")
                    time.sleep(self.RETRY_DELAY)
                except Exception as e:
                    print(f"选择选项时出错: {e}")
                    time.sleep(self.RETRY_DELAY)
        return sold_out

    # 获取当前不可被选中的选项
    def get_disabled_options(self,driver):
        disabled = {}  # 创建一个空字典，用于存储当前不可被选中的选项
        try:
            # 等待直到页面上加载出所有具有指定CSS选择器的选中项（选中的元素）
            disabled_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='isDisabled']"))
            )
            # 遍历所有选中的选项
            for idx, item in enumerate(disabled_items, start=1):
                try:
                    # 获取每个选项的文本内容
                    option_text = item.text
                    # 将选项文本存入字典，键为"option"加上索引，值为选项的文本
                    disabled[f"option{idx}"] = option_text
                except StaleElementReferenceException:
                    # 捕获元素状态过期异常，表示元素已经更新或移除，跳过该元素
                    print("选中的元素状态过期，跳过")
                    continue
        except TimeoutException:
            # 如果在指定时间内没有找到任何选中的选项，则输出超时信息
            print("未找到选中的选项")
        # 返回包含所有选中项的字典
        return disabled

    # 获取当前价格
    def get_current_price(self,driver):
        # 重试多次以防获取价格时出现临时错误
        for _ in range(self.MAX_RETRIES):
            try:
                # 获取所有匹配的元素，这里是查找所有class属性包含 'esVfqSHIbS--highlightPrice' 的div元素
                all_price_divs = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[class*='highlightPrice']"
                )
                # 初始化变量，准备保存实际可见的价格div元素
                visible_price_div = None
                # 遍历所有找到的div元素，查找第一个可见的div元素
                for div in all_price_divs:
                    if div.is_displayed():  # 判断该div元素是否在页面上可见
                        visible_price_div = div  # 找到可见的div元素，保存到visible_price_div变量中
                        break  # 结束循环，找到第一个可见的元素后不再继续查找
                if visible_price_div:  # 如果找到了可见的div元素
                    # 在可见的div元素中找到包含价格的span元素
                    price_span = visible_price_div.find_element(
                        By.CSS_SELECTOR,
                        "span[class*='text']"
                    )
                    # 打印价格
                    print(f"价格: {price_span.text}")
                    # 获取并返回价格文本
                    price = price_span.text
                    return price  # 返回价格文本
            except (TimeoutException, NoSuchElementException):
                # 如果在指定时间内未找到价格元素或元素不存在，打印错误并重试
                print("价格元素未找到，重试中...")
                time.sleep(self.RETRY_DELAY)  # 等待一段时间后再重试
            except StaleElementReferenceException:
                # 如果元素失效或过期，打印错误并重试
                print("价格元素状态过期，重试中...")
                time.sleep(self.RETRY_DELAY)  # 等待一段时间后再重试
            except Exception as e:
                # 捕获其他异常，打印错误信息并重试
                print(f"获取价格时出错: {e}")
                time.sleep(self.RETRY_DELAY)  # 等待一段时间后再重试

    # 获取当前选中的选项(暂无用处)
    def get_selected_options(self,driver):
        selected = {}  # 创建一个空字典，用于存储当前选中的选项
        try:
            # 等待直到页面上加载出所有具有指定CSS选择器的选中项（选中的元素）
            selected_items = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='isSelected']"))
            )
            # 遍历所有选中的选项
            for idx, item in enumerate(selected_items, start=1):
                try:
                    # 获取每个选项的文本内容
                    option_text = item.text
                    # 将选项文本存入字典，键为"option"加上索引，值为选项的文本
                    selected[f"option{idx}"] = option_text
                except StaleElementReferenceException:
                    # 捕获元素状态过期异常，表示元素已经更新或移除，跳过该元素
                    print("选中的元素状态过期，跳过")
                    continue
        except TimeoutException:
            # 如果在指定时间内没有找到任何选中的选项，则输出超时信息
            print("未找到选中的选项")
        # 返回包含所有选中项的字典
        return selected


    # 创建一个复合键（商品名+规格）用于匹配现有数据和新数据
    def create_composite_key(self,row):
        name = str(row["商品名"]) if "商品名" in row else ""
        options = [str(row.get(f"option{i}", "")).strip() for i in range(1, 8)]
        return name + "_" + "_".join(options)

    # 主运行函数：初始化浏览器并管理登录状态
    def run(self):
        # ----------------- 浏览器配置 -----------------
        options = Options()  # 创建浏览器配置对象，用于设置启动选项
        options.add_argument("--no-sandbox")  # 禁用沙盒模式，增加兼容性，解决某些系统上的兼容问题
        options.add_argument("--disable-dev-shm-usage")  # 禁用开发者共享内存，提高容器环境中的稳定性
        options.add_argument("--disable-blink-features=AutomationControlled")  # 禁用 WebDriver 特征，避免浏览器被检测到是自动化测试工具
        options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 禁用浏览器控制台中显示自动化测试相关信息
        options.add_experimental_option('useAutomationExtension', False)  # 禁用 WebDriver 自动化扩展，进一步隐藏自动化痕迹
        options.add_argument("--window-size=1920,1080")  # 设置浏览器窗口的大小为 1920x1080
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )  # 设置自定义的用户代理，伪装成常见的浏览器请求
        # 使用配置好的选项启动 Chrome 浏览器
        driver = webdriver.Chrome(
            service=Service(r'D:\pycharm\PyCharm 2023.3.2\电商平台爬虫\chromedriver.exe'),  # 指定 chromedriver 的路径
            options=options  # 使用上面设置的浏览器选项
        )
        # 执行 Chrome DevTools 协议的命令，修改 navigator.webdriver 属性，避免被检测为自动化脚本
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                  get: () => false
                })
            """
        })
        if os.path.exists(self.COOKIE_FILE):
            self.load_cookies(driver)
            time.sleep(3)
            if self.is_logged_in(driver):
                print("Cookie登录成功！")
                return driver
        print("未检测到有效Cookie，执行手动登录...")
        self.manual_login(driver)
        return driver

    def crawl_product_data(self,driver, url, current_time):
        # 打印正在访问的商品页面
        print(f"正在访问商品页面: {url}")
        # 使用 WebDriver 访问商品页面
        driver.get(url)
        # 等待5秒，确保页面加载完成
        time.sleep(5)
        # 获取商品名称
        product_name = self.get_product_name(driver)
        # 打印商品名称
        print(f"商品名称: {product_name}")
        # 获取规格信息
        specifications = self.get_specifications(driver)
        # 打印商品规格信息
        print("商品规格:")
        # 遍历并打印所有规格项
        for key, values in specifications.items():
            print(f"  {key}: {', '.join(values)}")

        # 生成所有可能的规格组合
        all_combinations = list(product(*specifications.values()))
        # 打印组合数量
        print(f"共有 {len(all_combinations)} 种规格组合")
        # 等待5秒，确保操作稳定
        time.sleep(5)

        # 初始化结果存储列表
        results = []

        # 遍历所有规格组合，处理每个组合
        for idx, combination in enumerate(all_combinations, 1):
            # 打印当前处理的组合索引和内容，显示进度
            print(f"\n处理组合 {idx}/{len(all_combinations)}: {combination}")
            # 暂停1秒钟，避免过于频繁的操作
            time.sleep(1)

            # 取消所有已选中的选项
            self.deselect_all_options(driver)
            time.sleep(1)

            # 判断当前规格组合是否售罄
            sold_out = self.judge_is_sold_out(driver, combination)

            # 如果售罄，跳过当前组合并设定价格为99999
            price = 0
            if sold_out:
                print("该组合无货，跳过")
                price = 99999
            else:
                # 如果没有售罄，则获取当前价格
                str_price = self.get_current_price(driver)
                try:
                    # 尝试将字符串价格转为浮动类型
                    price = float(str_price)
                    print(f"当前价格为{price}")
                except ValueError:
                    # 如果转换失败，打印错误信息
                    print("无法将字符串转换为 float 类型")

            # 准备当前组合的结果行，存储为字典
            row = {
                "商品名": product_name,
                current_time: price
            }

            # 添加规格选项列
            # 遍历组合的每一项，填充 row 字典中的选项
            for i in range(1, 8):
                # 对于 1 到 7 的每个 i，将 combination[i - 1] 的值赋给 row 的选项列
                # 如果 combination 列表长度不足，则对应的选项列为空字符串
                row[f"option{i}"] = combination[i - 1] if i <= len(combination) else ""

            # 将当前组合的数据行添加到结果列表
            results.append(row)
        # 返回结果列表和当前时间
        return results


    def save_to_excel(self,data, current_time, filename="商品价格数据1.0.xlsx"):
        # 如果没有数据，打印提示信息并返回
        if not data:
            print("没有数据可保存")
            # 退出方法
            return

        # 将数据data转换为DataFrame格式，方便后续处理
        current_df = pd.DataFrame(data)

        # 如果Excel文件不存在，执行下面代码，直接保存当前数据
        if not os.path.exists(filename):
            # 为current_df创建最低价，并将当前时间价格数据赋值给最低价
            current_df['最低价'] = current_df[current_time]
            # 设置列的排序顺序，包括商品名、规格列、最低价和当前日期
            columns_order = ["商品名"] + [f"option{i}" for i in range(1, 8)] + ["最低价", current_time]
            current_df = current_df[columns_order]
            # 将DataFrame保存为Excel文件，不包含索引
            current_df.to_excel(filename, index=False)
            print(f"首次创建文件 {filename}，新增日期列: {current_time}")
            # 返回excel文件，退出方法
            return current_df

        # 如果文件已存在，读取历史数据
        history_df = pd.read_excel(filename)
        # 创建历史商品复合键集合
        unique_keys = set()
        # 转换历史数据中的规格列（商品名、option1~option7），将NaN值替换为空字符串
        for col in ["商品名"] + [f"option{i}" for i in range(1, 8)]:
            if col in history_df.columns:
                # 将history_df[col]中的NaN值替换为空字符串，并转换为字符串类型
                history_df[col] = history_df[col].fillna('').astype(str)
        # 确保所有规格列（如商品名、option1~option7）都是字符串类型，并将NaN值替换为空字符串
        for col in ["商品名"] + [f"option{i}" for i in range(1, 8)]:
            if col in current_df.columns:
                # 将NaN值替换为空字符串，并转换为字符串类型
                current_df[col] = current_df[col].fillna('').astype(str)
        # 为历史数据和当前数据都添加复合键
        history_df['composite_key'] = history_df.apply(self.create_composite_key, axis=1)
        current_df['composite_key'] = current_df.apply(self.create_composite_key, axis=1)
        # 获取所有历史规格组合-商品复合键集合
        for index, row in history_df.iterrows():
            unique_keys.add(row['composite_key'])
        # 创建current_time列，默认值为nan
        history_df[current_time] = np.nan
        for key in current_df['composite_key']:
            # 如果当前复合键存在于历史复合键集合当中
            if key in unique_keys:
                # 获取当前价格
                current_price = current_df.loc[current_df['composite_key'] == key, current_time].values[0]
                # 将当前时间价格更新至history_df当中
                history_df.loc[history_df['composite_key'] == key, current_time] = current_price
                # 获取历史最低价
                history_minimal = history_df.loc[history_df['composite_key'] == key, '最低价'].values[0]
                # 将历史最低价与当前价格进行比较，将较低值重新放入‘最低价’
                history_df.loc[history_df['composite_key'] == key, '最低价'] = min(current_price, history_minimal)
            # 如果当前复合键不存在于历史复合键集合当中（新商品-规格组合）
            else:
                # 获取当前价格
                current_price = current_df.loc[current_df['composite_key'] == key, current_time].values[0]
                # 为current_df创建最低价，并将当前时间价格数据赋值给最低价
                current_df.loc[current_df['composite_key'] == key, '最低价'] = current_price
                row = current_df.loc[current_df['composite_key'] == key]
                # 合并数据
                history_df = pd.concat([history_df, row], ignore_index=True, sort=False)
        history_df = history_df.drop('composite_key', axis=1)
        # 填充NAN
        history_df = history_df.fillna('').astype(str)

        history_df.to_excel(filename, index=False)
        print(f"数据已保存到 {filename}，新增日期列: {current_time}")
        return history_df


    def __init__(self,urls):
        # run()函数，初始化浏览器并管理登录状态
        driver = self.run()
        # 商品URL列表（可以扩展为多个商品），后续改为手动输入
        """
        product_urls = [
            "https://detail.tmall.com/item.htm?detail_redpacket_pop=true&id=838578575872&ltk2=1748999748256to6ker0wl8ho9r0ajle4s&ns=1&priceTId=214783a017489997401072458e19b0&query=%E4%B8%80%E5%8A%A013&skuId=5638282057369&spm=a21n57.1.hoverItem.1&utparam=%7B%22aplus_abtest%22%3A%22f65d29b40a1efcc6b9e3fb2efed9fbf8%22%7D&xxc=ad_ztc",
            "https://detail.tmall.com/item.htm?detail_redpacket_pop=true&id=837016600330&ltk2=1750340434854kdfgcjbtirm9lvobtj6hsa&ns=1&priceTId=undefined&query=%E5%B0%8F%E7%B1%B315&skuId=5817070737140&spm=a21n57.1.hoverItem.1&utparam=%7B%22aplus_abtest%22%3A%2251b198ce7e1b94486cc0d419fa889048%22%7D&xxc=ad_ztc",
            "https://detail.tmall.com/item.htm?abbucket=8&detail_redpacket_pop=true&id=838797496766&ltk2=1750525587323jpti6x5i7ybpz6zr1v4tk9&ns=1&priceTId=undefined&query=oppofindx8&skuId=5908423718166&spm=a21n57.1.hoverItem.4&utparam=%7B%22aplus_abtest%22%3A%22e02333496ae2973e29de53eed5c2865a%22%7D&xxc=taobaoSearch",
            "https://detail.tmall.com/item.htm?abbucket=8&detail_redpacket_pop=true&id=836591170125&ltk2=17505648608979d3i0x9o8yu96gaveh7ot&ns=1&priceTId=undefined&query=%E5%B0%8F%E7%B1%B315pro&skuId=5802049978332&spm=a21n57.1.hoverItem.4&utparam=%7B%22aplus_abtest%22%3A%220ace348a28444f00a42cdee845ff9adb%22%7D&xxc=taobaoSearch"
            ]
        """
        # 空列表，用于保存后续爬取的商品信息
        all_results = []
        # 获取当前时间，并格式化为年/月/日 时:分:秒
        current_time = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        # 遍历商品 URL 列表
        for url in urls:
            try:
                # crawl_product_data函数，爬取商品数据，并获取结果和日期
                results = self.crawl_product_data(driver, url, current_time)
                # 将爬取的商品数据添加到 all_results 列表中
                all_results.extend(results)
            except Exception as e:
                # 如果爬取过程中出现异常，打印错误信息
                print(f"爬取商品 {url} 时出错: {e}")

        # 如果成功获取了商品数据，则将数据保存到 Excel 文件
        if all_results:
            self.save_to_excel(all_results, current_time)
        else:
            # 如果没有获取到任何商品数据，打印提示信息
            print("未获取到任何商品数据")
        print("爬取完成")
