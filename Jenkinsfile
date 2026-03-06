pipeline {
    agent any

    environment {
        PROJECT_NAME = "${env.PROJECT_NAME}"

        // Infrastructure - Set these in Jenkins System Configuration
        LXC_API_URL = "${env.LXC_API_BASE_URL}"
        LXC_IP      = "${env.LXC_TARGET_IP}"
        LXC_USER    = "${env.LXC_REMOTE_USER}"
        
        // Credentials - Set these in Jenkins Credentials Provider
        SSH_CERT_ID   = credentials('lxc-deploy-key')
        LXC_API_TOKEN = credentials('lxc-api-auth-token')
        // TELEGRAM_BOT_TOKEN = credentials('telegram-bot-token')
    }

    stages {
        stage('Initialize') {
            steps {
                checkout scm
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    [ -f requirements.txt ] && pip install -r requirements.txt
                '''
            }
        }

        stage('Quality Gate') {
            steps {
                sh '. venv/bin/activate && python3 -m unittest discover'
            }
        }

        stage('Provision LXC') {
            steps {
                // TODO: Create an orchestrator to handle LxC lifecycle (create, list by tag, delete) and use it here to remove old containers based on tags (e.g., project name + commit hash)
                script {
                    def lxc = load 'lxc_manager.groovy'
                    def commitHash = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()

                    // Set environment variables to be injected into the container
                    // lxc.set_environment(env.LXC_API_URL, env.LXC_API_TOKEN, env.PROJECT_NAME, "DB_HOST", "db.${env.PROJECT_NAME}.local")

                    lxc.create(env.LXC_API_URL, env.LXC_API_TOKEN, env.PROJECT_NAME, ["${env.PROJECT_NAME}", "${commitHash}"])
                }
            }
        }

        stage('Deploy & Launch') {
            steps {
                // TODO: Create an orchestrator to handle LxC lifecycle (create, list by tag, delete) and use it here to remove old containers based on tags (e.g., project name + commit hash)
                sshagent([env.SSH_CERT_ID]) {
                    sh """
                        # Copy project files
                        scp -o StrictHostKeyChecking=no -r . ${env.LXC_USER}@${env.LXC_IP}:/var/www/project

                        # Execute remote setup and start
                        ssh -o StrictHostKeyChecking=no ${env.LXC_USER}@${env.LXC_IP} 'cd /var/www/project && bash first_time.sh && bash start.sh'
                    """
                }
            }
        }

        stage('Cleanup') {
            steps {
                // TODO: Create an orchestrator to handle LxC lifecycle (create, list by tag, delete) and use it here to remove old containers based on tags (e.g., project name + commit hash)
                script {
                    def lxc = load 'lxc_manager.groovy'

                    lxc.delete(env.LXC_API_URL, env.LXC_API_TOKEN, env.PROJECT_NAME)
                }
            }
        }
    }

    post {
        always {
            emailext body: "Project: ${env.JOB_NAME}\nBuild: ${env.BUILD_NUMBER}\nResult: ${currentBuild.currentResult}",
                     subject: "Deployment Notification: ${env.JOB_NAME}",
                     to: "dev-team@example.com"
        }
    }
}