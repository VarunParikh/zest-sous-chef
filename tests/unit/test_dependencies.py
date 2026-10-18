"""Block 2.4 dependencies are installed at their pinned versions (build plan §4; C39)."""
import importlib.metadata as md


def test_transcript_and_multipart_pins():
    assert md.version("youtube-transcript-api") == "1.2.4"
    assert md.version("python-multipart") == "0.0.32"
    import python_multipart  # noqa: F401  FastAPI's form parser
    from youtube_transcript_api import YouTubeTranscriptApi  # noqa: F401
