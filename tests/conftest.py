import logging
import sys

import urllib3

# Suppress SSL warnings during testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def pytest_configure(config):
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )
