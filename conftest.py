import pytest
from dotenv import load_dotenv


def set_test():
    load_dotenv(".test_env")


def clear_test():
    load_dotenv(".development_env")


@pytest.fixture(scope="session", autouse=True)
def tests_setup_and_teardown():
    set_test()
    yield
    clear_test()
