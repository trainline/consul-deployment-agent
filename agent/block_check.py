""" Block Check Service """

import platform
import urllib2
import json
import base64

PLATFORM = platform.system().lower()

# These scripts are executed by Consul with 'sh'.
# Please avoid any 'bashisms' within your scripts.
LINUX_SCRIPT = """
#!/usr/bin/env bash
AWS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)
CONSUL_ENDPOINT="http://localhost:8500/v1/kv/nodes/$AWS_ID/cold-standby"
ENCODED_RESULT=$(curl $CONSUL_ENDPOINT | jq -r '.[].Value')

if [ -z "$ENCODED_RESULT" ] || [ $ENCODED_RESULT = null ]
then
    echo "HEALTHY: Key is null or empty."
    exit 0
else
    echo "UNHEALTHY: Key exists with value..."
    DECODED_RESULT=$(echo $ENCODED_RESULT | base64 --decode)
    echo $DECODED_RESULT
    exit 2
fi"""


WINDOWS_SCRIPT_MULTI = """
Try {
$c = Invoke-WebRequest "http://169.254.169.254/latest/meta-data/instance-id" -usebasicparsing
$AWSID = $c.Content

$CONSUL_ENDPOINT="http://127.0.0.1:8500/v1/kv/nodes/$AWSID/cold-standby"

    $RESULT=(Invoke-WebRequest "$CONSUL_ENDPOINT" -usebasicparsing).Content
    $RESULT_JSON = ConvertFrom-Json $RESULT
    $VALUE = $RESULT_JSON[0].Value
    $VALUE_DECODED = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($VALUE))
    if ($VALUE_DECODED -eq "") {
        [Environment]::exit(0)
    }
    [Environment]::exit(2)
}
Catch {
    [Environment]::exit(0)
}"""

encoded = base64.b64encode(WINDOWS_SCRIPT_MULTI.encode('utf-16LE'))
WINDOWS_SCRIPT = "powershell -EncodedCommand {0}".format(encoded)


class BlockCheckService(object):
    def __init__(self, platform=PLATFORM):
        self.platform = platform

    def get_platform_script(self):
        if self.platform == 'linux':
            return LINUX_SCRIPT
        if self.platform == 'windows':
            print WINDOWS_SCRIPT
            return WINDOWS_SCRIPT
        else:
            raise Exception("Invalid Platform")

    def register_block(self):
        r = RequestService()
        d = {}
        d["Name"] = "block-check"
        d["Interval"] = "3s"
        d["Script"] = self.get_platform_script()
        r.put("http://localhost:8500/v1/agent/check/register", json.dumps(d))


class RequestService(object):
    def __init__(self):
        pass

    def put(self, url, data):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.get_method = lambda: "PUT"
        url = opener.open(request)
        print url.readlines()


def main():
    p = platform.system().lower()
    b = BlockCheckService(platform=p)
    b.register_block()


if __name__ == '__main__':
    main()
