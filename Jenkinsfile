pipeline {
	agent any
	
	stages {
		stage('Check Formatting') {
			steps {
				sh "flake8 ./"
			}
		}
		stage('Build') { 
			steps {
				sh "make build" 
			}
		}

		stage('Test') {
			steps {
				sh 'make test'
			}
		}
	}
}
