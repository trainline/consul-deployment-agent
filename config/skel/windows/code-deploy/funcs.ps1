function LoadServiceEnvVariables()
{
	$file = "$PSScriptRoot\..\service.env"
	
	Write-Output "Loading service settings $file ..."

	Get-Content $file | Where-Object {$_.Contains('=')} | ForEach-Object {
		$key,$value= $_ -split '=',2
		New-Item -Name $key -value $value -ItemType Variable -Force -Path Env:
	} | Out-Null
}

function ReplaceVars($text, [string[]]$variables)
{
	foreach ($variable in $variables)
	{
		$text = $text.Replace("{{$variable}}", (Get-Item env:$variable).Value)
	}
	return $text;
}

function ReplaceEnvVars($text)
{
	return ReplaceVars $text 'TTL_SERVICE_PORT','TTL_SERVICE_SLICE','TTL_SERVICE_VERSION','TTL_SERVICE_CONSUL_NAME','TTL_SERVICE_NAME','TTL_SERVICE_NAME_WITH_SLICE','TTL_ENVIRONMENT','TTL_ENVIRONMENT_TYPE','TTL_INSTALL_DIR','TTL_SERVICE_EXE','TTL_LOG_DIR','TTL_WINDOWS_SERVICE_NAME','TTL_DEPLOYMENT_DIR','TTL_DEPLOYMENT_ID' #,'TTL_IAM_ROLE','TTL_INSTANCE_ID'
}

function ReplaceEnvVarsInFile($file)
{
	$content = ReplaceEnvVars (Get-Content -Raw $file)
	Set-Content -Path $file -Value $content
}

function LoadFileIfExists($file)
{
	if(-Not (Test-Path $file)) { return "" }
	return Get-Content $file -Raw
}