Instructions to setup a Jenkins server

1. Boot up a new starcluster instance with tabular_predDB plugin. Preferably use on-demand m1.small to save money (needs to be on-demand so CI works).

2. Install Jenkins

Ssh in as root.
Follow the directions here: http://pkg.jenkins-ci.org/debian-stable/
Essentially, just run these commands:

wget -q -O - http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key | sudo apt-key add -
sudo echo "deb http://pkg.jenkins-ci.org/debian-stable binary/" >> /etc/apt/sources.list
sudo apt-get update
sudo apt-get install jenkins
sudo apt-get update

3. Open port 8080 for http (by default, it's not open!! You can do this by editing your ec2 security group). Access the Jenkins web interface, and create a new job, called PredictiveDB, as a freestyle software project.

4. Configure the project.
Go to the configure menu under PredictiveDB on the Jenkins web UI.
Under build: 

      Add an "execute shell" build step, and add the line: "sh jenkins_script.sh"
Under post-build actions: 

      Add "archive the artifacts", and type "**/*.*".
      Add "Publish JUnit test result report", with text "**/nosetests.xml".
      Add "email" to preddb-dev@mit.edu
Then save your configuration.

5. Configure email

Go to <url>/configure. Fill out the forms under "e-mail notification."
To use your own gmail account:
SMTP server: smtp.gmail.com
Sender E-mail Address: your address
Check use SMTP Authentication
Click "Advanced"
User Name: your gmail username
Password: your gmail password (application-specific if you use 2-factor authentication)
Check Use SSL
SMTP Port 465

7. Hit "Build Now." It will fail but it will create the workspace directory.

8. Put the jenkins script (jenkins-script.sh) in /var/lib/jenkins/workspace/PredictiveDB. 
/var/lib/jenkins is the home directory for the jenkins users, and PredictiveDB is the Jenkins project name.

cp /home/sgeadmin/tabular_predDB/jenkins_script.sh /var/lib/jenkins/workspace/PredictiveDB/
chown -R jenkins:nogroup /var/lib/jenkins
chmod 777 /var/lib/jenkins/workspace/PredictiveDB
chmod 777 /var/lib/jenkins/workspace/PredictiveDB/jenkins_script.sh

9. Enable ssh login to the machine.
$ perl -pi.bak -e 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
$ service ssh reload

Change the jenkins user password: $ passwd jenkins

ssh in as the jenkins user. Then install virtualenv:
$ cd /var/lib/jenkins/workspace/PredictiveDB/tabular_predDB
$ bash -i virtualenv_setup.sh jenkins /var/lib/jenkins

10. Build again. It should work!

****

TODO/Needed features: 
-Using ssh keys instead of plaintext password in source (probcomp-reserve's password)
-Integration with Git plugin