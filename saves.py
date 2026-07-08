import re
from urllib.parse import urlparse, parse_qs

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

BOT_TOKEN = "8820510463:AAGtKRBFTbkeNQCErarqxV7heIR0VPv5-6U"

WEBSITE_1 = "https://eat-token.killersharmabot.online/"
WEBSITE_2 = "https://version-common-redflamenco.vercel.app/"

def extract_details(link):
    qs = parse_qs(urlparse(link).query)

    name = qs.get("nickname", ["Not Found"])[0]
    uid = qs.get("account_id", ["Not Found"])[0]
    region = qs.get("region", ["Not Found"])[0]

    return f"""Connected ✅

👤 Name: {name}
🆔 UID: {uid}
🌍 Region: {region}"""

async def process_flow(user_link):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = await browser.new_page()

        # Website 1
        await page.goto(WEBSITE_1, wait_until="networkidle", timeout=60000)

        await page.locator(
            'input[placeholder*="kiosgamer"], input[placeholder*="Eat token"]'
        ).fill(user_link)

        await page.get_by_role(
            "button",
            name=re.compile("GENERATE ACCESS", re.I)
        ).click()

        await page.wait_for_timeout(8000)

        text1 = await page.locator("body").inner_text()

        match = re.search(r"[a-fA-F0-9]{40,}", text1)

        if not match:
            await browser.close()
            return "❌ Access Token not found"

        token = match.group(0)

        # Website 2
        await page.goto(WEBSITE_2, wait_until="networkidle", timeout=60000)
        await page.fill("input", token)

        await page.get_by_role(
            "button",
            name=re.compile("verify", re.I)
        ).click()

        await page.wait_for_timeout(8000)

        final_text = await page.locator("body").inner_text()

        await browser.close()

        if "Connected" in final_text and "Verified" in final_text:
            return extract_details(user_link)

        return "❌ Verification failed. Please try again."

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_link = update.message.text.strip()

    msg = await update.message.reply_text("⏳ Processing...")

    try:
        result = await process_flow(user_link)
        await msg.edit_text(result[:4000])

    except Exception:
        await msg.edit_text("❌ Process failed. Please try again.")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

print("Bot Running...")
app.run_polling()
