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
ARG CONSUL_VERSION
ARG PYTHON_VERSION
COPY --from=download /artifacts/consul/consul /usr/local/bin/
RUN apt-get update && apt-get install -y \
    make \
    python-pip
WORKDIR /opt/consul-deployment-agent
COPY "agent" "agent"
COPY "config" "config"
COPY "tools" "tools"
COPY "lint-requirements.txt" "./"
COPY "Makefile" "./"
COPY "requirements.txt" "./"
COPY "test-requirements.txt" "./"
RUN make init \
    && ln -s "config/skel" "skel"
ENV CONSUL_BIND_INTERFACE "eth0"
ENV PYTHONPATH "/opt/consul-deployment-agent"
ENTRYPOINT [ "consul" ]

FROM build AS test
COPY "test-environment/consul-config.json" "/consul/config/"
COPY "test-environment/bin" "bin"
COPY "integration-tests" "integration-tests"
COPY "test-applications" "test-applications"
COPY "tests" "tests"
ENV PATH "/opt/consul-deployment-agent/bin:${PATH}"
RUN make lint init-test
RUN nosetests tests/* integration-tests/*

FROM build AS run