from collections import deque
import subprocess
import traceback
import sys
from threading import Thread
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # python 2.x

from nanome._internal._process import _ProcessEntry
from nanome.util import Logs

POSIX = 'posix' in sys.builtin_module_names


class _ProcessManager():
    process_data_type_queued = 0
    process_data_type_position_changed = 1
    process_data_type_starting = 2
    process_data_type_error = 3
    process_data_type_output = 4
    process_data_type_done = 5

    _max_process_count = 10

    def __init__(self):
        self.__pending = deque()
        self.__running = []

    def _update(self):
        try:
            for i in range(len(self.__running) - 1, -1, -1):
                proc = self.__running[i]
                if self.__update_process(proc) == False:
                    del self.__running[i]

            spawn_count = min(_ProcessManager._max_process_count - len(self.__running), len(self.__pending))
            if spawn_count > 0:
                while spawn_count > 0:
                    self.__start_process()
                    spawn_count -= 1

                count_before_exec = 1
                for entry in self.__pending:
                    entry.send(_ProcessManager.process_data_type_position_changed, [count_before_exec])
                    count_before_exec += 1
        except:
            Logs.error("Exception in process manager update:\n", traceback.format_exc())

    def __start_process(self):
        entry = self.__pending.popleft()
        entry.send(_ProcessManager.process_data_type_starting, [])
        request = entry.request
        args = [request.executable_path] + request.args
        has_text = entry.output_text

        def enqueue_output(out, err, queue_out, queue_err, text):
            if text:
                sentinel = ''
            else:
                sentinel = b''

            for line in iter(err.readline, sentinel):
                queue_err.put(line)
            err.close()
            for line in iter(out.readline, sentinel):
                queue_out.put(line)
            out.close()

        try:
            entry.process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1, cwd=request.cwd_path, universal_newlines=has_text, close_fds=POSIX)
            Logs.debug("Process started:", request.executable_path, "for session", entry.session._session_id)
        except:
            Logs.error("Couldn't execute process", request.executable_path, "Please check if executable is present and has permissions:\n", traceback.format_exc())
            entry.send(_ProcessManager.process_data_type_done, [-1])
            return
        entry.stdout_queue = Queue()
        entry.stderr_queue = Queue()
        thread = Thread(target=enqueue_output, args=(entry.process.stdout, entry.process.stderr, entry.stdout_queue, entry.stderr_queue, has_text))
        thread.daemon = True
        thread.start()
        self.__running.append(entry)

    def __update_process(self, entry):
        # Process stdout and stderr
        if entry.output_text:
            output = ""
            error = ""
        else:
            output = b""
            error = b""
        try:
            while True:
                output += entry.stdout_queue.get_nowait()
        except Empty:
            pass
        try:
            while True:
                error += entry.stderr_queue.get_nowait()
        except Empty:
            pass

        # error = error[entry._processed_error:]
        # entry._processed_error += len(error)
        if error:
            entry.send(_ProcessManager.process_data_type_error, [error])

        # output = output[entry._processed_output:]
        # entry._processed_output += len(output)
        if output:
            entry.send(_ProcessManager.process_data_type_output, [output])

        # Check if process finished
        return_value = entry.process.poll()
        if return_value is not None:
            # Finish process
            entry.send(_ProcessManager.process_data_type_done, [return_value])
            return False
        return True

    def _received_request(self, request, session):
        entry = _ProcessEntry(request, session)
        self.__pending.append(entry)
        session.send_process_data([_ProcessManager.process_data_type_queued, request])
