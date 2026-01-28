#!/usr/bin/env python3
"""Minimal C Code Executor with bubblewrap sandbox."""

import subprocess
import tempfile
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 3001


class CExecutorHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != '/execute':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        data = json.loads(body.decode('utf-8'))
        code = data.get('code', '')

        result = self.execute_c_code(code)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def execute_c_code(self, code):
        work_dir = tempfile.mkdtemp(prefix='c_exec_')
        source_file = os.path.join(work_dir, 'main.c')
        binary_file = os.path.join(work_dir, 'main')

        try:
            with open(source_file, 'w') as f:
                f.write(code)

            # Compile with gcc inside minimal bwrap
            compile_result = subprocess.run(
                [
                    'bwrap',
                    '--ro-bind', '/', '/',
                    '--bind', work_dir, work_dir,
                    '--tmpfs', '/tmp',
                    '--dev', '/dev',
                    '--proc', '/proc',
                    '--',
                    'gcc', '-o', binary_file, source_file, '-lm',
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if compile_result.returncode != 0:
                return {
                    'success': False,
                    'stage': 'compile',
                    'stdout': compile_result.stdout,
                    'stderr': compile_result.stderr,
                    'exit_code': compile_result.returncode
                }

            # Run binary inside minimal bwrap
            run_result = subprocess.run(
                [
                    'bwrap',
                    '--ro-bind', '/', '/',
                    '--bind', work_dir, work_dir,
                    '--tmpfs', '/tmp',
                    '--dev', '/dev',
                    '--proc', '/proc',
                    '--',
                    binary_file,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return {
                'success': run_result.returncode == 0,
                'stage': 'run',
                'stdout': run_result.stdout,
                'stderr': run_result.stderr,
                'exit_code': run_result.returncode
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'stage': 'timeout', 'stdout': '', 'stderr': 'Timeout', 'exit_code': -1}
        except Exception as e:
            return {'success': False, 'stage': 'error', 'stdout': '', 'stderr': str(e), 'exit_code': -1}
        finally:
            subprocess.run(['rm', '-rf', work_dir], capture_output=True)


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), CExecutorHandler)
    print(f"Server running on http://127.0.0.1:{PORT}")
    server.serve_forever()
