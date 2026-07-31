"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio

from playwright.async_api import async_playwright


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Sends a WhatsApp message to the specified phone number using Playwright.

    Args:
        phone: The phone number to send the message to.
        message: The message content to send.

    Returns:
        True if the message was sent successfully, False otherwise.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        target_url = f"https://web.whatsapp.com/send?phone={phone}"
        await page.goto(target_url, wait_until="networkidle")

    print("PLAYWRIGHT ⏳ Aguardando liberação do campo de texto...")

    try:
        # Seletor universal moderno da caixa de mensagem do WhatsApp Web
        selector = "div[contenteditable='true'][role='textbox']"

        # Aguarda até 30s o WhatsApp carregar a conversa completamente
        chat_box = await page.wait_for_selector(selector, timeout=30000)

        if not chat_box:
            print("PLAYWRIGHT ❌ Erro: Campo de texto não encontrado.")
            return False

        print("PLAYWRIGHT 🎯 Campo de texto localizado!")
        await chat_box.focus()
        await chat_box.fill(message)
        await asyncio.sleep(1)  # Pausa tática para ativar o botão de envio
        await chat_box.press("Enter")

        print("PLAYWRIGHT 📤 Mensagem disparada com sucesso!")
        await asyncio.sleep(3)  # Aguarda o envio ser processado pelos servidores
        return True

    except TimeoutError:
        print("PLAYWRIGHT ⏱️ Timeout: Campo de texto não apareceu no tempo limite.")
        return False
    except RuntimeError as err:
        if "Target page, context or browser has been closed" in str(err):
            print("PLAYWRIGHT ⚠️ A janela do navegador foi fechada antes da conclusão.")
        else:
            print(f"PLAYWRIGHT ❌ Erro inesperado: {str(err)}")
        return False
