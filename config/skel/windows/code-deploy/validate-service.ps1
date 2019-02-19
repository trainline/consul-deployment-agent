. "$PSScriptRoot\funcs.ps1"
$ErrorActionPreference = "Stop"
LoadServiceEnvVariables

add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

$url="https://127.0.0.1:${env:TTL_SERVICE_PORT}/diagnostics/healthcheck"

Write-Host "Testing $url..."

$result = Invoke-WebRequest $url -useBasicParsing -ErrorAction SilentlyContinue

if ($result.statuscode -eq 200)
{
	Write-Output "Service is running: $($result.content)"
}
else
{
	throw "Service did not returned HTTP 200: $($result.statuscode)"
}
