from os import access, errno, path, R_OK, X_OK, walk
from shutil import copytree
from subprocess import CalledProcessError, check_output, STDOUT
from uuid import uuid4
from yaml import safe_load

def test_scripts_union_of_default_and_user_supplied():
    def check_scripts_union_of_default_and_user_supplied(package_name):
        deployment_id = uuid4().hex
        deploy(deployment_id, package_name)
        default = set(lsr('/opt/consul-deployment-agent/skel/linux/healthchecks'))
        user = set(lsr(path.join(package_dir(package_name), 'healthchecks')))
        output = set(lsr(path.join(archive_dir(deployment_id, package_name), 'healthchecks')))
        assert output >= default | user, 'missing: {0}'.format((default | user) - output)
    for params in ['CustomHealthchecks', 'NoHealthchecks']:
        yield check_scripts_union_of_default_and_user_supplied, params

def test_template_expressions_replaced_in_all_files():
    def check_template_expressions_replaced_in_all_files(package_name):
        deployment_id = uuid4().hex
        deploy(deployment_id, package_name)
        output = path.join(archive_dir(deployment_id, package_name), 'healthchecks')
        try:
            check_output(['! grep -rl \'{{{{[^{{}}]+}}}}\' "{}"'.format(output)], shell=True, stderr=STDOUT)
        except CalledProcessError as e:
            print e
            print e.output
            raise
    for params in ['CustomHealthchecks', 'NoHealthchecks']:
        yield check_template_expressions_replaced_in_all_files, params

def test_all_scripts_executable():
    def is_non_executable_script(filename):
        return path.splitext(filename)[1] in set(['.py', '.rb', '.sh']) and not (access(filename, R_OK) and access(filename, X_OK))
    def check_all_scripts_executable(package_name):
        deployment_id = uuid4().hex
        deploy(deployment_id, package_name)
        output = path.join(archive_dir(deployment_id, package_name), 'healthchecks')
        non_executable_scripts = [path.join(dirname, file) for dirname, _, files in walk(output) for file in files if is_non_executable_script(path.join(dirname, file))]
        assert len(non_executable_scripts) == 0, non_executable_scripts
    for params in ['CustomHealthchecks', 'NoHealthchecks']:
        yield check_all_scripts_executable, params

def test_healthchecks_union_of_default_and_user_supplied():
    def check_healthchecks_union_of_default_and_user_supplied(check_type, package_name):
        def list_healthchecks(filename):
            try:
                with open(filename, 'r') as f:
                    content = safe_load(f)
                    checks = content.get('{}_healthchecks'.format(check_type))
                    return checks.keys() if checks is not None else []
            except IOError as e:
                if e.errno == errno.ENOENT:
                    return []
                else:
                    raise
        deployment_id = uuid4().hex
        deploy(deployment_id, package_name)
        healthchecks_subpath = ['healthchecks', check_type, 'healthchecks.yml']
        default = set(list_healthchecks(path.join(deployment_dir(deployment_id, package_name), 'work', 'in', 'default', *healthchecks_subpath)))
        user = set(list_healthchecks(path.join(deployment_dir(deployment_id, package_name), 'work', 'in', 'user', *healthchecks_subpath)))
        output = set(list_healthchecks(path.join(archive_dir(deployment_id, package_name), *healthchecks_subpath)))
        assert output == default | user, 'missing: {0}'.format((default | user) - output)
    for params in [(check_type, package_name) for check_type in ['consul', 'sensu'] for package_name in ['CustomHealthchecks', 'NoHealthchecks']]:
        yield check_healthchecks_union_of_default_and_user_supplied, params[0], params[1]

def lsr(dir):
    try:
        return [path.relpath(path.join(dirname, file), dir) for dirname, _, files in walk(dir) for file in files]
    except OSError as e:
        if e.errno == errno.ENOENT:
            return []
        else:
            raise

def archive_dir(deployment_id, package_name):
    return path.join(deployment_dir(deployment_id, package_name), 'archive')

def deployment_dir(deployment_id, package_name):
    return path.join('/opt/consul-deployment-agent/deployments', package_name, deployment_id)

def package_dir(package_name):
    return path.join('/test-applications/', package_name)

def deploy(deployment_id, package_name):
    def copy_files(deployment_id, package_name):
        src = package_dir(package_name)
        dst = archive_dir(deployment_id, package_name)
        copytree(src, dst)
        copytree('/opt/consul-deployment-agent/skel/linux/code-deploy', path.join(archive_dir(deployment_id, package_name), 'code-deploy'))
        copytree('/opt/consul-deployment-agent/skel/linux/misc', path.join(archive_dir(deployment_id, package_name), 'misc'))
        copytree('/opt/consul-deployment-agent/skel/linux', path.join(deployment_dir(deployment_id, package_name), 'defaults'))
    copy_files(deployment_id, package_name)
    env = mkenv(deployment_id, package_name)
    try:
        check_output([path.join(archive_dir(deployment_id, package_name), 'code-deploy', 'on-after-install.sh')], env=env, stderr=STDOUT)
    except CalledProcessError as e:
        print e
        print e.output
        raise

def mkenv(deployment_id, package_name):
    return {
            'DEPLOYMENT_BASE_DIR': archive_dir(deployment_id, package_name),
            'TTL_ROLE': 'MyRole',
            'EM_SERVICE_PORT': str(43568),
            'EM_SERVICE_SLICE': 'blue',
            'EM_SERVICE_VERSION': '1.0.1',
            'EM_SERVICE_NAME': 'c50-{package_name}-blue'.format(package_name=package_name),
            'DEPLOYMENT_ID': str(deployment_id),
            'EC2_INSTANCE_ID': 'i-35479843130',
            'TTL_ENVIRONMENT': 'c50',
            'TTL_ENVIRONMENT_TYPE': 'Cluster',
            'TTL_SERVICE_EXE': ''
        }
