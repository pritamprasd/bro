# Implementation Plan: Resource Attachments, Audit Intelligence, Command Center Widgets & In-UI User Manual

This plan implements all four requirements for **BRO // VARIANT 1**:
1. **Resource Attachments & On-Demand File Prompting**: Allow attaching files upfront; if a required file is missing and Bro detects it, prompt the user (via interactive Web modal or CLI prompt) to supply the file and resume without breaking execution.
2. **Human-Readable Audit Trail & Visual Intelligence**: Elevate the Audit & History interface with visual analytics (SVG actuator donut chart, success/failure breakdown, duration trend chart, search/filter controls, step timeline with collapsible thoughts/parameters, and full-resolution screenshot lightbox).
3. **Command Center Homepage Widgets**: Add high-value widgets to the Command Center HUD, including a Live Watchdog Sentinels Matrix, Multi-Disk Storage Health meters, Recent Missions Activity Feed, and Quick-Action controls.
4. **Interactive In-UI User Guide & Manual**: Add a dedicated `📖 System Manual & Guide` tab to the Web HUD containing all structured information from `user-guide.md` with interactive navigation, copyable CLI commands, visual diagrams, and quick-action test triggers.

---

## User Review Required

> [!IMPORTANT]
> **Key Experience Design Elements:**
> 1. **Zero External Charting Libraries**: All charts (Actuator breakdown donut, duration sparklines, success ratio bars) are rendered natively using lightweight SVG & CSS inside the HUD dashboard to guarantee instant offline rendering without CDN latency or privacy leaks.
> 2. **Dual-Mode File Supply Modal**: When Bro invokes `request_file`, the HUD modal allows either (a) dragging & dropping / picking a file to upload to `~/.bro/attachments/`, OR (b) pasting an existing absolute filesystem path (e.g., `~/data.csv`), plus a "File Unavailable / Cancel" button to safely continue if the file cannot be supplied.
> 3. **Live Watchdog Sentinels Grid on Homepage**: Provides real-time visual status badges for Thermal/VRAM Sentinel, Download Organizer, CDP Everyday Chrome (:9222), Tier-0 Router, Global Spotlight (<kbd>Alt</kbd>+<kbd>J</kbd>), and Telegram Remote.
> 4. **In-UI Interactive User Guide**: Features a searchable sidebar navigation covering all 12 operational topics, styled in Bro Obsidian/Neon Cyan, with copy-code buttons and 1-click test action buttons.

---

## Proposed Changes

### Component 1: Core Audit Analytics & Hardware Sentinel

#### [MODIFY] [audit.py](src/bro/core/audit.py)
- Extend `AuditManager.get_analytics()`:
  - Add total steps executed, average steps per run, fastest and longest execution times.
  - Return recent run summaries (`recent_timeline`) with formatted timestamps, step counts, duration, and status for instant charting.
  - Include actuator percentage distribution.

#### [MODIFY] [sentinel.py](src/bro/watchdogs/sentinel.py)
- Enhance `HardwareSentinel.get_hardware_metrics()`:
  - Add multi-disk metrics: Root partition (`/`) and Secondary Storage (`/mnt/HDD-500GB/` if present) with used GB, free GB, total GB, and percent used.

---

### Component 2: Backend API & WebSocket Server

#### [MODIFY] [server.py](src/bro/ui/server.py)
- Allow `/api/supply-file` to accept `Optional[str]` for `file_path`, handling cancellation gracefully (`file_request_event.set()`, sets `last_supplied_file = None` and notifies WebSocket).
- Add endpoint `/api/guide` to serve the full markdown content and section index of `user-guide.md`.
- Add endpoint `/api/history/{run_id}/markdown` to export any mission audit trail as a formatted markdown summary.
- Provide real-time watchdog status info in `/api/status`.

---

### Component 3: Tactical Web HUD & Visual Analytics

