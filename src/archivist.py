# -*- coding: utf-8 -*-
"""
Log Archiving Module.
This module provides a logging utility to track script execution,
errors, and status messages by creating timestamped log files.
"""

import datetime
import psutil
import os
from .utilities import generate_filename


class Logger:
    """
    A file-based logger that tracks elapsed time between log entries.
    """

    def __init__(self):
        now = datetime.datetime.now()
        self.filename = generate_filename(prefix="CAL", ext=".log")
        self.process_id = psutil.Process(os.getpid())

        # Inizializziamo il riferimento temporale per il calcolo del delta
        self.last_log_time = now

        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(
                f"--- Log Session Start: {now.strftime('%Y-%m-%d %H:%M:%S')} ---\n\n"
            )

    def log(self, message):
        """
        Writes a message entry with timestamp and elapsed time since last call.
        """
        now = datetime.datetime.now()

        # Calcolo della differenza di tempo
        elapsed = now - self.last_log_time
        # Formattiamo il delta (es: 0:00:05.123456)
        delta_str = str(elapsed)

        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        # Costruiamo l'entrata includendo il delta
        log_entry = f"[{timestamp}] (+{delta_str})\n{message}\n\n"

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(log_entry)

        # Aggiorniamo l'ultimo timestamp per la prossima chiamata
        self.last_log_time = now

    def logmem(self):
        """
        Log the current memory usage of the process to a file.

        Calculates the RSS memory in Megabytes and appends a formatted
        entry to the instance's log file.
        """
        mem_bytes = self.process_id.memory_info().rss
        mem_mb = mem_bytes / (1024**2)
        log_entry = f"Memory used by the script: {mem_mb:.2f} MB\n\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(log_entry)
