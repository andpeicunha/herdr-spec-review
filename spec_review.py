#!/usr/bin/env python3
"""Entry point for the Spec Review reader pane."""
from specreview.ui import log_crash, main


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        log_crash()
        raise
