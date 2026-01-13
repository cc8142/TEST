pipeline {
  agent any
  options {
    timestamps()
  }
  parameters {
    booleanParam(name: 'RUN_UI', defaultValue: false, description: 'Run UI suite')
  }
  stages {
    stage('Install') {
      steps {
        script {
          if (isUnix()) {
            sh 'python -m pip install -r requirements.txt -c requirements.lock'
          } else {
            bat 'python -m pip install -r requirements.txt -c requirements.lock'
          }
        }
      }
    }
    stage('Quality') {
      steps {
        script {
          if (isUnix()) {
            sh 'python -m pip install -r requirements-dev.txt -c requirements.lock'
            sh 'python -m ruff check .'
            sh 'python -m ruff format --check .'
            sh 'python -m mypy framework tests'
            sh 'python -m bandit -r framework tests'
          } else {
            bat 'python -m pip install -r requirements-dev.txt -c requirements.lock'
            bat 'python -m ruff check .'
            bat 'python -m ruff format --check .'
            bat 'python -m mypy framework tests'
            bat 'python -m bandit -r framework tests'
          }
        }
      }
    }
    stage('Smoke') {
      steps {
        script {
          if (isUnix()) {
            sh 'python tests/run_all.py --suite smoke --env local'
          } else {
            bat 'python tests\\run_all.py --suite smoke --env local'
          }
        }
      }
    }
    stage('UI Suite') {
      when {
        expression { return params.RUN_UI }
      }
      steps {
        script {
          if (isUnix()) {
            sh 'python -m pip install -r requirements.txt -c requirements.lock'
            sh 'python -m playwright install'
            sh 'python tests/run_all.py --suite ui --env local'
          } else {
            bat 'python -m pip install -r requirements.txt -c requirements.lock'
            bat 'python -m playwright install'
            bat 'python tests\\run_all.py --suite ui --env local'
          }
        }
      }
    }
  }
  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit.xml'
      archiveArtifacts artifacts: 'reports/**', fingerprint: true
    }
  }
}
