pipeline {
	agent any
	
	stages {
		stage('Check Formatting') {
			steps {
				catchError(buildResult: 'SUCCESS', stageResult: 'FAILURE') {
		        	sh "flake8 ./"
		        }
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
