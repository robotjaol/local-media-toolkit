from localmedia.core import codec_args, overwrite_args


def test_codec_args_h264():
    args = codec_args("h264", 28, "medium")
    assert "libx264" in args
    assert "28" in args


def test_overwrite_flags():
    assert overwrite_args(True) == ["-y"]
    assert overwrite_args(False) == ["-n"]
