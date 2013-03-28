Instructions to setup a Jenkins server

1. Start an ec2 instance in any way you'd like. (These directions are written assuming Ubuntu, but to use a different operating system, just change the way you install Jenkins).

2. Install Jenkins

Follow the directions here: http://pkg.jenkins-ci.org/debian-stable/

wget -q -O - http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key | sudo apt-key add -
deb http://pkg.jenkins-ci.org/debian-stable binary/
sudo apt-get update
sudo apt-get install jenkins

3. Ensure that port 8080 can be accessed over HTTP. Access the Jenkins web interface, and create a new project, called C++ unit tests.

4. Put the jenkins script (jenkins-script.sh) in /var/lib/jenkins/C++\ unit\ tests. /var/lib/jenkins is the home directory for the jenkins users, and C++\ unit\ tests is the Jenkins project name.

5. Configure the project.

Go to the configure menu under C++ unit tests on the Jenkins web UI.

Under build: add an "execute shell" build step, and add the line: "sh jenkins_script.sh"

Under post-build actions: add "archive the artifacts", and type "**/*.*", and add "Publish JUnit test result report", with text "**/nosetests.xml".

Then save your configuration.

6. Try running the build now. This should clone the latest version of the code, build it, and run all tests.