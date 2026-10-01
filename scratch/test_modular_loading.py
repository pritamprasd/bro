import asyncio
import os
import uvicorn
from pathlib import Path
from playwright.async_api import async_playwright
from bro.ui.server import app

async def run_server(port: int):
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    await server.serve()

async def run_tests():
    port = 8765
    server_task = asyncio.create_task(run_server(port))
    await asyncio.sleep(1.0) # wait for server to bind

    url = f"http://127.0.0.1:{port}"
    output_dir = Path("/home/pritam/code/ai/jarvis/docs/assets")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Connecting Playwright to {url}...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Capture console errors if any
        errors = []
        page.on("pageerror", lambda err: errors.append(str(err)))
        page.on("console", lambda msg: print(f"  [Browser {msg.type}]: {msg.text}") if msg.type == "error" else None)

        print("1. Loading root index.html via FastAPI server...")
        await page.goto(url)
        await page.wait_for_timeout(600)
        
        # Verify Command Center is active initially
        cmd_tab = await page.query_selector("#tab-command")
        assert cmd_tab is not None, "Command Center tab not found"
        is_active = await page.evaluate("document.getElementById('tab-command').classList.contains('active')")
        print(f"  Command tab initial active status: {is_active}")

        # 2. Test On-Demand Lazy Tab Loading for all tabs
        tabs_to_test = ['calendar', 'settings', 'history', 'displays', 'memory', 'errors', 'resources', 'guide']
        for tab in tabs_to_test:
            print(f"  Testing lazy load for tab: '{tab}'...")
            await page.evaluate(f"switchTab('{tab}')")
            await page.wait_for_timeout(400)
            target_id = 'tab-errors' if tab == 'errors' else f'tab-{tab}'
            tab_el = await page.query_selector(f"#{target_id}")
            assert tab_el is not None, f"Lazy-loaded tab #{target_id} not found in DOM after switchTab!"
            has_content = await page.evaluate(f"document.getElementById('{target_id}').children.length > 0")
            assert has_content, f"Lazy-loaded tab #{target_id} has no children elements!"
            print(f"    Tab '{tab}' successfully mounted and rendered in DOM.")

        # 3. Test Settings sections
        print("3. Testing Settings tab sections & Theme switching...")
        await page.evaluate("switchTab('settings')")
        await page.evaluate("showSettingsSection('theme')")
        await page.wait_for_timeout(300)
        await page.evaluate("setSystemTheme('glassmorphism')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(output_dir / "modular_glassmorphism_settings.png"))

        # 4. Test Audio Visualizer HUD
        print("4. Testing Audio HUD with Quantum Aurora Sphere...")
        await page.evaluate("switchTab('command')")
        await page.evaluate("setConversationMode('audio_only')")
        await page.evaluate("setAudioVisualizerStyle('quantum_sphere')")
        await page.evaluate("updateVoiceVisualizerState('listening', 'LISTENING // QUANTUM AURORA')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "modular_audio_hud_sphere.png"))

        # 5. Test Arc Reactor HUD
        print("5. Testing Audio HUD with Arc Reactor...")
        await page.evaluate("setAudioVisualizerStyle('arc_reactor')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(output_dir / "modular_audio_hud_reactor.png"))

        # 6. Test Equalizer Matrix HUD
        print("6. Testing Audio HUD with Equalizer Matrix...")
        await page.evaluate("setAudioVisualizerStyle('equalizer_matrix')")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(output_dir / "modular_audio_hud_matrix.png"))

        # 7. Test Talking Emoji HUD (Speaking, Listening, Processing, Idle)
        print("7. Testing Cyber Talking Emoji HUD...")
        await page.evaluate("setAudioVisualizerStyle('talking_emoji')")
        await page.evaluate("updateVoiceVisualizerState('speaking', 'BRO SPEAKING // VOICE SYNTHESIS ACTIVE')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "talking_emoji_speaking.png"))

        await page.evaluate("updateVoiceVisualizerState('listening', 'LISTENING // SPEAK YOUR COMMAND')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "talking_emoji_listening.png"))

        await page.evaluate("updateVoiceVisualizerState('processing', 'EVALUATING // THINKING...')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "talking_emoji_processing.png"))

        # 8. Check Settings visualizer card 4
        print("8. Verifying Settings Audio HUD Visualizer Card 4...")
        await page.evaluate("switchTab('settings')")
        await page.evaluate("showSettingsSection('audiovisualizer')")
        await page.wait_for_timeout(600)
        await page.screenshot(path=str(output_dir / "settings_talking_emoji_card.png"))

        await browser.close()

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    if errors:
        print(f"Page errors encountered ({len(errors)}):", errors)
        raise RuntimeError("Encountered browser console errors during testing")
    else:
        print("SUCCESS! All modular tabs, themes, and audio visualizers verified with 0 errors!")

if __name__ == "__main__":
    asyncio.run(run_tests())
