# Copyright (c) Trainline Limited, 2016-2017. All rights reserved. See LICENSE.txt in the project root for license information.

import os
import stat
import subprocess
from threading import Timer

class SubprocessTimeoutError(RuntimeError):
    pass

class Script(object):
    def __init__(self, filepath, env={}, run_as=None, timeout=3600):
        self.filepath = filepath
        self.env = os.environ.copy()
        self.env.update(env)
        self.process = None
        self.return_code = None
        self.run_as = run_as
        self.stdout = None
        self.timeout = timeout
    def execute(self, logger):
        def kill():
            try:
                logger.error('Process #%d killed after %d seconds' % (self.process.pid, self.timeout))
                self.process.kill()
            except OSError:
                pass

        logger.info('Starting execution of {0}. Will timeout after {1} seconds if not completed.'.format(self.filepath, self.timeout))
        timer = Timer(self.timeout, kill)
        try:
            timer.start()
            stdout, _ = self.process.communicate()
        finally:
            timer.cancel()
        self.stdout = stdout
        code = self.process.returncode
        return 1 if code is None else code, self.stdout

class ShellScript(Script):
    def __init__(self, filepath, env={}, run_as=None, timeout=3600):
        Script.__init__(self, filepath, env, run_as, timeout)
    def execute(self, logger):
        file_stats = os.stat(self.filepath)
        os.chmod(self.filepath, file_stats.st_mode | stat.S_IEXEC)
        if self.run_as is None or self.run_as == 'root':
            command = self.filepath
        else:
            command = 'su {0} -c {1}'.format(self.run_as, self.filepath)
        logger.debug('Command: {0}'.format(command))
        self.process = subprocess.Popen(command, cwd=os.getcwd(), env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return super(ShellScript, self).execute(logger)

class PowershellScript(Script):
    def __init__(self, filepath, env={}, run_as=None, timeout=3600):
        Script.__init__(self, filepath, env, run_as, timeout)
    def execute(self, logger):
        self.process = subprocess.Popen([r'C:/WINDOWS/system32/WindowsPowerShell/v1.0/powershell.exe',
                                         '-ExecutionPolicy', 'Unrestricted', self.filepath],
                                        cwd=os.getcwd(), env=self.env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return super(PowershellScript, self).execute(logger)
