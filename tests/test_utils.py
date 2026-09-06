import pytest

from localmedia.utils import human_bytes, parse_bitrate, parse_time


def test_parse_time_seconds():
    assert parse_time("12.5") == 12.5


def test_parse_time_mm_ss():
    assert parse_time("01:30") == 90


def test_parse_time_hh_mm_ss():
    assert parse_time("01:02:03") == 3723


def test_parse_time_rejects_invalid_seconds():
    with pytest.raises(ValueError):
        parse_time("01:99")


def test_parse_bitrate():
    assert parse_bitrate("128k") == 128_000
    assert parse_bitrate("2M") == 2_000_000


def test_human_bytes():
    assert human_bytes(1024) == "1.00 KiB"
