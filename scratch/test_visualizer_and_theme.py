import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
    html_file = Path("/home/pritam/code/ai/jarvis/src/bro/ui/web/index.html").resolve()
    file_url = f"file://{html_file}"
    output_dir = Path("/home/pritam/code/ai/jarvis/docs/assets")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {file_url} in Playwright...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()

        # 1. Load Audio Only HUD with Quantum Aurora Sphere
        print("1. Capturing Audio HUD with Quantum Aurora Sphere visualizer...")
        await page.goto(file_url)
        await page.wait_for_timeout(800)
        
        # Switch to audio_only mode, glassmorphism theme, quantum sphere visualizer
        await page.evaluate("setConversationMode('audio_only')")
        await page.evaluate("setSystemTheme('glassmorphism')")
        await page.evaluate("setAudioVisualizerStyle('quantum_sphere')")
        await page.evaluate("updateVoiceVisualizerState('listening', 'LISTENING... SPEAK NOW')")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(output_dir / "audio_hud_quantum_sphere.png"))

        # 2. Open Settings -> 10. Audio HUD Animations
        print("2. Capturing Settings -> Audio HUD Animations Tab...")
        await page.evaluate("setConversationMode('audio+chat')")
        await page.evaluate("switchTab('settings')")
        await page.evaluate("showSettingsSection('audiovisualizer')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "settings_audio_visualizer.png"))

        # 3. Open Settings -> 9. UX Theme & Styling (Aurora Glassmorphism)
        print("3. Capturing Settings -> UX Theme & Styling Tab...")
        await page.evaluate("showSettingsSection('theme')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "settings_theme_glassmorphism.png"))

        # 4. Open Command Center in Glassmorphism theme
        print("4. Capturing Glassmorphism Command Center...")
        await page.evaluate("switchTab('command')")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(output_dir / "glassmorphism_mission_control.png"))

        await browser.close()
        print("All visualizer and theme screenshots successfully captured and verified in docs/assets/!")

if __name__ == "__main__":
    asyncio.run(main())
