from app.classifier import detect


def test_detects_distortion_with_absolutes():
    result = detect("I always mess everything up.")
    assert result.has_cognitive_distortion is True


def test_handles_neutral_sentence():
    result = detect("I am learning to code and I practice daily.")
    assert result.has_cognitive_distortion is False


def test_detects_distortion_with_identity_label():
    result = detect("I am a failure.")
    assert result.has_cognitive_distortion is True


def test_detects_distortion_with_binary_framing():
    result = detect("It is either a total success or a complete failure.")
    assert result.has_cognitive_distortion is True
