pipeline {
    agent any

    parameters {
        string(name: 'DOCKER_IMAGE', defaultValue: 'nithya200x/devflow-app', description: 'Container image repository to build and deploy')
        string(name: 'KUBE_NAMESPACE', defaultValue: 'devflow-prod', description: 'Kubernetes namespace to update')
        string(name: 'KUSTOMIZE_PATH', defaultValue: 'devflowcd/overlays/prod', description: 'Kustomize overlay path for the target environment')
        booleanParam(name: 'ENABLE_IMAGE_SIGNING', defaultValue: false, description: 'Sign the pushed image with Cosign')
    }

    environment {
        APP_NAME = 'devflow-app'
        IMAGE_REPOSITORY = "${params.DOCKER_IMAGE}"
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        KUBE_NAMESPACE = "${params.KUBE_NAMESPACE}"
        KUSTOMIZE_PATH = "${params.KUSTOMIZE_PATH}"
        KUBE_DEPLOYMENT = 'devflow-deployment'
        KUBE_CONTAINER = 'devflow-app'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                dir('devflowci') {
                    sh 'python -m pip install --upgrade pip'
                    sh 'pip install -r requirements.txt'
                    sh 'python -m pytest'
                }
            }
        }

        stage('Build Image') {
            steps {
                dir('devflowci') {
                    sh 'docker build -t $IMAGE_REPOSITORY:$DOCKER_TAG -t $IMAGE_REPOSITORY:latest .'
                }
            }
        }

        stage('Vulnerability Scan') {
            steps {
                sh 'trivy image --exit-code 1 --severity HIGH,CRITICAL $IMAGE_REPOSITORY:$DOCKER_TAG'
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
                    sh 'docker push $IMAGE_REPOSITORY:$DOCKER_TAG'
                    sh 'docker push $IMAGE_REPOSITORY:latest'
                }
            }
        }

        stage('Sign Image') {
            when {
                expression { return params.ENABLE_IMAGE_SIGNING }
            }
            steps {
                withCredentials([
                    file(credentialsId: 'cosign-private-key', variable: 'COSIGN_KEY'),
                    string(credentialsId: 'cosign-password', variable: 'COSIGN_PASSWORD')
                ]) {
                    sh 'cosign sign --key "$COSIGN_KEY" -y $IMAGE_REPOSITORY:$DOCKER_TAG'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh 'kubectl apply -k $KUSTOMIZE_PATH'
                    sh 'kubectl -n $KUBE_NAMESPACE set image deployment/$KUBE_DEPLOYMENT $KUBE_CONTAINER=$IMAGE_REPOSITORY:$DOCKER_TAG'
                    sh 'kubectl -n $KUBE_NAMESPACE set env deployment/$KUBE_DEPLOYMENT APP_VERSION=$DOCKER_TAG'
                    sh 'kubectl -n $KUBE_NAMESPACE rollout status deployment/$KUBE_DEPLOYMENT --timeout=120s'
                }
            }
        }
    }

    post {
        always {
            sh 'docker logout || true'
        }
    }
}
