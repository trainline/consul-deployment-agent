ARG BUILD_NUMBER=${BUILD_NUMBER}
ARG BUILD_TARGET=${BUILD_TARGET}
ARG CONSUL_VERSION=0.9.4
ARG PYTHON_VERSION=2.7

FROM alpine AS download
ARG CONSUL_VERSION=0.9.4
RUN apk update && apk add wget zip
WORKDIR /tmp/download/consul
RUN wget -q "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip" \
    "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS" \
    "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS.sig" \
    && sed -i -n -E "/consul_${CONSUL_VERSION}_linux_amd64.zip\$/ p" consul_${CONSUL_VERSION}_SHA256SUMS \
    && sha256sum -c consul_${CONSUL_VERSION}_SHA256SUMS \
    && mkdir -p /artifacts/consul \
    && unzip -d /artifacts/consul "consul_${CONSUL_VERSION}_linux_amd64.zip"

FROM microsoft/dotnet:2.1-runtime AS build
ARG BUILD_NUMBER
ARG BUILD_TARGET
ARG CONSUL_VERSION
ARG PYTHON_VERSION
RUN apt-get update && apt-get install -y \
    make \
    python-pip \
    ruby-full
RUN pip install pyinstaller
RUN gem install fpm
WORKDIR /src
COPY "agent" "agent"
COPY "config" "config"
COPY "tests" "tests"
COPY "tools" "tools"
COPY "lint-requirements.txt" "./"
COPY "Makefile" "./"
COPY "requirements.txt" "./"
COPY "test-requirements.txt" "./"
COPY "build.sh" "./"
RUN make lint init-test
RUN nosetests --verbosity=2 tests/*
# Build the .deb Debian package
RUN ./build.sh ${BUILD_TARGET}
# Install the .deb package and run the integration tests
WORKDIR /out
RUN mv /src/*.deb ./ && ls | xargs dpkg -i
WORKDIR /
COPY "integration-tests" "integration-tests"
COPY "test-applications" "test-applications"
RUN nosetests --verbosity=2 integration-tests/*

FROM build AS publisher
RUN gem install aptly_cli
WORKDIR /
COPY "aptly-cli.conf" "/etc/"
COPY "publish.sh" "publish.sh"
COPY --from=build "/out" "/out"
WORKDIR /out
ENTRYPOINT [ "/publish.sh" ]

FROM microsoft/dotnet:2.1-runtime AS test
COPY --from=download /artifacts/consul/consul /usr/local/bin/
WORKDIR /tmp
COPY --from=build "/out" "consul-deployment-agent"
WORKDIR /tmp/consul-deployment-agent
RUN ls | xargs dpkg -i
COPY "test-environment/consul-config.json" "/consul/config/"
ENV CONSUL_BIND_INTERFACE "eth0"
ENTRYPOINT [ "consul" ]
