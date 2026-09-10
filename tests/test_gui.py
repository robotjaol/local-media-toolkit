import queue
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from localmedia.gui import ConverterTab, available_output, video_command


def test_collision_names(tmp_path):
    source = tmp_path / "my photo.png"
    (tmp_path / "my photo_converted.png").touch()
    assert available_output(source, tmp_path, "PNG").name == "my photo_converted_2.png"


def test_video_actions_preserved_without_forced_overwrite():
    for action in ("convert", "compress", "strip-metadata"):
        command = video_command(Path("my video.mov"), Path("result.mp4"), action, "mp4", 23)
        assert "my video.mov" in command
        assert action in command
        assert "--overwrite" not in command
        assert ("--crf" in command) == (action == "compress")
        assert ("--to" in command) == (action == "convert")


def test_batch_continues_after_failure(tmp_path):
    worker = SimpleNamespace(media="Image", events=queue.Queue())
    jobs = [("1", tmp_path / "bad.png"), ("2", tmp_path / "good.png")]
    with patch("localmedia.gui.convert_image", side_effect=[ValueError("invalid"), None]):
        ConverterTab._worker(worker, jobs, tmp_path, "PNG", "convert", 28, {}, None)
    events = list(worker.events.queue)
    assert [event[0] for event in events] == ["running", "failure", "running", "success", "done"]
    assert events[-1] == ("done", 1, 1)
