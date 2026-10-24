
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                echo 'Jenkins checked out the repository.'
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

        stage('Terraform Plan') {
            steps {
                dir('infra/terraform') {
                    sh 'terraform plan -input=false -lock-timeout=60s -var="container_image=819693014102.dkr.ecr.ap-south-1.amazonaws.com/reliability-pipeline:74a6d8d995c5186644a99e5427c716f35451cf40-39903631045-1" -out=tfplan'
                }
            }
        }
    }
}
