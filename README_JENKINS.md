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

8. Put the jenkins script (jenkins-script.sh) in /var/lib/jenkins/workspace/PredictiveDB. /var/lib/jenkins is the home directory for the jenkins users, and PredictiveDB is the Jenkins project name.

cp /home/sgeadmin/tabular_predDB/jenkins_script.sh /var/lib/jenkins/workspace/PredictiveDB/
chmod 777 /var/lib/jenkins/workspace/PredictiveDB
chmod 777 /var/lib/jenkins/workspace/PredictiveDB/jenkins_script.sh

9. Build again.  This will check out the source. It may also correctly set up the virtual environment for the jenkins user. Check to see if /var/lib/jenkins/.virtualenvs was created. If yes, go to the next step. If no, now run:
$ bash tabular_predDB/virtualenv_setup.sh jenkins /var/lib/jenkins
as the jenkins user (sudo -su jenkins from root). You may have to delete /var/lib/jenkins/.bashrc if you ran the shell script once without the correct arguments.
In order to properly set up a virtual environment for the jenkins user.

Now, install numpy separatly. As the jenkins user: $ pip install numpy=1.7.0

6. Try running the build now. This should clone the latest version of the code, build it, and run all tests.


****

TODO/Needed features: 
-Using ssh keys instead of plaintext password in source (probcomp-reserve's password)
-Integration with Git plugin