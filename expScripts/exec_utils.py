# exec_utils.py
import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from _email_sender import EmailSender  
from pitest_utils import extract_pitest_sections

logger = logging.getLogger(__name__)

def make_java_env(jdk_home: str) -> Dict[str, str]:
    env = dict(os.environ)
    env["JAVA_HOME"] = jdk_home
    env["PATH"] = str(Path(jdk_home) / "bin") + os.pathsep + env.get("PATH", "")
    return env

def run_command(
    cmd: str,
    env: Dict[str, str],
    cwd: Path,
    email_sender: EmailSender,
    verbose: bool = True,
    capture_pitest: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    Execute a shell command in a subprocess without deadlocking on large output.
    Streams stdout/stderr into both the console (if verbose=True) and the Python logger,
    ensuring that Maven (mvn) output is captured in the log file as well.

    If the command returns a non-zero exit code, send an email with failure details
    before exiting. If capture_pitest=True, extract and return the Pitest timing/statistics
    sections; otherwise return (None, None).
    """
    MAX_LINES = 1000
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    logger.info("Current working directory: %s", cwd)
    logger.info("Running command: %s", cmd)

    def reader_thread(stream, buffer_list: List[str], is_stdout: bool):
        for line in iter(stream.readline, ""):
            buffer_list.append(line)
            if len(buffer_list) > MAX_LINES:
                del buffer_list[0]
            if verbose:
                text = line.rstrip("\n")
                if is_stdout:
                    logger.info(text)
                else:
                    logger.error(text)
        stream.close()

    proc = subprocess.Popen(
        cmd, shell=True, executable="/bin/bash",
        env=env, cwd=str(cwd),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1
    )

    t_out = threading.Thread(target=reader_thread, args=(proc.stdout, stdout_lines, True), daemon=True)
    t_err = threading.Thread(target=reader_thread, args=(proc.stderr, stderr_lines, False), daemon=True)
    t_out.start()
    t_err.start()

    retcode = proc.wait()
    t_out.join()
    t_err.join()

    combined_output = "".join(stdout_lines) + "".join(stderr_lines)

    if retcode != 0:
        logger.error("Command failed (exit code %d): %s", retcode, cmd)
        logger.error(combined_output)
        try:
            email_sender.send_failure_email(cmd, combined_output)
        except Exception as e:
            logger.error("Error while sending failure email: %s", e)
        return None, None

    return extract_pitest_sections(combined_output) if capture_pitest else (None, None)
