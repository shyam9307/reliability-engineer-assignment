
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
    }
}
