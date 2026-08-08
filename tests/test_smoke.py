import omni
from omni.errors import ConversionError


def test_version():
    assert omni.__version__.count(".") == 2


def test_error_is_exception():
    err = ConversionError("boom")
    assert err.message == "boom"
    assert isinstance(err, Exception)