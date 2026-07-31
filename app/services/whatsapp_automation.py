"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending WhatsApp messages using Playwright Chromium.
    Includes User-Agent bypass for QR Code readability.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )

        # User-Agent oficial de Chrome Desktop para evitar bloqueio no QR Code
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        session_file = "playwright_whatsapp_session.json"
        try:
            context = await browser.new_context(
                storage_state=session_file, user_agent=user_agent
            )
        except (FileNotFoundError, PlaywrightError):
            context = await browser.new_context(user_agent=user_agent)

        page = await context.new_page()

        try:
            target_url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"PLAYWRIGHT 🌐 Navegando para: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")

            # Aguarda até 90s para você ter tempo tranquilo de escanear o QR Code
            print("PLAYWRIGHT 🔑 Aguardando login / leitura do QR Code...")
            try:
                await page.wait_for_selector("#side", timeout=90000)
                print("PLAYWRIGHT ✅ Sessão conectada!")
            except asyncio.TimeoutError:
                print("PLAYWRIGHT ❌ Tempo limite para o QR Code expirou.")
                await browser.close()
                return False

            # Aguarda a caixa de mensagem
            print("PLAYWRIGHT ⏳ Procurando campo de mensagem...")
            text_box_selectors = [
                "div[contenteditable='true'][role='textbox']",
                "div[contenteditable='true'][data-tab='10']",
                "footer div[contenteditable='true']",
                "div[contenteditable='true']",
            ]

            chat_box = None
            for selector in text_box_selectors:
                try:
                    chat_box = await page.wait_for_selector(
                        selector, timeout=15000, state="attached"
                    )
                    if chat_box:
                        print(f"PLAYWRIGHT 🎯 Campo localizado: {selector}")
                        break
                except asyncio.TimeoutError:
                    continue

            if not chat_box:
                print("PLAYWRIGHT ❌ Campo de mensagem não localizado.")
                await browser.close()
                return False

            # Foca no campo de texto localizado
            await chat_box.focus()

            # 1. Garante caixa limpa e simula a digitação nativa do usuário
            await chat_box.fill("")
            await page.keyboard.insert_text(message)
            await asyncio.sleep(1.5)  # Tempo para o React/DOM habilitar o botão de envio

            print("PLAYWRIGHT 📤 Disparando envio...")

            # 2. Localiza e clica no botão oficial de enviar (setinha verde)
            send_button_selector = "button span[data-icon='send']"
            try:
                send_button = await page.wait_for_selector(send_button_selector, timeout=3000)
                if send_button:
                    await send_button.click()
                    print("PLAYWRIGHT 🟢 Clique no botão de enviar realizado!")
                else:
                    await chat_box.press("Enter")
            except (asyncio.TimeoutError, PlaywrightError):
                # Caso o botão visual não esteja acessível, força o envio pelo teclado
                print("PLAYWRIGHT ⌨️ Enviando via tecla Enter...")
                await chat_box.press("Enter")

            # 3. Aguarda 5 segundos para processar o envio na rede antes de encerrar
            print("PLAYWRIGHT ⏳ Aguardando confirmação de entrega na rede...")
            await asyncio.sleep(5)

            # Salva o estado da sessão autenticada para os próximos disparos
            await context.storage_state(path=session_file)
            await browser.close()
            return True

        except (PlaywrightError, asyncio.TimeoutError) as err:
            print(f"PLAYWRIGHT ❌ Erro: {str(err)}")
            await browser.close()
            return False
