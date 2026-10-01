import re
from pathlib import Path

def refactor():
    base_dir = Path("/home/pritam/code/ai/jarvis/src/bro/ui/web")
    index_path = base_dir / "index.html"
    content = index_path.read_text(encoding="utf-8")

    css_dir = base_dir / "css"
    js_dir = base_dir / "js"
    tabs_dir = base_dir / "tabs"
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)
    tabs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Extract CSS
    style_match = re.search(r"<style>(.*?)</style>", content, re.DOTALL)
    if style_match:
        full_css = style_match.group(1).strip()

        # Split into themes.css, visualizers.css, layout.css
        # Themes part is from start to before * { box-sizing
        themes_end_idx = full_css.find("* {\n      box-sizing: border-box;")
        if themes_end_idx == -1:
            themes_end_idx = full_css.find("* {")
        
        themes_css = full_css[:themes_end_idx].strip()
        (css_dir / "themes.css").write_text(themes_css, encoding="utf-8")

        # Visualizers part
        vis_start_idx = full_css.find("/* Dedicated Audio-Only Interactive Stage")
        vis_end_idx = full_css.find("/* High-Tech Media Display Dialog Modal")
        
        if vis_start_idx != -1 and vis_end_idx != -1:
            vis_css = full_css[vis_start_idx:vis_end_idx].strip()
            (css_dir / "visualizers.css").write_text(vis_css, encoding="utf-8")
            layout_css = full_css[themes_end_idx:vis_start_idx].strip() + "\n\n" + full_css[vis_end_idx:].strip()
        else:
            layout_css = full_css[themes_end_idx:].strip()
        
        (css_dir / "layout.css").write_text(layout_css, encoding="utf-8")
        print("CSS modularized into themes.css, visualizers.css, layout.css")

    # 2. Extract Tab HTMLs
    tab_patterns = {
        "calendar": r'(<div id="tab-calendar" class="tab-content".*?</div>\s*</div>\s*</div>\s*</div>)',
        "displays": r'(<div id="tab-displays" class="tab-content".*?</div>\s*</div>\s*</div>)',
        "settings": r'(<div id="tab-settings" class="tab-content".*?</div>\s*</div>\s*</div>\s*</div>\s*</div>)',
        "history": r'(<div id="tab-history" class="tab-content".*?</div>\s*</div>\s*</div>)',
        "errors": r'(<div id="tab-errors" class="tab-content".*?</div>\s*</div>\s*</div>)',
        "memory": r'(<div id="tab-memory" class="tab-content".*?</div>\s*</div>\s*</div>)',
        "guide": r'(<div id="tab-guide" class="tab-content".*?</div>\s*</div>\s*</div>\s*</div>)',
        "resources": r'(<div id="tab-resources" class="tab-content".*?</div>\s*</div>\s*</div>)',
    }

    print("Refactoring helper ready.")

if __name__ == "__main__":
    refactor()
