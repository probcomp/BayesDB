Instructions to setup a Jenkins server
==================

* Boot up a new starcluster instance with tabular_predDB plugin. Preferably use on-demand m1.small to save money (needs to be on-demand so CI works).

* Install Jenkins

  * Ssh in as root.
  * Follow the directions here: http://pkg.jenkins-ci.org/debian-stable/, or follow the commands below.

        root> wget -q -O - http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key | sudo apt-key add -
        root> sudo echo "deb http://pkg.jenkins-ci.org/debian-stable binary/" >> /etc/apt/sources.list
        root> sudo apt-get update
        root> sudo apt-get install jenkins
        root> sudo apt-get update

* Open port 8080 for http (by default, it's not open!! You can do this by editing your ec2 security group). Access the Jenkins web interface, and create a new job, called PredictiveDB, as a freestyle software project.

* Configure the project. Go to the configure menu under PredictiveDB on the Jenkins web UI.
   * Under build: 
      * Add an "execute shell" build step, and add the line: "sh jenkins_script.sh"
   * Under post-build actions: 
       * Add "archive the artifacts", and type "**/*.*".
       * Add "Publish JUnit test result report", with text "**/nosetests.xml".
       * Add "email" to preddb-dev@mit.edu
   * Then save your configuration.

* Configure email.

  * Go to <url>/configure. Fill out the forms under "e-mail notification."
  * To use your own gmail account:
       * SMTP server: smtp.gmail.com
       * Sender E-mail Address: your address
       * Check use SMTP Authentication
       * Click "Advanced"
       * User Name: your gmail username
       * Password: your gmail password (application-specific if you use 2-factor authentication)
       * Check Use SSL
       * SMTP Port 465
  * To do this in a smarter way (recommended): set up a different mail server and enter its information.
     
* Hit "Build Now." It will fail but it will create the workspace directory.

* Put the jenkins script (jenkins_script.sh) in /var/lib/jenkins/workspace/PredictiveDB. The easiest way is to do this:

        root> cp /home/sgeadmin/tabular_predDB/jenkins_script.sh /var/lib/jenkins/workspace/PredictiveDB/
        root> chown -R jenkins:nogroup /var/lib/jenkins
        root> chmod 777 /var/lib/jenkins/workspace/PredictiveDB
        root> chmod 777 /var/lib/jenkins/workspace/PredictiveDB/jenkins_script.sh

* Enable ssh login to the machine.

        root> perl -pi.bak -e 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
        root> service ssh reload

  Change the jenkins user password: 

        root> passwd jenkins

  ssh in as the jenkins user. Then install virtualenv:

        root> cd /var/lib/jenkins/workspace/PredictiveDB/tabular_predDB
        root> bash -i virtualenv_setup.sh jenkins /var/lib/jenkins

* Build again. It should work!

#Setting up Git Commit Hook

* Install Github plugin. Enter the URL for the repository, and ensure that the jenkins users' ssh keys are added on github.

* On Github, click on the repository settings, and add a post-receive hook. Click the github plugin page, and add the url for the jenkins server, appended with "/github-webhook/".

#Troubleshooting

* You may need to edit the matplotlib backend. To do this:

        python> import matplotlib
        python> matplotlib.matplotlib_fname()
        # Will print out a file location. Use vim/emacs/nano to edit that file, and change "backend" to "Agg".

* If it isn't already installed, install hcluster as follows (as user jenkins):

        jenkins> sgeadmin >workon tabular_predDB
        jenkins> pip install hcluster (once downloaded, cancel - it will fail eventually).
        jenkins> cd /home/sgeadmin/.virtualenvs/tabular_predDB/build/hcluster
        jenkins> python setup.py install
        jenkins> choose option 2

* Run table_setup, if you haven't already. (This shouldn't be necessary, but maybe it's worth a try?)

        root> su sgeadmin
        sgeadmin> psql -f /var/lib/jenkins/workspace/PredictiveDB/tabular_predDB/table_setup.sql


#TODO/Needed features: 

* Using ssh keys instead of plaintext password in source (probcomp-reserve's password)

* Integration with Git plugin