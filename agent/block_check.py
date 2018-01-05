""" Block Check Service """

import platform
import urllib2
import json

PLATFORM = platform.system().lower()

LINUX_SCRIPT = """
AWS_ID=$(curl http://169.254.169.254/latest/meta-data/instance-id)

CONSUL_ENDPOINT="http://localhost:8500/v1/kv/nodes/$AWS_ID/cold-standby"

RESULT=$(curl $CONSUL_ENDPOINT | jq -r '.[].Value' | base64 --decode) 

if [ "$RESULT" == "true" ]
then
        exit 1
else
        exit 0
fi"""

WINDOWS_SCRIPT = "exit 1"

OLD_WINDOWS_SCRIPT = """
$AWS_ID = Invoke-RestMethod "http://169.254.169.254/latest/meta-data/instance-id" -UseBasicParsing

$CONSUL_ENDPOINT="http://127.0.0.1:8500/v1/kv/nodes/$AWS_ID/cold-standby"

Try {
    $RESULT = Invoke-RestMethod "$CONSUL_ENDPOINT" -UseBasicParsing
    $VALUE_DECODED = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($RESULT))
    if ($VALUE_DECODED -eq "true") {
        exit 1
    }
    exit 0
}
Catch {
    exit 0
}"""


class BlockCheckService(object):
    def __init__(self, platform=PLATFORM):
        self.platform = platform

    def get_platform_script(self):
        if self.platform == 'linux':
            return LINUX_SCRIPT
        if self.platform == 'windows':
            return WINDOWS_SCRIPT
        else:
            raise Exception("Invalid Platform")

    def register_block(self):
        r = RequestService()
        d = {}
        d["Name"] = "kangaroo"
        d["Interval"] = "3s"
        d["Script"] = self.get_platform_script()
        r.put("http://localhost:8500/v1/agent/check/register",
              json.dumps(d))


class RequestService(object):
    def __init__(self):
        pass

    def put(self, url, data):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(url, data=data)
        request.add_header("Content-Type", "application/json")
        request.get_method = lambda: "PUT"
        opener.open(request)


def main():
    p = platform.system().lower()
    b = BlockCheckService(platform=p)
    b.register_block()


if __name__ == '__main__':
    main()
