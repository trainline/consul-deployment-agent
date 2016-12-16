# Copyright (c) Trainline Limited, 2016. All rights reserved. See LICENSE.txt in the project root for license information.

import os, stat, subprocess
from threading import Thread

class SubprocessTimeoutError(RuntimeError):
    pass

class Script(object):
    def __init__(self, filepath, env={}, run_as=None, timeout=3600):
        self.filepath = filepath
        self.env = os.environ.copy()
        self.env.update(env)
        self.run_as = run_as
        self.timeout = timeout
    def execute(self, logger):
        def run():
            self.stdout = ''
            while self.process.poll() is None:
                output = self.process.stdout.readline()
                self.stdout += output
            output = self.process.communicate()[0]
            self.stdout += output
            self.return_code = self.process.returncode
        logger.info('Starting execution of {0}. Will timeout after {1} seconds if not completed.'.format(self.filepath, self.timeout))
        process_thread = Thread(target=run)
        process_thread.start()
        process_thread.join(self.timeout)
        if process_thread.is_alive():
            # Process still running - kill it and raise timeout error
            try:
                self.process.kill()
            except OSError, e:
                # The process finished between the `is_alive()` and `kill()`
                self.return_code = self.process.returncode
            raise SubprocessTimeoutError('Process #%d killed after %d seconds' % (self.process.pid, self.timeout))
        return (self.return_code, self.stdout)

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
