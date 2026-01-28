#!/usr/bin/env python3
"""C Code Executor with hardened bubblewrap sandbox."""

import subprocess
import tempfile
import os
import json
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 3001
COMPILE_TIMEOUT = 10
RUN_TIMEOUT = 5
MAX_OUTPUT_SIZE = 64 * 1024


class CExecutorHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._respond(200, {'status': 'ok'})
        else:
            self._respond(404, {'error': 'Not found'})

    def do_POST(self):
        if self.path != '/execute':
            self._respond(404, {'error': 'Not found'})
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            code = data.get('code', '')

            if not code.strip():
                self._respond(400, {'error': 'No code provided'})
                return

            result = self.execute_c_code(code)
            self._respond(200, result)
        except json.JSONDecodeError:
            self._respond(400, {'error': 'Invalid JSON'})
        except Exception:
            self._respond(500, {'error': 'Internal error'})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def execute_c_code(self, code):
        work_dir = tempfile.mkdtemp(prefix='c_exec_')
        source_file = os.path.join(work_dir, 'main.c')
        binary_file = os.path.join(work_dir, 'main')

        try:
            with open(source_file, 'w') as f:
                f.write(code)

            # Hardened bwrap for compilation
            compile_result = subprocess.run(
                [
                    'bwrap',
                    # Namespace isolation
                    '--unshare-pid',
                    '--unshare-ipc',
                    '--unshare-uts',
                    '--unshare-cgroup',
                    # Network isolation (no network access)
                    '--unshare-net',
                    # Minimal read-only system binds
                    '--ro-bind', '/usr', '/usr',
                    '--ro-bind', '/lib', '/lib',
                    '--ro-bind', '/lib64', '/lib64',
                    '--ro-bind', '/bin', '/bin',
                    '--ro-bind', '/sbin', '/sbin',
                    '--ro-bind', '/etc/alternatives', '/etc/alternatives',
                    # Writable temp and work dir
                    '--tmpfs', '/tmp',
                    '--bind', work_dir, work_dir,
                    # Minimal /dev and /proc
                    '--dev', '/dev',
                    '--proc', '/proc',
                    # Die if parent dies
                    '--die-with-parent',
                    # New session to prevent terminal hijacking
                    '--new-session',
                    '--',
                    'gcc', '-o', binary_file, source_file, '-lm',
                    '-Wall', '-Wextra', '-O2', '-std=c99',
                ],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT,
            )

            if compile_result.returncode != 0:
                return {
                    'success': False,
                    'stage': 'compile',
                    'stdout': compile_result.stdout[:MAX_OUTPUT_SIZE],
                    'stderr': compile_result.stderr[:MAX_OUTPUT_SIZE],
                    'exit_code': compile_result.returncode
                }

            # Hardened bwrap for execution (even stricter)
            run_result = subprocess.run(
                [
                    'bwrap',
                    # Full namespace isolation
                    '--unshare-pid',
                    '--unshare-ipc',
                    '--unshare-uts',
                    '--unshare-cgroup',
                    '--unshare-net',
                    # Minimal read-only system (only what's needed to run)
                    '--ro-bind', '/usr/lib', '/usr/lib',
                    '--ro-bind', '/lib', '/lib',
                    '--ro-bind', '/lib64', '/lib64',
                    # Writable temp and work dir
                    '--tmpfs', '/tmp',
                    '--ro-bind', work_dir, work_dir,
                    # Minimal /dev (no /proc for user code)
                    '--dev', '/dev',
                    # Security options
                    '--die-with-parent',
                    '--new-session',
                    '--',
                    binary_file,
                ],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT,
            )

            return {
                'success': run_result.returncode == 0,
                'stage': 'run',
                'stdout': run_result.stdout[:MAX_OUTPUT_SIZE],
                'stderr': run_result.stderr[:MAX_OUTPUT_SIZE],
                'exit_code': run_result.returncode
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'stage': 'timeout', 'stdout': '', 'stderr': 'Timeout', 'exit_code': -1}
        except Exception as e:
            return {'success': False, 'stage': 'error', 'stdout': '', 'stderr': str(e), 'exit_code': -1}
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def log_message(self, format, *args):
        pass  # Suppress request logging


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), CExecutorHandler)
    print(f"C Executor running on http://127.0.0.1:{PORT}")
    server.serve_forever()
