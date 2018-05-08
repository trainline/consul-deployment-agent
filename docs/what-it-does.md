# What the Consul Deployment Agent Does

## On startup

- Waits for puppet to drop file to signal instance readiness before proceeding (if instructed to do so in the config file).

- Loads consul and standard configuration from the local config.yml file.

- Loads server role information from the host EC2 instance's tags (or hard-coded values during local development).

- Figures out server role key and constantly polls (long polling) for changes in key value store. When a change is detected the convergence process is run (see [Convergence](#convergence) process below). Key format is... `environments/{ENVIRONMENT}/roles/{SERVER_ROLE}`

<a id="convergence"></a>

## Convergence

- Loads list of serviceSlices registered in the catalog.

- Loads list of serviceSlices in KV store.

	- Key to list services: `environments/{ENVIRONMENT}/roles/{SERVER_ROLE}/services`
	- Key to list slices for a service: `environments/{ENVIRONMENT}/roles/{SERVER_ROLE}/services/{SERVICE_NAME}`

- For each serviceSlice listed...

  - pulls details from: `environments/{ENVIRONMENT}/roles/{SERVER_ROLE}/services/{SERVICE_NAME}/{SLICE}`. This gives us the deploymentId and version number. We then collect further details from:
    - `environments/{ENVIRONMENT}/services/{SERVICE_NAME}/{VERSION}/definition`
    - `environments/{ENVIRONMENT}/services/{SERVICE_NAME}/{VERSION}/installation`
    - `deployments/{DEPLOYMENT_ID}`
  - Figures out which serviceSlices are not present or have the wrong version.
  - Filters serviceSlices which are in 'Ignore' state or which have beenpreviously quarantened.
  - Deploys each serviceSlice in sequence (see [Deployment](#deployment) below).

<a id="deployment"></a>

## Deployment

- Creates a new log / report for the deployment

- Update the status of the node (started deployment) in the KV store.Key: deployments/{DEPLOYMENT_ID}/nodes/{NODE_ID}

- Runs the deployment stages in sequence (see [Deployment Stages](#deployment-stages) for more details)
	
- If any of the stages above fail then report failed and attempt to run stop stage, otherwise report success

- Finalise the log and the report

- Update the status of the node (finished deployment) in the KV store. Key: `deployments/{DEPLOYMENT_ID}/nodes/{NODE_ID}`

<a id="deployment-stages"></a>

## Deployment Stages

- Of the above stages the following need to be provided in the deployment package...

	- StopApplication
	- BeforeInstall
	- AfterInstall
	- StartApplication
	- ValidateService

- The location of the script files in the package are specified by the appspec.yml.

- They are executed in the above order.

- The StopApplication stage is special in that it's the StopApplication script from the previous deployment that is run (not the current deployment). This is why we keep the previous deployment files.

- The following is the complete list of deployment stages and what they're for:

  - CheckDiskSpace - Fails the deployment if not enough disk-space is available

  - ValidateDeployment - Fails the deployment if this deployment has been  tried more than the max number of times

  - DeregisterOldConsulHealthChecks - Removes all consul health checks for  this serviceSlice

  - DeregisterOldSensuHealthChecks - Removes all sensu health checks for this serviceSlice

  - DownloadBundleFromS3 - Downloads the package from S3

  - ValidateBundle - Validates that the appspec file is present and makes sense

  - StopApplication - User provided - Stops the currently running service

  - BeforeInstall - User provided - Does anything else the user wants to do

  - CopyFiles - Copies the package contents to a particular location if specified in the appspec file

  - ApplyPermissions - Makes the files executable on Linux machines

  - AfterInstall - User provided - Performs the actual install of the service

  - StartApplication - User provided - Starts the service

  - ValidateService - User provided - Checks that the service has been installed and started properly

  - RegisterWithConsul - Registers the service with consul. If already
 previously registered this will update the tags (i.e. version number)

  - RegisterConsulHealthChecks - Register consul healthchecks provided in the package with consul

  - RegisterSensuHealthChecks - Register sensu healthchecks provided in the package with sensu
  
  - DeletePreviousDeploymentFiles - Deletes all but the current and previous deployment files
