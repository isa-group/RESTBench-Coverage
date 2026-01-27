# Use Ubuntu 22.04 LTS as base
FROM ubuntu:22.04

# Set timezone to Europe/Madrid and disable interactive prompts
ENV MAVEN_VERSION=3.9.10
ENV MAVEN_HOME=/opt/apache-maven-${MAVEN_VERSION}

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Europe/Madrid \
    JDK_8=/usr/lib/jvm/java-8-openjdk-amd64 \
    JDK_11=/usr/lib/jvm/java-11-openjdk-amd64 \
    JDK_17=/usr/lib/jvm/java-17-openjdk-amd64 \
    PATH="$MAVEN_HOME/bin:$PATH" \
    # Make Testcontainers explicitly use the host Docker socket (in conjunction with Compose mounting)
    DOCKER_HOST=unix:///var/run/docker.sock \
    TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE=/var/run/docker.sock

# 1) Core system packages & tzdata
RUN apt-get update --allow-releaseinfo-change && \
    apt-get install -y --no-install-recommends \
      tzdata \
      software-properties-common \
      gnupg \
      wget \
      curl \
      unzip \
      git \
      ca-certificates \
      lsb-release

# Configure timezone non-interactively
RUN ln -sf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# 2) Docker CLI and JDKs
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      docker.io \
      openjdk-8-jdk \
      openjdk-11-jdk \
      openjdk-17-jdk

# 3) Python 3.11 from Deadsnakes
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      python3.11 \
      python3.11-distutils \
      python3.11-dev \
      build-essential && \
    ln -sf /usr/bin/python3.11 /usr/bin/python3 && \
    wget -qO /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python3.11 /tmp/get-pip.py && \
    ln -sf /usr/local/bin/pip3 /usr/bin/pip3 && \
    pip3 install --no-cache-dir \
      pyyaml \
      pandas \
      beautifulsoup4 \
      click==8.3.1 \
      python-dotenv \
      schemathesis==4.5.4 \
      matplotlib-inline==0.1.7 \
      zstandard==0.23.0 \
      orjson==3.11.3


# 4) Set up update-alternatives for Java
RUN update-alternatives --install /usr/bin/java  java /usr/lib/jvm/java-8-openjdk-amd64/bin/java   1081 && \
    update-alternatives --install /usr/bin/java  java /usr/lib/jvm/java-11-openjdk-amd64/bin/java  1111 && \
    update-alternatives --install /usr/bin/java  java /usr/lib/jvm/java-17-openjdk-amd64/bin/java  1171 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-8-openjdk-amd64/bin/javac 1081 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-11-openjdk-amd64/bin/javac 1111 && \
    update-alternatives --install /usr/bin/javac javac /usr/lib/jvm/java-17-openjdk-amd64/bin/javac 1171 && \
    update-alternatives --install /usr/bin/jar   jar   /usr/lib/jvm/java-8-openjdk-amd64/bin/jar   1081 && \
    update-alternatives --install /usr/bin/jar   jar   /usr/lib/jvm/java-11-openjdk-amd64/bin/jar  1111 && \
    update-alternatives --install /usr/bin/jar   jar   /usr/lib/jvm/java-17-openjdk-amd64/bin/jar  1171

# 5) Install Maven
RUN mkdir -p /opt && \
    wget -qO /tmp/maven.tar.gz \
      https://archive.apache.org/dist/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz && \
    tar -xzf /tmp/maven.tar.gz -C /opt && \
    ln -s /opt/apache-maven-${MAVEN_VERSION} $MAVEN_HOME && \
    ln -s $MAVEN_HOME/bin/mvn /usr/bin/mvn && \
    rm -rf /tmp/maven.tar.gz /var/lib/apt/lists/*

# ───────────────────────────────────────────────────────────────────────────────
# Install gosu for user privilege switching in the entrypoint script
# ───────────────────────────────────────────────────────────────────────────────
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -sSL "https://github.com/tianon/gosu/releases/download/1.17/gosu-$(dpkg --print-architecture)" -o /usr/local/bin/gosu && \
    chmod +x /usr/local/bin/gosu && \
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/*

# ───────────────────────────────────────────────────────────────────────────────
# Install toolchains.xml at build time
# ───────────────────────────────────────────────────────────────────────────────
# Copy the user's toolchains.xml, and mvn dependencies into the container's Maven config
COPY toolchains.xml /root/.m2/toolchains.xml

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
CMD ["bash"]