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
				sh "flake8 ./ --output-file=flake8.log --exit-zero"
				sh 'make coverage'
			}
			post {
				always {
					recordIssues(tool:flake8(pattern: 'flake8.log'))
					cobertura coberturaReportFile: './vision/coverage.xml'
				}
			}
		}
	}
	
	post {
		// clean up unused docker images and containers
		always {
			sh 'docker image prune -f'
			sh 'docker container prune -f'
		}
	
		// send an email if it failed
        failure {       
            emailext subject: '$DEFAULT_SUBJECT',
                body: '$DEFAULT_CONTENT',
                recipientProviders: [
                    [$class: 'CulpritsRecipientProvider'],
                    [$class: 'DevelopersRecipientProvider'],
                    [$class: 'RequesterRecipientProvider']
                ], 
                replyTo: '$DEFAULT_REPLYTO',
                to: '$DEFAULT_RECIPIENTS'
        }
    }
}
