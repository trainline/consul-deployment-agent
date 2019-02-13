$ErrorActionPreference = "Stop"

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

$url="https://127.0.0.1:{{TTL_SERVICE_PORT}}/diagnostics/healthcheck"

Write-Host "Testing $url..."

try 
{
	$result = Invoke-WebRequest $url -useBasicParsing -ErrorAction SilentlyContinue

	if ($result.statuscode -eq 200)
	{
		Write-Output "Service is running: $($result.content)"
		[Environment]::Exit(0)
	}
	else
	{
		Write-Output "Service did not returned HTTP 200: $($result.statuscode)"
	}
}
catch {
    $error = $_.Exception.Message;
    Write-Output "Health check failed with error: $error"
}
[Environment]::Exit(2)