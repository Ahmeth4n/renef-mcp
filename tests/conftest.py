import pytest

from src.session import manager
from tests.mock_server import FakeRenefTarget, MockServer


@pytest.fixture
def mock_renef():
    """Spin up an offline framed MockServer and bind the global SessionManager to it."""
    target = FakeRenefTarget()
    server = MockServer(target, framing=True)
    manager.configure("127.0.0.1", server.port)
    yield server, target
    manager.reset_session()
    server.close()
