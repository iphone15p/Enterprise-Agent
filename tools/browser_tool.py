# ==========================================
# 导入区：所有工具共享的公共依赖
# ==========================================
from playwright.sync_api import sync_playwright
import time
from langchain_core.tools import tool
import threading
import asyncio
import sys
import urllib.parse
import re


# ==============================================================================
# 🌟 一号机械臂：百度搜索底层逻辑
# ==============================================================================
def _run_baidu_rpa_in_thread(keyword: str, result_container: list):
    """【百度专属隔离舱】"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        print(f"\n🤖 [百度机械臂] 准备前往百度搜索：{keyword}...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # 穿上伪装外套，假装自己是真人的 Windows 电脑
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = context.new_page()

            # 抹除机器人的标签，实现隐身
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)

            try:
                print("   -> 🌐 正在使用【URL直达法】绕过首页...")
                encoded_keyword = urllib.parse.quote(keyword)
                target_url = f"https://www.baidu.com/s?wd={encoded_keyword}"
                page.goto(target_url, wait_until="domcontentloaded")

                print("   -> ⏳ 正在等待搜索结果加载...")
                try:
                    page.wait_for_selector(
                        "#content_left, #results, .result, .c-container, .result-op",
                        timeout=15000,
                    )
                except Exception:
                    print("   -> ⚠️ 主选择器未命中，尝试兜底等待...")
                    page.wait_for_load_state("networkidle")
                    time.sleep(3)

                print("   -> 📜 滚动页面以触发懒加载...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(0.8)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)
                page.evaluate("window.scrollTo(0, 0)")
                time.sleep(0.5)

                print("   -> 🕵️‍♂️ 正在提取百度搜索结果...")
                cards = page.locator(
                    "div.result, div.c-container, div.result-op, "
                    ".c-result, div[srcid], .result-item"
                ).all()

                result_text = f"【百度关于 '{keyword}' 的搜索情报报告】\n"
                valid_count = 0

                for idx, card in enumerate(cards):
                    if valid_count >= 5:  # 提取前 5 条
                        break
                    try:
                        # 挖标题
                        title = ""
                        for title_sel in ["h3 a", "h3", "a.title", ".t", "h3.c-title a"]:
                            loc = card.locator(title_sel)
                            if loc.count() > 0:
                                raw = loc.first.inner_text().replace("\n", "").strip()
                                if raw and len(raw) > 1:
                                    title = raw
                                    break
                        if not title or len(title) <= 1:
                            h3_loc = card.locator("h3")
                            if h3_loc.count() > 0:
                                title = h3_loc.first.text_content().replace("\n", "").strip()
                            else:
                                continue

                        if any(kw in title for kw in ["广告", "推广", "百度为您找到相关结果"]):
                            continue

                        # 挖摘要
                        abstract = ""
                        for abs_sel in [".c-abstract", ".c-span-last", ".content-right_8Zs40", ".c-abstract-new",
                                        ".c-span18", ".c-gap-top-small span", ".article-content"]:
                            loc = card.locator(abs_sel)
                            if loc.count() > 0:
                                abstract = loc.first.inner_text().replace("\n", "").strip()
                                if abstract and len(abstract) > 5:
                                    break

                        # 摘要兜底
                        if not abstract or len(abstract) <= 5:
                            full_text = card.inner_text().replace("\n", " ").strip()
                            if title in full_text:
                                abstract = full_text.replace(title, "", 1).strip()
                            else:
                                abstract = full_text
                            abstract = re.sub(r"\s+", " ", abstract)
                            if len(abstract) > 300:
                                abstract = abstract[:300] + "..."

                        result_text += f"Top {valid_count + 1}:\n"
                        result_text += f" - 📌 标题: {title}\n"
                        result_text += f" - 📝 摘要: {abstract}\n\n"
                        valid_count += 1
                    except Exception:
                        continue

                if valid_count == 0:
                    result_text += "（⚠️ 未能提取到有效搜索结果）\n"

                print(f"✅ 百度抓取完成！共提取 {valid_count} 条有效结果。")
                result_container.append(result_text)

            except Exception as e:
                result_container.append(f"❌ 百度抓取异常: {str(e)}")
            finally:
                context.close()
                browser.close()

    except Exception as e:
        result_container.append(f"❌ 浏览器异常: {str(e)}")


# ==============================================================================
# 🌟 二号机械臂：B站搜索底层逻辑（最强无死角破盾版）
# ==============================================================================
def _run_bilibili_rpa_in_thread(keyword: str, result_container: list):
    """【B站专属隔离舱】"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        print(f"\n🤖 [B站机械臂] 收到指令！准备前往 B站 搜索：{keyword}...")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)

            # 给 B 站也穿上真人的伪装外套！
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )
            page = context.new_page()
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                window.chrome = { runtime: {} };
            """)

            try:
                print("   -> 🌐 正在打开 Bilibili 首页...")
                page.goto("https://www.bilibili.com")
                page.wait_for_selector(".nav-search-input")

                print("   -> ⌨️ 正在模拟真人打字...")
                search_input = page.locator(".nav-search-input")
                search_input.click()
                search_input.type(keyword, delay=200)

                print("   -> 🖱️ 敲击回车，拦截新弹窗...")
                with page.expect_popup() as new_page_info:
                    page.keyboard.press("Enter")

                new_page = new_page_info.value

                print("   -> ⏳ 等待搜索结果...")
                new_page.wait_for_selector(".bili-video-card, .bili-live-card", timeout=15000)

                print("   -> 🖱️ 模拟往下滚动，逼出隐藏的懒加载数据...")
                new_page.keyboard.press("PageDown")
                time.sleep(3)

                print("   -> 🕵️‍♂️ 启动【无视CSS截断】的全景雷达扫描...")
                cards = new_page.locator(".bili-video-card, .bili-live-card").all()

                result_text = f"【B站关于 '{keyword}' 的高管竞品情报报告】\n"
                valid_count = 0

                for card in cards:
                    if valid_count >= 5:  # 统一升级，也抓 5 个！
                        break

                    try:
                        # --- 挖标题 ---
                        title = ""
                        # 先找带 title 属性的元素，拿最长的
                        all_title_elements = card.locator("[title]").all()
                        for el in all_title_elements:
                            val = el.get_attribute("title")
                            if val and len(val) > len(title):
                                title = val
                        # 如果没有 title 属性，动用终极撕裂者 text_content()
                        if not title:
                            h3 = card.locator("h3")
                            if h3.count() > 0:
                                title = h3.first.text_content()

                        # --- 挖 UP 主/主播 ---
                        up_name = ""
                        up_loc = card.locator("[class*='author'], [class*='uname'], [class*='up-name vip'], [class*='bili-video-card__info--author']")
                        if up_loc.count() > 0:
                            up_name = up_loc.first.text_content()
                        else:
                            # 没标签就顺藤摸瓜找主页链接
                            links = card.locator("a[href*='space.bilibili.com'], a[href*='live.bilibili.com']， [class*='up-name']").all()
                            if links:
                                up_name = links[-1].text_content()

                        # --- 数据清洗 ---
                        title = title.replace("\n", " ").strip() if title else "未知"
                        if up_name:
                            up_name = up_name.replace("\n", "").replace("UP", "").replace("·", "").strip()
                        else:
                            up_name = "未知"

                        if title == "未知" and up_name == "未知":
                            continue

                        result_text += f"Top {valid_count + 1}:\n"
                        result_text += f" - 🎬 视频: {title}\n"
                        result_text += f" - 👤 来源: {up_name}\n\n"

                        valid_count += 1
                    except Exception:
                        continue

                print("✅ B站抓取完成！即将关闭浏览器。")
                result_container.append(result_text)

            except Exception as e:
                result_container.append(f"❌ B站抓取过程异常: {str(e)}")
            finally:
                context.close()
                browser.close()
    except Exception as e:
        result_container.append(f"❌ 浏览器启动失败: {str(e)}")


# ==============================================================================
# 🌟 LangChain 暴露接口区：将底层的机械臂打包成 AI 能认识的工具
# ==============================================================================

@tool
def search_baidu(keyword: str) -> str:
    """
    【百度搜索工具】
    当用户需要搜索技术教程、新闻资讯、通用百科或日常知识时，优先调用此工具。
    输入参数 keyword: 需要搜索的关键词。
    """
    result_container = []
    t = threading.Thread(target=_run_baidu_rpa_in_thread, args=(keyword, result_container))
    t.start()
    t.join()
    return result_container[0] if result_container else "❌ 未获取到百度抓取结果"  # 因为只有一条内容，5条信息全部在这了


@tool
def search_bilibili(keyword: str) -> str:
    """
    【B站搜索工具】
    当用户明确要求搜索"视频"、"UP主"、"直播间"或"游戏通关攻略"时，优先调用此工具。
    输入参数 keyword: 需要搜索的关键词。
    """
    result_container = []
    t = threading.Thread(target=_run_bilibili_rpa_in_thread, args=(keyword, result_container))
    t.start()
    t.join()
    return result_container[0] if result_container else "❌ 未获取到B站抓取结果"


# ==========================================
# 调试区：单独运行此文件进行单元测试
# ==========================================
if __name__ == "__main__":
    print("=== 测试一：百度搜索 ===")
    print(search_baidu.invoke({"keyword": "马斯克 星舰发射 最新进展"}))

    print("\n=== 测试二：B站搜索 ===")
    print(search_bilibili.invoke({"keyword": "黑神话悟空"}))