## Beware that this only makes sense to do on before-install, as for example application-stop won't get all variables set
## That is why before-install bakes the service.env that is later being loaded on all other stages

# $env:TTL_IAM_ROLE=$env:TTL_ROLE #missing
$env:TTL_SERVICE_PORT=$env:EM_SERVICE_PORT
$env:TTL_SERVICE_SLICE=$env:EM_SERVICE_SLICE
$env:TTL_SERVICE_VERSION=$env:EM_SERVICE_VERSION
$env:TTL_SERVICE_CONSUL_NAME=$env:EM_SERVICE_NAME
$env:TTL_SERVICE_NAME=($env:EM_SERVICE_NAME).Split("-")[1]
$env:TTL_SERVICE_NAME_WITH_SLICE="${env:TTL_SERVICE_NAME}-${env:TTL_SERVICE_SLICE}"
$env:TTL_DEPLOYMENT_ID=$env:DEPLOYMENT_ID
$env:TTL_DEPLOYMENT_DIR=$env:DEPLOYMENT_BASE_DIR
# $env:TTL_INSTANCE_ID=$env:EC2_INSTANCE_ID #missing

# Windows specific
$env:TTL_SERVICE_EXE="Trainline.${env:TTL_SERVICE_NAME}.exe"
$env:TTL_INSTALL_DIR="d:\Trainline\Apps\${env:TTL_SERVICE_NAME_WITH_SLICE}\"
$env:TTL_LOG_DIR="d:\Trainline\Logs\${env:TTL_SERVICE_NAME_WITH_SLICE}\"
$env:TTL_WINDOWS_SERVICE_NAME = "Trainline.${env:TTL_SERVICE_NAME_WITH_SLICE}"