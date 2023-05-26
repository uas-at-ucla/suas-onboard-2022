pipeline {
	agent any
	
	stages {
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
