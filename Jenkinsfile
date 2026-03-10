pipeline {
    agent any

    environment {
        APP_ENV          = 'test'
        POSTGRES_HOST    = 'localhost'
        POSTGRES_PORT    = '5432'
        POSTGRES_DB      = 'mydb'
        POSTGRES_USER    = 'myuser'
        POSTGRES_PASSWORD = 'mypassword'
        JWT_SECRET_KEY   = credentials('chat-jwt-secret-key')
        VENV             = "${WORKSPACE}/.venv"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Start Postgres') {
            steps {
                sh '''
                    docker run -d \
                        --name chat-postgres-${BUILD_NUMBER} \
                        -e POSTGRES_USER=${POSTGRES_USER} \
                        -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
                        -e POSTGRES_DB=${POSTGRES_DB} \
                        -p 5432:5432 \
                        postgres:17

                    echo "Waiting for Postgres to be ready..."
                    for i in $(seq 1 30); do
                        docker exec chat-postgres-${BUILD_NUMBER} \
                            pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB} && break
                        sleep 2
                    done
                '''
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3.14 -m venv ${VENV} || python3 -m venv ${VENV}
                    ${VENV}/bin/pip install --upgrade pip
                    ${VENV}/bin/pip install -e . 2>/dev/null || \
                    ${VENV}/bin/pip install -e ".[dev]"
                '''
            }
        }

        stage('Migrate') {
            steps {
                sh '${VENV}/bin/alembic upgrade head'
            }
        }

        stage('Test') {
            steps {
                sh '${VENV}/bin/pytest --tb=short -v --junitxml=reports/junit.xml'
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker stop chat-postgres-${BUILD_NUMBER} || true
                docker rm  chat-postgres-${BUILD_NUMBER}  || true
            '''
            cleanWs()
        }
        success {
            echo 'Pipeline passed.'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
