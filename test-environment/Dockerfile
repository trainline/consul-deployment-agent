FROM microsoft/dotnet:2.1-runtime AS run
ARG CONSUL_VERSION=0.9.4
RUN apt-get update && apt-get install -y \
    # py2-pip is a build time dependency of consul-deployment-agent
    python-pip \
    wget \
    zip
RUN pip install --upgrade pip
WORKDIR /tmp/consul
RUN wget "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_linux_amd64.zip" \
    "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS" \
    "https://releases.hashicorp.com/consul/${CONSUL_VERSION}/consul_${CONSUL_VERSION}_SHA256SUMS.sig"  && \
    sha256sum --ignore-missing -c consul_${CONSUL_VERSION}_SHA256SUMS && \
    unzip -d /usr/local/bin "consul_${CONSUL_VERSION}_linux_amd64.zip"
WORKDIR /opt/consul-deployment-agent
COPY "." "./"
COPY "test-environment/consul-config.json" "/consul/config/"
COPY "test-environment/bin" "bin"
RUN make init && ln -s "config/skel" "skel"
ENV CONSUL_BIND_INTERFACE "eth0"
ENV PATH "/opt/consul-deployment-agent/bin:${PATH}"
ENV PYTHONPATH "/opt/consul-deployment-agent"
ENTRYPOINT [ "consul" ]