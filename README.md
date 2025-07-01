# Taobao Price Crawler 🕷️

基于 Selenium 和 PyQt6 开发的淘宝商品价格爬虫，支持自动化登录、商品价格抓取及数据保存功能。

## ✨ 功能特性

- 淘宝网站自动化登录
- 指定商品链接价格爬取
- 基于登录账号的实时到手价抓取
- 数据保存为结构化文件（CSV/Excel）
- PyQt6 图形化操作界面

## ⚙️ 环境依赖

```python
# 安装必需库
pip install selenium pandas numpy pyqt6 urllib3
```

## 📦 安装步骤

### 1. 浏览器驱动配置

1. 下载与您 Chrome 浏览器版本匹配的 [ChromeDriver](https://chromedriver.chromium.org/)
2. 将 `chromedriver.exe` 放置在项目根目录
3. 修改 `taobao.py` 第 361 行路径指向驱动文件：

```python
# 示例路径（根据实际位置修改）
 service=Service(r'D:\chromedriver.exe'),  # 指定 chromedriver 的路径
```

> 🔍 驱动版本匹配教程：[谷歌浏览器驱动下载指南](https://blog.csdn.net/nings666/article/details/134314452)

### 2. 账号配置

首次运行时：

```python
# taobao.py 第 92/95 行（可选）
self.human_typing(account_input_element, '您的账号')  # 第 92 行
self.human_typing(password_input_element, ‘您的密码’)     # 第 95 行
```

> ⚠️ 建议手动登录（账号密码填写在代码中不安全）

## 🚀 使用指南

1. **运行程序**

    ```python
     pyqt6.py
    ```
2. **将商品详情页链接粘贴至链接输入框**

    ![image](assets/image-20250701133623-c02h817.png)
3. **点击开始爬取按钮**
4. **登录操作**

    - 首次运行需手动登录淘宝账号
    - 登录成功后控制台按 `Enter` 继续爬取
5. **数据输出**
    爬取结果自动保存到当前路径下“商品价格数据1.0.xlsx”（默认路径）

## ⚠️ 注意事项

1. **价格说明**
    商品价格基于登录账号的优惠券/红包计算，不同账号价格可能不同
2. **商品名称规范**

    - 不同活动期间商品名称可能变化
    - 建议提取核心商品名（如去除活动后缀）
    - 示例：

      ```python
      # 原始名称："【618狂欢】iPhone 14 全网通5G"
      # 建议改为："iPhone14"
      ```
3. **登录安全**
    强烈建议避免在代码中硬编码账号密码（使用手动登录更安全）

## 🧩 项目结构

```python
taobao-crawler/
├── chromedriver.exe      # 浏览器驱动
├── taobao.py             # 爬虫程序
├── pyqt6.py              # 图形化界面程序（主程序）
├── 商品价格数据1.0.xlsx    # 示例输出文件（第一次爬取成功后自动创建）
├── taobaocookies.json    # 浏览器cookie（第一次登陆成功后自动创建）
└── success_crawl_urls    # 历史爬取链接（第一次爬取成功后自动创建）
```

## 🔧 常见问题

**Q：登录后程序不继续执行？** 
A：确保在控制台按 `Enter` 键继续流程

**Q：出现** **`ChromeDriver version mismatch`** **错误？** 
A：请下载与 Chrome 浏览器版本匹配的驱动

**Q：商品价格与网页显示不一致？** 
A：系统抓取的是当前登录账号的专属价格，请检查账号优惠状态
