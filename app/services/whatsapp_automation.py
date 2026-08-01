"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio
from datetime import datetime

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright


def obter_saudacao_expediente() -> str:
    """
    Retorna a saudação adequada ao horário de expediente:
    - 08:30 às 12:00: 'Bom dia!'
    - 13:30 às 17:00: 'Boa tarde!'
    - Intervalo de almoço / Fora de expediente: 'Olá!'
    """
    agora = datetime.now()
    tempo_em_minutos = agora.hour * 60 + agora.minute

    # Mapeamento em minutos acumulados desde 00:00
    # 08:30 = 510 min | 12:00 = 720 min | 13:30 = 810 min | 17:00 = 1020 min
    faixas_expediente = {
        range(510, 720): "Bom dia!",  # 08:30 às 11:59
        range(810, 1020): "Boa tarde!",  # 13:30 às 16:59
    }

    return next(
        (msg for r, msg in faixas_expediente.items() if tempo_em_minutos in r),
        "Olá!",  # Fallback seguro para horário de almoço ou exceções
    )


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending WhatsApp messages using Playwright Chromium with interactive dialogue.
    Simulates human typing rhythm: Saudacao -> '1' -> '3' -> Relatorio.
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

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        session_file = "playwright_whatsapp_session.json"
        try:
            context = await browser.new_context(
                storage_state=session_file, user_agent=user_agent
            )
        except PlaywrightError:
            context = await browser.new_context(user_agent=user_agent)

        page = await context.new_page()

        try:
            target_url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"PLAYWRIGHT 🌐 Navegando para: {target_url}")
            await page.goto(target_url, wait_until="domcontentloaded")

            # Aguarda até 90s para login / QR Code
            print("PLAYWRIGHT 🔑 Aguardando login / leitura do QR Code...")
            try:
                await page.wait_for_selector("#side", timeout=90000)
                print("PLAYWRIGHT ✅ Sessão conectada!")
            except (PlaywrightError, asyncio.TimeoutError, TimeoutError):
                print("PLAYWRIGHT ❌ Tempo limite para o QR Code expirou.")
                await browser.close()
                return False

            # Função auxiliar interna para simular o diálogo cadenciado
            async def enviar_passo(texto: str, espera_segundos: float = 2.0) -> bool:
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
                            selector, timeout=10000, state="attached"
                        )
                        if chat_box:
                            break
                    except (PlaywrightError, asyncio.TimeoutError, TimeoutError):
                        continue
                if not chat_box:
                    return False

                await chat_box.focus()
                await chat_box.fill("")
                await page.keyboard.insert_text(texto)
                await asyncio.sleep(0.8)

                send_button_selector = "button span[data-icon='send']"
                try:
                    send_button = await page.wait_for_selector(
                        send_button_selector, timeout=2500
                    )
                    if send_button:
                        await send_button.click()
                    else:
                        await chat_box.press("Enter")
                except (PlaywrightError, asyncio.TimeoutError, TimeoutError):
                    await chat_box.press("Enter")

                print(f"PLAYWRIGHT 💬 Passo enviado: '{texto}'")
                await asyncio.sleep(espera_segundos)
                return True

            # -------------------------------------------------------------
            # 🔄 EXECUÇÃO DO DIÁLOGO INTERATIVO
            # -------------------------------------------------------------
            saudacao_dinamica = obter_saudacao_expediente()
            print(
                f"PLAYWRIGHT 🤝 Iniciando diálogo com a saudação: '{saudacao_dinamica}'"
            )

            # Passo 1: Saudação
            if not await enviar_passo(saudacao_dinamica, espera_segundos=2.5):
                await browser.close()
                return False

            # Passo 2: Opção 1
            if not await enviar_passo("1", espera_segundos=2.0):
                await browser.close()
                return False

            # Passo 3: Opção 3
            if not await enviar_passo("3", espera_segundos=2.0):
                await browser.close()
                return False

            # Passo 4: Envio do Relatório Final
            print("PLAYWRIGHT 📄 Transmitindo relatório detalhado...")
            if not await enviar_passo(message, espera_segundos=5.0):
                await browser.close()
                return False

            print("PLAYWRIGHT 🎉 Diálogo e Relatório concluídos com sucesso!")

            # Salva o estado da sessão autenticada
            await context.storage_state(path=session_file)
            await browser.close()
            return True

        except (PlaywrightError, asyncio.TimeoutError) as err:
            print(f"PLAYWRIGHT ❌ Erro na automação: {str(err)}")
            await browser.close()
            return False
