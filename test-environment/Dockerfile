FROM consul:0.9.4 AS build
WORKDIR /opt/consul-deployment-agent
RUN apk update && apk add \
    # bash is a runtime dependency of consul-deployment-agent to run deployment scripts
    bash \
    # make is a build time dependency of consul-deployment-agent
    make \
    # py2-pip is a build time dependency of consul-deployment-agent
    py2-pip
RUN pip install --upgrade pip
COPY "." "./"
COPY "test-environment/consul-config.json" "/consul/config/"
COPY "test-environment/bin" "bin"
RUN make init
ENV CONSUL_BIND_INTERFACE "eth0"
ENV PATH "/opt/consul-deployment-agent/bin:${PATH}"
ENV PYTHONPATH "/opt/consul-deployment-agent"