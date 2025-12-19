pipeline {
    agent any
    
    environment {
        PYTHON_VERSION = '3.11'
        NODE_VERSION = '18'
        GO_VERSION = '1.21'
    }
    
    stages {
        stage('Setup') {
            steps {
                script {
                    // Install Python dependencies
                    sh '''
                        python3 -m pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install click bandit
                    '''
                    
                    // Install Node.js dependencies
                    sh '''
                        npm install -g eslint eslint-plugin-security
                    '''
                    
                    // Install Go tools
                    sh '''
                        go install github.com/securego/gosec/v2/cmd/gosec@latest
                    '''
                    
                    // Install Rust tools (if Rust is available)
                    sh '''
                        if command -v cargo &> /dev/null; then
                            cargo install cargo-audit
                            rustup component add clippy
                        fi
                    '''
                }
            }
        }
        
        stage('Security Scan') {
            parallel {
                stage('Python Scan') {
                    steps {
                        script {
                            sh '''
                                python -m app.cli scan \
                                    --path . \
                                    --language python \
                                    --format json \
                                    --output python-results.json \
                                    --fail-on high || true
                            '''
                        }
                    }
                }
                
                stage('JavaScript Scan') {
                    steps {
                        script {
                            sh '''
                                python -m app.cli scan \
                                    --path . \
                                    --language javascript \
                                    --format json \
                                    --output js-results.json \
                                    --fail-on high || true
                            '''
                        }
                    }
                }
                
                stage('TypeScript Scan') {
                    steps {
                        script {
                            sh '''
                                python -m app.cli scan \
                                    --path . \
                                    --language typescript \
                                    --format json \
                                    --output ts-results.json \
                                    --fail-on high || true
                            '''
                        }
                    }
                }
                
                stage('Go Scan') {
                    steps {
                        script {
                            sh '''
                                python -m app.cli scan \
                                    --path . \
                                    --language go \
                                    --format json \
                                    --output go-results.json \
                                    --fail-on high || true
                            '''
                        }
                    }
                }
                
                stage('Rust Scan') {
                    steps {
                        script {
                            sh '''
                                python -m app.cli scan \
                                    --path . \
                                    --language rust \
                                    --format json \
                                    --output rust-results.json \
                                    --fail-on high || true
                            '''
                        }
                    }
                }
            }
        }
        
        stage('Aggregate Results') {
            steps {
                script {
                    sh '''
                        python -m app.cli scan \
                            --path . \
                            --format sarif \
                            --output security-results.sarif \
                            --fail-on high
                    '''
                }
            }
        }
        
        stage('Publish Results') {
            steps {
                // Archive artifacts
                archiveArtifacts artifacts: '*-results.json,security-results.sarif', allowEmptyArchive: true
                
                // Publish to SonarQube (if configured)
                script {
                    if (env.SONAR_HOST_URL) {
                        sh '''
                            sonar-scanner \
                                -Dsonar.projectKey=secure-code-bot \
                                -Dsonar.sources=. \
                                -Dsonar.sarifReportPaths=security-results.sarif
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            // Clean up
            cleanWs()
        }
        
        failure {
            // Send notification on failure
            echo '❌ Security scan failed. Please review the findings.'
        }
        
        success {
            echo '✅ Security scan passed!'
        }
    }
}
