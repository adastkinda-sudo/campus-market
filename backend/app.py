from __future__ import annotations

from http.server import ThreadingHTTPServer

import core
import server
from core import *  # Re-exported for MySQL adapter compatibility.
from server import CampusMarketHandler, main


if __name__ == "__main__":
    main()
