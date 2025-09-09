import subprocess
import threading
from queue import Queue
from typing import Sequence, Optional

class SubprocessRunner:
    """Run external tasks in a subprocess and forward stdout lines to a queue."""

    def __init__(self, cmd: Sequence[str], event_queue: Queue) -> None:
        self.cmd = cmd
        self.event_queue = event_queue
        self.process: Optional[subprocess.Popen[str]] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the subprocess and begin forwarding output."""
        try:
            self.process = subprocess.Popen(
                self.cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError:
            # Ensure the GUI receives information about failure
            self.event_queue.put("RESULT:FAIL")
            return
        self._thread = threading.Thread(target=self._forward_output, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Terminate the subprocess and stop forwarding output."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self._thread and self._thread.is_alive():
            self._thread.join()

    def _forward_output(self) -> None:
        """Read lines from stdout and put them on the queue."""
        proc = self.process
        if not proc:
            return
        stdout = proc.stdout
        if stdout:
            while True:
                if proc.poll() is not None:
                    break
                line = stdout.readline()
                if not line:
                    break
                self.event_queue.put(line.rstrip())
            stdout.close()
        returncode = proc.poll()
        if returncode is None:
            returncode = proc.wait()
        if returncode != 0:
            # Ensure the GUI receives some information about failure
            self.event_queue.put("RESULT:FAIL")
        # Signal that process has ended
        self.event_queue.put("__PROC_END__")

