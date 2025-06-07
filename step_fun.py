
#!/usr/bin/env python3
"""
Stepfun AI聊天机器人
自动访问stepfun.com网站，输入查询并获取AI回复
"""

import asyncio
import os
import logging
from playwright.async_api import async_playwright
import json
import time
from typing import List, Dict, Any, Optional
from playwright.async_api import Page

# 配置logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('stepfun_chat.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def chat_with_stepfun_ai(input_text: str) -> str:
    """
    与Stepfun AI进行对话

    Args:
        input_text (str): 要发送给AI的查询文本

    Returns:
        str: AI的回复内容
    """
    logger.info("启动Stepfun AI对话...")

    # 创建输出目录
    os.makedirs("output", exist_ok=True)

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)

        # 创建新的浏览器上下文
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            locale="zh-CN"
        )

        # 打开新页面
        page = await context.new_page()

        try:
            # 访问网站
            logger.info("正在访问stepfun.com...")
            await page.goto("https://www.stepfun.com/")
            await page.wait_for_load_state("networkidle")

            # 点击推理按钮
            deepseek_button = await page.query_selector("button:has-text('推理')")
            if deepseek_button:
                await deepseek_button.click()
                logger.info("已点击推理按钮")

            # 查找输入框并输入文本
            input_fields = await page.query_selector_all("input, textarea, [contenteditable='true']")
            logger.info(f"找到 {len(input_fields)} 个输入框")

            if not input_fields:
                raise Exception("未找到输入框")

            input_field = input_fields[0]
            await input_field.fill(input_text)
            logger.info("已输入查询文本")

            # 查找并点击聊天按钮（位于联网和视频创作之间）
            buttons = await page.query_selector_all("button")
            web_search_index = -1
            stepfun_video_index = -1

            for i, button in enumerate(buttons):
                text = await button.text_content()
                if "联网" in text:
                    web_search_index = i
                elif "视频创作" in text:
                    stepfun_video_index = i

            if web_search_index == -1 or stepfun_video_index == -1:
                raise Exception("未找到目标按钮")

            # 点击两个按钮之间的聊天按钮
            middle_buttons = buttons[web_search_index+1:stepfun_video_index]
            if not middle_buttons:
                raise Exception("未找到聊天按钮")

            middle_button = middle_buttons[0]
            await middle_button.click()
            logger.info("已点击聊天按钮，等待AI回复...")

            # 等待AI回复完成
            return await wait_for_ai_response(page)

        finally:
            await browser.close()


async def wait_for_ai_response(page) -> str:
    """
    等待并获取AI的完整回复

    Args:
        page: Playwright页面对象

    Returns:
        str: AI的回复内容
    """
    prev_response = ""

    for i in range(1800):  # 最多等待30分钟
        await page.wait_for_timeout(1000)  # 每次等待1秒

        try:
            response = await get_ai_response(page)
            # response = response.replace('复制代码查看全部', '')

            # 跳过思考阶段的提示
            if "与 DeepSeek R1 生成" in response:
                logger.debug('<thinking...>')
                continue

            # 检查回复是否完成（连续两次相同）
            if len(prev_response.strip()) > 0 and prev_response.strip() == response.strip():
                logger.info("AI回复完成")
                return response
            else:
                prev_response = response
                logger.debug(f"正在接收回复... (第{i+1}秒)")

        except Exception as e:
            logger.error(f"获取回复时出错: {e}")
            continue

    logger.warning("AI回复超时")
    return prev_response if prev_response else "回复超时，未获取到完整回复"


async def get_ai_response(page: Page) -> str:
    """
    从页面获取AI的回复内容

    Args:
        page: Playwright页面对象

    Returns:
        str: AI回复的文本内容
    """
    try:
        # 使用XPath定位AI回复元素
        response_element = page.locator(
            "xpath=/html/body/div/div[5]/div/div/div[1]/div/div[1]/div[1]/div/div[1]/div/div/div[1]/div/div[2]"
        ).first
        # print(await response_element.inner_html())

        response_text = await response_element.text_content()
        return response_text if response_text else ""

    except Exception as e:
        logger.error(f"获取AI回复时出错: {e}")
        return ""


# 示例使用
async def main():
    """示例主函数"""
    sample_query = """
    编写一个python排序代码
    """

    try:
        ai_response = await chat_with_stepfun_ai(sample_query)
        logger.info("\n=== AI回复 ===")
        logger.info(ai_response)
        return ai_response
    except Exception as e:
        logger.error(f"聊天过程中发生错误: {e}")
        return None


if __name__ == "__main__":
    logger.info("=== 测试Stepfun AI OpenAI兼容接口 ===\n")

    # 运行原始示例
    logger.info("1. 运行原始异步示例:")
    asyncio.run(main())

    logger.info("\n" + "="*50 + "\n")
