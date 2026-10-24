pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        AWS_ACCOUNT_ID = '819693014102'
        ECR_REPOSITORY = 'reliability-pipeline'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Jenkins checked out the repository.'
                script {
                    env.GIT_SHA = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()

                    env.IMAGE_TAG = "${env.GIT_SHA}-${env.BUILD_NUMBER}"
                    env.IMAGE_URI = "${env.AWS_ACCOUNT_ID}.dkr.ecr.${env.AWS_REGION}.amazonaws.com/${env.ECR_REPOSITORY}:${env.IMAGE_TAG}"

                    echo "Image to build and push: ${env.IMAGE_URI}"
                }
            }
        }

        stage('Verify Terraform') {
            steps {
                dir('infra/terraform') {
                    sh 'terraform fmt -check -recursive'
                    sh 'terraform init -input=false'
                    sh 'terraform validate'
                    sh 'terraform state list'
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -f docker/Dockerfile -t "$IMAGE_URI" .'
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh '''
                    set -eu
                    aws ecr get-login-password --region "$AWS_REGION" |
                        docker login --username AWS --password-stdin \
                        "$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

                    docker push "$IMAGE_URI"
                '''
            }
        }

        stage('Terraform Plan Only') {
            steps {
                dir('infra/terraform') {
                    sh '''
                        set -eu
                        terraform plan \
                            -input=false \
                            -lock-timeout=60s \
                            -var="container_image=$IMAGE_URI" \
                            -out=tfplan

                        terraform show -no-color tfplan
                    '''
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished. Terraform apply was not executed.'
        }
    }
}