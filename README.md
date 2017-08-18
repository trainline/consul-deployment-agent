# consul-deployment-agent

A cross platform service that synchronises the set of applications installed on a machine with a manifest stored in a Consul key value store.

## Package Format

consul-deployment-agent installs applications packaged in the AWS [CodeDeploy revision format](http://docs.aws.amazon.com/codedeploy/latest/userguide/reference-appspec-file.html). This is a `.zip` file containing your code and an `appspec.yml` file that describes how to install the application.

### Hook Scripts

consul-deployment-agent supports the following subset of the [deployment lifecycle hooks](http://docs.aws.amazon.com/codedeploy/latest/userguide/reference-appspec-file-structure-hooks.html):

- BeforeInstall
- AfterInstall
- StartApplication
- ValidateService

#### Hook Script Execution Environment

consul-deployment-agent sets the following variables in the hook script execution environment

| Variable | Value |
|---|---|
| APPLICATION_ID | ? |,
| DEPLOYMENT_BASE_DIR | ? |
| DEPLOYMENT_ID | Environment Manager deployment ID for this application installation |
| LIFECYCLE_EVENT | The name of the currently executing lifecycle event. One of _BeforeInstall_, _AfterInstall_, _StartApplication_, _ValidateService_ |
| EM_SERVICE_SLICE | The slice the service is being installed to. One of _blue_, _green_, _none_ |
| EM_SERVICE_NAME | The name of the service being installed |
| EM_SERVICE_PORT | The port on which the service should listen  |
| EM_SERVICE_VERSION | The version of the service being installed |

## Command line options

```bash
$ python agent/core.py -h
usage: core.py [-h] [-config-dir CONFIG_DIR] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -config-dir CONFIG_DIR
                        Location of configuration files (e.g. config.yml and
                        config-logging.yml)
  -v, --version         show program's version number and exit
```

## Configuration

Deployment agent supports multiple configuration files. The agent will look for configuration files in the same directory as the executable.

| Filename           | Description                          | Example |
| ------------------ | ------------------------------------ | ------- |
| config-logging.yml | (optional) Python logging module configuration. If not specified, logs will be sent to stdout with level set to DEBUG. | [sample-config-logging.yml] (https://github.thetrainline.com/PlatformServices/consul-deployment-agent/blob/master/config/sample-config-logging.yml) |
| config.yml     | (optional) Various configuration settings. See example for supported options. | [sample-config.yml] (https://github.thetrainline.com/PlatformServices/consul-deployment-agent/blob/master/config/sample-config.yml) |

## Development

### Prerequisites (Linux and Windows)
1. Python (using 2.7+)
2. Consul agent

### Linux development

First, initialise the dependencies by running:
```bash
  sudo make init
```

Start Consul agent in development mode:
```bash
  consul agent -dev
```

To start the deployment agent:
```bash
  python agent/core.py
```

Running the tests:
```bash
  sudo make init-test
  make test
```

### Windows development

First, initialise the dependencies by running:
```bash
  pip install -r requirements.txt
```

Start Consul agent in development mode:
```bash
  consul agent -dev -advertise=127.0.0.1
```

Start the deployment agent:
```bash
  python agent/core.py
```

Running the tests:
```bash
  pip install -r test-requirements.txt
  nosetests --verbosity=2 tests
```

### Deployment simulation

Follow these steps to perform a deployment simulation:

1. Upload a deployment package to tl-deployment-sandbox S3 bucket in the Sandbox account
2. Start Consul agent as per instructions above.
3. Start Consul deployment agent as per instructions above.
4. Run the following script to trigger the deployment:
```bash
  ./scripts/deploy_service.py -n <service_name> -p <service_port> -v <version> -s <slice_name> -t <environment_type> -c <cluster_name> -b tl-deployment-sandbox -k <s3_object_key>
```
