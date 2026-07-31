"""update contenteditable chat selectors and add fill delay"""
import asyncio

from playwright.async_api import async_playwright


async def send_whatsapp_with_playwright(phone: str, message: str) -> bool:
    """
    Automates sending a WhatsApp message via Playwright Chromium.
    Uses resilient selectors for the WhatsApp Web chat box.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        # # URL de direcionamento direto
        target_url = f"https://web.whatsapp.com/send?phone={phone}"
        await page.goto(target_url, wait_until="networkidle")

    # Lista de seletores modernos para a caixa de texto do WhatsApp Web
    text_box_selectors = [
        "div[contenteditable='true'][data-tab='10']",
        "div[contenteditable='true'][role='textbox']",
        "div[contenteditable='true']",
        "footer div[contenteditable='true']",
    ]

    print("PLAYWRIGHT ⏳ Aguardando liberação do campo de texto...")
    chat_box = None
    for selector in text_box_selectors:
        try:
            # Tenta localizar cada seletor aguardando até 8 segundos por tentativa
            chat_box = await page.wait_for_selector(selector, timeout=8000)
            if chat_box:
                print(
                    f"PLAYWRIGHT 🎯 Campo de texto localizado via seletor: {selector}"
                )
                break
        except TimeoutError:
            continue

    if not chat_box:
        print(
            "PLAYWRIGHT ❌ Erro: Não foi possível localizar os blocos do texto do chat."
        )
        return False

    # Foca no campo, digita o texto (preservando as quebras de linha) e envia
    await chat_box.focus()

    # Digita o texto (o Shift+Enter é tratado automaticamente se o texto tiver \n)
    await chat_box.fill(message)
    await asyncio.sleep(1)  # Pequena pausa tática para o botão de envio habilitar

    # Pressiona Enter para disparar a mensagem
    await chat_box.press("Enter")
    print("PLAYWRIGHT 📤 Mensagem disparada com sucesso!")

    # Aguarda 3 segundos para garantir a entrega antes de fechar a página
    await asyncio.sleep(3)
    return True
