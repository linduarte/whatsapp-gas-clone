"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio

from playwright.async_api import async_playwright


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending WhatsApp messages using Playwright Chromium with stable flags.
    """
    async with async_playwright() as p:
        # Args essenciais para estabilidade no Linux e Windows
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
            ],
        )

        # Tenta utilizar o estado da sessão salva (cookies/localStorage)
        session_file = "playwright_whatsapp_session.json"
        try:
            context = await browser.new_context(storage_state=session_file)
        except (FileNotFoundError, ValueError):
            context = await browser.new_context()

        page = await context.new_page()

        try:
            target_url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"PLAYWRIGHT 🌐 Navegando para: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")

            print("PLAYWRIGHT ⏳ Aguardando liberação do campo de texto...")

            # Lista de seletores em ordem de prioridade
            text_box_selectors = [
                "div[contenteditable='true'][role='textbox']",
                "div[contenteditable='true'][data-tab='10']",
                "footer div[contenteditable='true']",
                "div[contenteditable='true']",
            ]

            chat_box = None
            for selector in text_box_selectors:
                try:
                    # Aguarda até 20s e aceita se o seletor estiver anexado ao DOM (state='attached')
                    chat_box = await page.wait_for_selector(
                        selector,
                        timeout=20000,
                        state="attached"
                    )
                    if chat_box:
                        print(f"PLAYWRIGHT 🎯 Campo localizado com o seletor: {selector}")
                        break
                except TimeoutError:
                    continue

            if not chat_box:
                print("PLAYWRIGHT ❌ Não foi possível encontrar o campo de mensagem.")
                await browser.close()
                return False

            # Foca, preenche a mensagem e dispara
            await chat_box.focus()
            await chat_box.fill(message)
            await asyncio.sleep(1)  # Pausa tática para habilitar o envio
            await chat_box.press("Enter")

            print("PLAYWRIGHT 📤 Mensagem disparada com sucesso!")
            await asyncio.sleep(4)  # Garante o envio na rede antes de salvar sessão

            # Salva o estado atualizado da sessão para os próximos disparos
            await context.storage_state(path=session_file)
            await browser.close()
            return True

        except (TimeoutError, OSError, ValueError) as err:
            print(f"PLAYWRIGHT ❌ Erro na execução da automação: {str(err)}")
            await browser.close()
            return False
