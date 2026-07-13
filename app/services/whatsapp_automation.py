"""Módulo de automação do WhatsApp Web utilizando Playwright Assíncrono."""

import asyncio
import os
import re
from datetime import datetime

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

# Constantes de seletores estáveis do WhatsApp Web
SELECTOR_SEARCH_BOX = "div[contenteditable='true'][data-tab='3']"
SELECTOR_MESSAGE_BOX = "div[contenteditable='true'][data-tab='10']"

async def send_whatsapp_with_playwright(phone: str, message: str, status_callback=None) -> bool:
    """Fluxo de automação do WhatsApp Web via Playwright Assíncrono com suporte a menus."""

    def update_status(text):
        if status_callback:
            status_callback(text)
        print(f"[PLAYWRIGHT] {text}")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    session_file = os.path.join(script_dir, "playwright_whatsapp_session.json")

    clean_phone = re.sub(r"\D", "", phone)
    if len(clean_phone) == 11 and not clean_phone.startswith("55"):
        clean_phone = "55" + clean_phone

    async with async_playwright() as p:
        update_status("Iniciando navegador Chromium...")
        browser = await p.chromium.launch(
            headless=False, args=["--disable-blink-features=AutomationControlled"]
        )

        if os.path.exists(session_file):
            update_status("Carregando sessão de login persistente...")
            context = await browser.new_context(storage_state=session_file)
        else:
            update_status("Nova sessão criada. Autenticação via QR Code necessária.")
            context = await browser.new_context()

        page = await context.new_page()
        url_target = f"https://web.whatsapp.com/send?phone={clean_phone}"
        await page.goto(url_target)

        try:
            update_status("Aguardando sincronização do WhatsApp... (Escaneie o QR Code se necessário)")
            await page.wait_for_selector(f"{SELECTOR_SEARCH_BOX},{SELECTOR_MESSAGE_BOX}", timeout=150000)

            if not os.path.exists(session_file):
                await context.storage_state(path=session_file)
                update_status("Conectado! Sessão persistente salva para os próximos envios.")
        except PlaywrightTimeoutError:
            update_status("❌ Tempo limite esgotado aguardando o QR Code/Carregamento.")
            await browser.close()
            return False

        if "send?phone=" not in page.url:
            update_status("🔄 Redirecionando para a janela de conversa...")
            await page.goto(url_target)

        try:
            update_status("Aguardando liberação do campo de texto...")
            await page.wait_for_selector(SELECTOR_MESSAGE_BOX, timeout=45000)
            message_field = page.locator(SELECTOR_MESSAGE_BOX)
            await message_field.focus()

            # Passo 1: Saudação baseada no horário
            hora = datetime.now().hour
            saudacao = "Bom dia!" if 5 <= hora < 12 else "Boa tarde!" if 12 <= hora < 18 else "Boa noite!"
            update_status(f"Enviando saudação: {saudacao}")
            await message_field.fill(saudacao)
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            # Passo 2: Menu - Opção 1
            update_status("Navegando no menu: Selecionando Opção 1...")
            await message_field.fill("1")
            await page.keyboard.press("Enter")
            await asyncio.sleep(5)

            # Passo 3: Menu - Opção 3
            update_status("Navegando no menu: Selecionando Opção 3...")
            await message_field.fill("3")
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)

            # Passo 4: Envio do Relatório Gerado pelo Streamlit
            update_status("Transmitindo o Relatório de Consumo Final...")
            await message_field.fill(message)
            await page.keyboard.press("Enter")

            await asyncio.sleep(5)  # Tempo para o pacote de rede subir
            update_status("✅ Mensagem enviada com sucesso!")
            return True

        except PlaywrightTimeoutError:
            update_status("❌ Erro: Não foi possível localizar os blocos de texto do chat.")
            return False
        finally:
            await context.close()
            await browser.close()