"""
Hybrid reader: reads text via Accessibility (AX) API, with fallback
to macOS Vision OCR via screencapture for Electron-based apps like Claude/Gemini.
"""
import subprocess
import tempfile
from pathlib import Path

try:
    from ApplicationServices import (
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        kAXChildrenAttribute,
        kAXValueAttribute,
        kAXTitleAttribute,
        kAXDescriptionAttribute,
    )
    _AX_AVAILABLE = True
except ImportError:
    _AX_AVAILABLE = False

try:
    import Quartz
    import Vision
    from Foundation import NSURL
    _VISION_AVAILABLE = True
except ImportError:
    _VISION_AVAILABLE = False


def is_claude_running(process_name="Claude"):
    """Cheap check using `pgrep`; no special permission required."""
    try:
        result = subprocess.run(
            ["pgrep", "-i", process_name], capture_output=True, text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _get_pid(process_name="Claude"):
    try:
        result = subprocess.run(
            ["pgrep", "-i", process_name], capture_output=True, text=True
        )
        if result.returncode != 0 or not result.stdout.strip():
            return None
        return int(result.stdout.strip().splitlines()[0])
    except (FileNotFoundError, ValueError):
        return None


def _ocr_window(process_name):
    """Fallback OCR using macOS native Vision framework."""
    if not _VISION_AVAILABLE:
        return ""

    pid = _get_pid(process_name)
    if not pid:
        return ""

    tmp_path = Path(tempfile.gettempdir()) / f"aigrid_ocr_{process_name}.png"

    # Capture window to temp file silently (-x skips sound, -l targets window PID if possible, or full screen fallback)
    try:
        subprocess.run(["screencapture", "-x", str(tmp_path)], check=True, timeout=2)
    except Exception:
        return ""

    if not tmp_path.exists():
        return ""

    recognized_texts = []

    def completion_handler(request, error):
        if error:
            return
        observations = request.results()
        if observations:
            for obs in observations:
                top_candidate = obs.topCandidates_(1)
                if top_candidate:
                    recognized_texts.append(top_candidate[0].string())

    try:
        input_url = NSURL.fileURLWithPath_(str(tmp_path))
        input_image = Quartz.CIImage.imageWithContentsOfURL_(input_url)
        if input_image:
            request_handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(input_image, None)
            request = Vision.VNRecognizeTextRequest.alloc().initWithCompletionHandler_(completion_handler)
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            request_handler.performRequests_error_([request], None)
    except Exception:
        pass

    try:
        tmp_path.unlink(missing_ok=True)
    except Exception:
        pass

    return "\n".join(recognized_texts)


def dump_visible_text(process_name="Claude", max_depth=40, max_nodes=4000):
    """
    Tries AX tree walking first. If it yields nothing (common in Electron apps),
    falls back to macOS Vision OCR screenshot parsing automatically.
    """
    texts = []

    if _AX_AVAILABLE:
        pid = _get_pid(process_name)
        if pid is not None:
            app_ref = AXUIElementCreateApplication(pid)
            visited = 0

            def walk(element, depth):
                nonlocal visited
                if element is None or depth > max_depth or visited > max_nodes:
                    return
                visited += 1
                for attr in (kAXTitleAttribute, kAXValueAttribute, kAXDescriptionAttribute):
                    err, value = AXUIElementCopyAttributeValue(element, attr, None)
                    if err == 0 and isinstance(value, str) and value.strip():
                        texts.append(value)
                err, children = AXUIElementCopyAttributeValue(
                    element, kAXChildrenAttribute, None
                )
                if err == 0 and children:
                    for child in children:
                        walk(child, depth + 1)

            walk(app_ref, 0)

    ax_text = "\n".join(texts)

    # If AX text is empty or sparse, fall back to native OCR screen scanning
    if not ax_text.strip():
        ocr_text = _ocr_window(process_name)
        if ocr_text:
            return ax_text + "\n" + ocr_text

    return ax_text