#### [MODIFY] [index.html](src/bro/ui/web/index.html)
- **Homepage (Command Center) Enhancements:**
  - **Watchdogs Matrix Card**: Real-time status cards for Thermal Sentinel, Download Auto-Organizer, CDP Chrome, Tier-0 Router, Spotlight Daemon, and Telegram Bot.
  - **Multi-Disk Storage Health**: Real-time meters for NVMe (`/`) and HDD (`/mnt/HDD-500GB/`).
  - **Recent Missions Activity Feed**: Sleek mini-feed of the last 3-4 missions on the homepage with 1-click "Inspect" deep-link to the Audit tab.
  - **Terminal Log Controls**: Add "Clear Terminal" and "Copy Logs" buttons.
- **Audit & History Visual Overhaul:**
  - **Interactive SVG Actuator Donut Chart**: Visual distribution of Desktop vs Browser vs Python vs Shell vs Macro actions with hover tooltips and legend.
  - **Success / Failure Metric Gauge**: Visual ratio bar and percentage breakdown.
  - **Mission Velocity & Duration Chart**: Interactive bar/sparkline chart showing execution time of recent runs.
  - **Filter & Search Bar**: Quick search box to filter missions by goal keyword and status pills (`All`, `Success`, `Failed`).
  - **Human-Readable Step Timeline**: Formatted cards with clear "Intent & Thought" bubble, action pills, formatted parameters table, clean observation output, and clickable screenshot thumbnails.
  - **Screenshot Lightbox Modal**: High-res overlay when clicking any step screenshot to inspect full 1920x1080 capture with zoom.
  - **Export Mission Report**: 1-click button to download or copy the run's markdown audit trail.
- **Resource Attachment & Prompting:**
  - Enhanced drop-zone and attachment chips in Command Center.
  - Dual-input modal (Upload file OR Enter local file path) + "File Unavailable / Cancel" button.
- **Dedicated In-UI User Guide Tab (`📖 System Manual`):**
  - Interactive topic sidebar covering Architecture & ReAct Loop, Lifecycle, 4 Communication Modalities, Voice Persona, Daily Brief, Resource Attachments, Model Selection, Automation, Safety, and Memory.
  - Interactive code blocks with 1-click copy for `uv run bro ...` CLI commands.
  - Quick action buttons ("Test Mic", "Trigger Daily Brief", "Attach Chrome", etc.) directly in the guide.

---

### Component 4: Documentation & Test Suite

#### [MODIFY] [tests/test_audit.py](tests/test_audit.py)
- Add unit tests for extended `get_analytics()` metrics (total steps, actuator distribution, timeline items).

#### [MODIFY] [README.md](README.md) & [user-guide.md](user-guide.md)
- Document file attachment usage (`-f` in CLI, Web UI drop bar).
- Document on-demand file requesting mechanism.
- Document Audit Trail charts and Command Center widgets.
- Keep in sync with UI manual.

---

## Verification Plan

### Automated Tests
- `uv run pytest -v` (ensure all tests pass, including new audit analytics tests).

### Manual Verification
1. **File Attachments & Missing File Prompting:**
   - Launch `bro start` and open HUD at `http://127.0.0.1:8765`.
   - Test uploading a file via UI drop bar and running a task referencing it.
   - Test triggering a task where a file is required (e.g., "Analyze the data in quarterly_sales.csv"), verifying that the modal prompts for the file, and that supplying the file resumes the agent.
   - Test canceling the modal and verifying agent receives graceful error observation.
2. **Audit Trail & Charts:**
   - Open Audit tab, inspect the SVG Donut chart, duration trend bars, and KPI metrics.
   - Test search and status filter buttons.
   - Click a mission, verify formatted timeline, click a screenshot to verify lightbox zoom.
3. **Command Center Widgets:**
   - Verify Watchdogs Matrix shows active statuses.
   - Verify Disk meters show NVMe and HDD capacity.
   - Verify Recent Missions feed displays latest runs.
   - Verify Terminal Clear and Copy buttons work as expected.
4. **In-UI System Manual:**
   - Switch to `📖 System Manual` tab.
   - Verify all 12 operational sections render with clean formatting, copy buttons, and quick actions.
