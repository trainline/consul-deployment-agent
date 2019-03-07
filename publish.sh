#!/bin/bash

if [ -z "${APTLY_PASSWORD}" ]; then echo "APTLY_PASSWORD is required" >&2; exit 1; fi

for i in $(ls -1 *.deb); do 
    yes "${APTLY_PASSWORD}" | aptly-cli file_upload --directory /ci-upload-ttl-cda --upload ${i}
    yes "${APTLY_PASSWORD}" | aptly-cli repo_upload --name ttl-cda --dir /ci-upload-ttl-cda --file ${i} --forcereplace
done
yes "${APTLY_PASSWORD}" | aptly-cli publish_update --prefix s3:euwest1prod:ttl-cda --distribution ttl-cda --forceoverwrite --gpg_key B14FD29B70E6A759CD4C756C5DBEC517FBE2F2CE