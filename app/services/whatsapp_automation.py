"""
Automates sending a WhatsApp message via Playwright Chromium.
Handles TargetClosedError gracefully if the page or browser is closed.
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

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
        range(510, 720): "Bom dia!",    # 08:30 às 11:59
        range(810, 1020): "Boa tarde!"  # 13:30 às 16:59
    }

    return next(
        (msg for r, msg in faixas_expediente.items() if tempo_em_minutos in r),
        "Olá!"  # Fallback seguro para horário de almoço ou exceções
    )


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending WhatsApp messages using Playwright Chromium with interactive dialogue.
    Simulates human typing rhythm: Saudacao -> '1' -> '3' -> Relatorio.
    Handles cross-platform session path resolution (Linux/Windows).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        # Garante o caminho absoluto baseado na raiz do projeto (cross-platform)
        base_dir = Path(__file__).resolve().parent.parent.parent
        session_file = base_dir / "playwright_whatsapp_session.json"

        # Verifica se o arquivo de sessão realmente existe no disco antes de carregar
        if os.path.exists(session_file):
            print(f"PLAYWRIGHT 🔑 Carregando sessão existente: {session_file}")
            context = await browser.new_context(
                storage_state=str(session_file),
                user_agent=user_agent
            )
        else:
            print("PLAYWRIGHT 🆕 Nenhuma sessão encontrada. Iniciando novo contexto para autenticação...")
            context = await browser.new_context(user_agent=user_agent)

        page = await context.new_page()

        try:
            target_url = f"https://web.whatsapp.com/send?phone={phone}"
            print(f"PLAYWRIGHT 🌐 Navegando diretamente para o contato: {target_url}")

            # Aumenta o tempo limite de carregamento da página para 120s no Linux
            await page.goto(target_url, wait_until="domcontentloaded", timeout=120000)

            print("PLAYWRIGHT 🔑 Aguardando carregamento do WhatsApp / Leitura do QR Code...")

            # Aguarda a interface principal carregar (com timeout estendido para o Linux)
            try:
                await page.wait_for_selector("#side", timeout=120000)
                print("PLAYWRIGHT ✅ Interface do WhatsApp Web carregada!")
            except (asyncio.TimeoutError, PlaywrightError):
                print("PLAYWRIGHT ❌ Tempo limite expirado aguardando interface.")
                await browser.close()
                return False

            # Salva o estado da sessão IMEDIATAMENTE após a autenticação confirmada
            await context.storage_state(path=str(session_file))
            print("PLAYWRIGHT 💾 Estado da sessão armazenado no disco!")

            # Espera até 30s para que a caixa de conversa específica do número seja aberta
            print("PLAYWRIGHT ⏳ Aguardando abertura do chat do destinatário...")
            chat_pronto = False
            for _ in range(15):  # Tenta por até 30 segundos (15 x 2s)
                try:
                    # Verifica se a caixa de texto de digitação já está visível
                    box = await page.wait_for_selector("div[contenteditable='true'][role='textbox']", timeout=2000)
                    if box:
                        chat_pronto = True
                        break
                except (asyncio.TimeoutError, PlaywrightError):
                    await asyncio.sleep(2)

            if not chat_pronto:
                print("PLAYWRIGHT ⚠️ O chat do número não abriu a tempo. Verifique a conexão do celular.")
                await browser.close()
                return False

            # ... segue para a execução do diálogo interativo (Passo 1, 2, 3...)
            # Função auxiliar interna para simular o diálogo cadenciado
            async def enviar_passo(texto: str, espera_segundos: float = 2.0) -> bool:
                text_box_selectors = [
                    "div[contenteditable='true'][role='textbox']",
                    "div[contenteditable='true'][data-tab='10']",
                    "footer div[contenteditable='true']",
                    "div[contenteditable='true']"
                ]

                chat_box = None
                for selector in text_box_selectors:
                    try:
                        chat_box = await page.wait_for_selector(selector, timeout=10000, state="attached")
                        if chat_box:
                            break
                    except (asyncio.TimeoutError, PlaywrightError):
                        continue

                if not chat_box:
                    print(f"PLAYWRIGHT ❌ Campo de texto não localizado para o passo '{texto}'.")
                    return False

                await chat_box.focus()
                await chat_box.fill("")
                await page.keyboard.insert_text(texto)
                await asyncio.sleep(0.8)

                send_button_selector = "button span[data-icon='send']"
                try:
                    send_button = await page.wait_for_selector(send_button_selector, timeout=2500)
                    if send_button:
                        await send_button.click()
                    else:
                        await chat_box.press("Enter")
                except (asyncio.TimeoutError, PlaywrightError):
                    await chat_box.press("Enter")

                print(f"PLAYWRIGHT 💬 Passo enviado: '{texto}'")
                await asyncio.sleep(espera_segundos)
                return True

            # -------------------------------------------------------------
            # 🔄 EXECUÇÃO DO DIÁLOGO INTERATIVO
            # -------------------------------------------------------------
            saudacao_dinamica = obter_saudacao_expediente()
            print(f"PLAYWRIGHT 🤝 Iniciando diálogo com a saudação: '{saudacao_dinamica}'")

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

            # Salva o estado da sessão autenticada convertendo o Path para string
            await context.storage_state(path=str(session_file))
            await browser.close()
            return True

        except (PlaywrightError, asyncio.TimeoutError) as err:
            print(f"PLAYWRIGHT ❌ Erro na automação: {str(err)}")
            await browser.close()
            return False
