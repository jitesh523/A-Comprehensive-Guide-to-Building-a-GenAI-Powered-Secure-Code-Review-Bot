FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies including Go, Rust, Java, and C/C++ tools
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    curl \
    wget \
    # Java tools
    openjdk-17-jdk \
    maven \
    # C/C++ tools
    cppcheck \
    clang-tidy \
    && rm -rf /var/lib/apt/lists/*

# Install Go (updated to latest stable)
ENV GO_VERSION=1.23.5
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/root/go"
ENV PATH="${GOPATH}/bin:${PATH}"

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set Java environment
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Install Gradle
ENV GRADLE_VERSION=8.5
RUN wget https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip && \
    unzip gradle-${GRADLE_VERSION}-bin.zip -d /opt && \
    rm gradle-${GRADLE_VERSION}-bin.zip
ENV PATH="/opt/gradle-${GRADLE_VERSION}/bin:${PATH}"

# Install SpotBugs for Java security scanning
ENV SPOTBUGS_VERSION=4.8.3
RUN wget https://github.com/spotbugs/spotbugs/releases/download/${SPOTBUGS_VERSION}/spotbugs-${SPOTBUGS_VERSION}.tgz && \
    tar -xzf spotbugs-${SPOTBUGS_VERSION}.tgz -C /opt && \
    rm spotbugs-${SPOTBUGS_VERSION}.tgz
ENV PATH="/opt/spotbugs-${SPOTBUGS_VERSION}/bin:${PATH}"

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Install Node.js and npm for ESLint
RUN apt-get update && apt-get install -y \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install npm dependencies
COPY package.json .
RUN npm install

# Install Go security tools
RUN go install github.com/securego/gosec/v2/cmd/gosec@latest

# Install Rust security tools
RUN cargo install cargo-audit && \
    rustup component add clippy

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/cloned_repos /app/logs

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Default command (overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
