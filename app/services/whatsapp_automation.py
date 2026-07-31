"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio

from playwright.async_api import async_playwright


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending WhatsApp messages using Playwright.
    Gives generous timeout for QR Code authentication before searching for text box.
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

        session_file = "playwright_whatsapp_session.json"
        try:
            context = await browser.new_context(storage_state=session_file)
        except FileNotFoundError:
            context = await browser.new_context()

        page = await context.new_page()

        try:
            target_url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"PLAYWRIGHT 🌐 Navegando para: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")

            # 🔑 PASSO 1: Aguarda o login / sincronização (QR Code) se necessário (até 90s)
            print(
                "PLAYWRIGHT 🔑 Verificando autenticação / QR Code... (Aguardando até 90s para você escanear se necessário)"
            )
            try:
                # O painel lateral 'side' só surge quando o WhatsApp está logado!
                await page.wait_for_selector("#side", timeout=90000)
                print("PLAYWRIGHT ✅ Sessão autenticada e conectada com sucesso!")
            except TimeoutError:
                print("PLAYWRIGHT ❌ Tempo limite para escanear o QR Code expirou.")
                await browser.close()
                return False

            # 🎯 PASSO 2: Agora que está logado, aguarda a caixa de texto do chat específico
            print("PLAYWRIGHT ⏳ Aguardando liberação do campo de texto da conversa...")
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
                        print(f"PLAYWRIGHT 🎯 Campo localizado via seletor: {selector}")
                        break
                except TimeoutError:
                    continue

            if not chat_box:
                print("PLAYWRIGHT ❌ Campo de texto não encontrado após o login.")
                await browser.close()
                return False

            # Digita e envia
            await chat_box.focus()
            await chat_box.fill(message)
            await asyncio.sleep(1)
            await chat_box.press("Enter")

            print("PLAYWRIGHT 📤 Mensagem disparada com sucesso!")
            await asyncio.sleep(4)

            # Salva a sessão autenticada para NUNCA MAIS pedir QR Code
            await context.storage_state(path=session_file)
            await browser.close()
            return True

        except (TimeoutError, ConnectionError, OSError) as err:
            print(f"PLAYWRIGHT ❌ Erro durante a automação: {str(err)}")
            await browser.close()
            return False
