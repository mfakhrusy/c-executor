#!/usr/bin/env python3
"""
Lightweight C Code Executor
A minimal HTTP server that compiles and runs C code using gcc + firejail.

Requires: gcc, firejail
Install firejail: https://github.com/netblue30/firejail
"""

import subprocess
import tempfile
import os
import json
import secrets
import shutil
import signal
import atexit
from http.server import HTTPServer, BaseHTTPRequestHandler

# Configuration
PORT = 3001
MAX_CODE_SIZE = 64 * 1024  # 64KB max code size
MAX_OUTPUT_SIZE = 64 * 1024  # 64KB max output
COMPILE_TIMEOUT = 10  # seconds
RUN_TIMEOUT = 5  # seconds
MAX_MEMORY_MB = 128  # Max memory for executed program

# Allowed origins for CORS (set to specific domain in production)
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '*')

# Track temp directories for cleanup on shutdown
_temp_dirs = set()


def cleanup_temp_dirs():
    """Cleanup any remaining temp directories on shutdown."""
    for d in list(_temp_dirs):
        try:
            shutil.rmtree(d, ignore_errors=True)
        except Exception:
            pass
    _temp_dirs.clear()


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    cleanup_temp_dirs()
    raise SystemExit(0)


# Register cleanup handlers
atexit.register(cleanup_temp_dirs)
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


class CExecutorHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type='application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        
        # CORS headers - restrict in production
        origin = self.headers.get('Origin', '')
        if ALLOWED_ORIGINS == '*':
            self.send_header('Access-Control-Allow-Origin', '*')
        elif origin in ALLOWED_ORIGINS.split(','):
            self.send_header('Access-Control-Allow-Origin', origin)
        
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path == '/health':
            self._set_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        elif self.path == '/whoami':
            import pwd
            user = pwd.getpwuid(os.getuid()).pw_name
            uid = os.getuid()
            gid = os.getgid()
            self._set_headers()
            self.wfile.write(json.dumps({'user': user, 'uid': uid, 'gid': gid}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def do_POST(self):
        if self.path != '/execute':
            self._set_headers(404)
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())
            return

        try:
            # Validate Content-Length header exists and is valid
            content_length_header = self.headers.get('Content-Length')
            if content_length_header is None:
                self._set_headers(411)
                self.wfile.write(json.dumps({'error': 'Content-Length required'}).encode())
                return
            
            try:
                content_length = int(content_length_header)
            except ValueError:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid Content-Length'}).encode())
                return
            
            if content_length < 0 or content_length > MAX_CODE_SIZE:
                self._set_headers(413)
                self.wfile.write(json.dumps({'error': 'Code too large'}).encode())
                return

            body = self.rfile.read(content_length)
            
            # Validate UTF-8 encoding
            try:
                body_str = body.decode('utf-8')
            except UnicodeDecodeError:
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid UTF-8 encoding'}).encode())
                return
            
            data = json.loads(body_str)
            
            # Validate data is a dict
            if not isinstance(data, dict):
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Invalid request format'}).encode())
                return
            
            code = data.get('code', '')
            
            # Validate code is a string
            if not isinstance(code, str):
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'Code must be a string'}).encode())
                return

            if not code.strip():
                self._set_headers(400)
                self.wfile.write(json.dumps({'error': 'No code provided'}).encode())
                return

            result = self.execute_c_code(code)
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())

        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())
        except Exception:
            # Don't leak internal error details
            self._set_headers(500)
            self.wfile.write(json.dumps({'error': 'Internal server error'}).encode())

    def execute_c_code(self, code):
        """Compile and execute C code in firejail sandbox."""
        # Use secure random suffix for temp directory
        work_dir = tempfile.mkdtemp(prefix='c_exec_', suffix=f'_{secrets.token_hex(8)}')
        _temp_dirs.add(work_dir)
        
        source_file = os.path.join(work_dir, 'main.c')
        binary_file = os.path.join(work_dir, 'main')

        try:
            # Write source code with restricted permissions
            fd = os.open(source_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as f:
                f.write(code)

            # Compile with gcc inside firejail
            # Less restrictive than execution sandbox - needs access to:
            #   - /usr/include (headers)
            #   - /usr/lib (libraries)
            #   - /usr/bin/gcc, /usr/bin/as, /usr/bin/ld
            # But still blocks:
            #   - Network access
            #   - Home directory (prevents #include "/home/user/.ssh/id_rsa")
            #   - Most of /etc
            compile_result = subprocess.run(
                [
                    '/usr/bin/firejail',
                    '--quiet',
                    '--noprofile',
                    f'--private={work_dir}',
                    '--private-tmp',
                    '--private-dev',
                    '--private-etc=alternatives,ld.so.cache,ld.so.conf,ld.so.conf.d',
                    '--net=none',
                    '--nosound',
                    '--no3d',
                    '--novideo',
                    '--nodvd',
                    '--nogroups',
                    '--nonewprivs',
                    '--noroot',
                    '--seccomp',
                    '--caps.drop=all',
                    f'--rlimit-as={MAX_MEMORY_MB * 4 * 1024 * 1024}',  # More memory for compiler
                    '--rlimit-cpu=10',
                    '--rlimit-fsize=10485760',  # 10MB for object files
                    '--rlimit-nproc=20',  # gcc spawns subprocesses (cc1, as, ld)
                    '--rlimit-nofile=100',
                    f'--timeout=00:00:{COMPILE_TIMEOUT:02d}',
                    '--read-only=/usr',
                    '--read-only=/lib',
                    '--read-only=/lib64',
                    '--',
                    '/usr/bin/gcc',
                    '-o', binary_file,
                    source_file,
                    '-lm',
                    '-Wall',
                    '-Wextra',
                    '-pie',
                    '-fPIE',
                    '-Wl,-z,now',
                    '-Wl,-z,relro',
                ],
                capture_output=True,
                text=True,
                timeout=COMPILE_TIMEOUT + 2,
                cwd=work_dir,
                env={},
                shell=False,
            )

            if compile_result.returncode != 0:
                return {
                    'success': False,
                    'stage': 'compile',
                    'stdout': '',
                    'stderr': self._sanitize_output(compile_result.stderr),
                    'exit_code': compile_result.returncode
                }

            # Make binary executable
            os.chmod(binary_file, 0o500)

            # Execute in firejail sandbox
            # Firejail options:
            #   --quiet: Suppress firejail messages
            #   --noprofile: Don't use default profiles
            #   --private=DIR: Use DIR as private /home
            #   --private-tmp: Mount empty /tmp
            #   --private-dev: Limited /dev
            #   --private-etc=none: Empty /etc
            #   --net=none: No network access
            #   --no3d: Disable 3D acceleration
            #   --nosound: Disable sound
            #   --novideo: Disable video
            #   --nodvd: Disable DVD/CD
            #   --nogroups: Disable supplementary groups
            #   --nonewprivs: No new privileges
            #   --noroot: No root in sandbox
            #   --seccomp: Enable seccomp filter
            #   --caps.drop=all: Drop all capabilities
            #   --rlimit-*: Resource limits
            #   --timeout: Kill after timeout
            run_result = subprocess.run(
                [
                    '/usr/bin/firejail',
                    '--quiet',
                    '--noprofile',
                    f'--private={work_dir}',
                    '--private-tmp',
                    '--private-dev',
                    '--private-etc=none',
                    '--net=none',
                    '--no3d',
                    '--nosound',
                    '--novideo',
                    '--nodvd',
                    '--nogroups',
                    '--nonewprivs',
                    '--noroot',
                    '--seccomp',
                    '--caps.drop=all',
                    f'--rlimit-as={MAX_MEMORY_MB * 1024 * 1024}',
                    '--rlimit-cpu=5',
                    '--rlimit-fsize=1048576',
                    '--rlimit-nproc=5',
                    '--rlimit-nofile=20',
                    f'--timeout=00:00:0{RUN_TIMEOUT}',
                    '--',
                    binary_file,
                ],
                capture_output=True,
                text=True,
                timeout=RUN_TIMEOUT + 2,  # Extra buffer for firejail overhead
                cwd=work_dir,
                env={},  # Empty environment
                shell=False,
            )

            return {
                'success': run_result.returncode == 0,
                'stage': 'run',
                'stdout': self._sanitize_output(run_result.stdout),
                'stderr': self._sanitize_output(run_result.stderr),
                'exit_code': run_result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stage': 'timeout',
                'stdout': '',
                'stderr': 'Execution timed out',
                'exit_code': -1
            }
        except FileNotFoundError as e:
            if 'firejail' in str(e):
                return {
                    'success': False,
                    'stage': 'error',
                    'stdout': '',
                    'stderr': 'Sandbox not available. Install firejail: sudo apt install firejail',
                    'exit_code': -1
                }
            return {
                'success': False,
                'stage': 'error',
                'stdout': '',
                'stderr': 'Execution failed',
                'exit_code': -1
            }
        except Exception:
            return {
                'success': False,
                'stage': 'error',
                'stdout': '',
                'stderr': 'Execution failed',
                'exit_code': -1
            }
        finally:
            # Secure cleanup
            try:
                shutil.rmtree(work_dir, ignore_errors=True)
                _temp_dirs.discard(work_dir)
            except Exception:
                pass

    def _sanitize_output(self, output):
        """Sanitize output to remove sensitive paths and limit size."""
        if not output:
            return ''
        
        # Truncate to max size
        output = output[:MAX_OUTPUT_SIZE]
        
        # Remove absolute paths that might leak server info
        output = output.replace(tempfile.gettempdir(), '/tmp')
        
        # Remove firejail messages that might leak info
        lines = output.split('\n')
        filtered = [l for l in lines if not l.startswith('Parent pid')]
        
        return '\n'.join(filtered)

    def log_message(self, format, *args):
        # Sanitize log output to prevent log injection
        msg = str(args[0]).replace('\n', ' ').replace('\r', ' ')[:200]
        print(f"[{self.log_date_time_string()}] {msg}")


def check_dependencies():
    """Check if required dependencies are installed."""
    missing = []
    
    for cmd, pkg in [('/usr/bin/gcc', 'gcc'), ('/usr/bin/firejail', 'firejail')]:
        if not os.path.exists(cmd):
            missing.append(pkg)
    
    if missing:
        print(f"ERROR: Missing dependencies: {', '.join(missing)}")
        print(f"Install with: sudo apt install {' '.join(missing)}")
        return False
    
    return True


def run_server():
    if not check_dependencies():
        return
    
    # Bind only to localhost for security
    server = HTTPServer(('127.0.0.1', PORT), CExecutorHandler)
    print(f"C Executor server running on http://127.0.0.1:{PORT}")
    print(f"Sandbox: firejail (seccomp + namespaces)")
    print(f"Endpoints:")
    print(f"  POST /execute - Execute C code")
    print(f"  GET  /health  - Health check")
    print(f"\nPress Ctrl+C to stop")
    try:
        server.serve_forever()
    except (KeyboardInterrupt, SystemExit):
        print("\nShutting down...")
        server.shutdown()
        cleanup_temp_dirs()


if __name__ == '__main__':
    run_server()
