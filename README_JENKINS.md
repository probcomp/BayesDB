Instructions to setup a Jenkins server
==================

* Boot up a new starcluster instance with tabular_predDB plugin. Preferably use on-demand m1.small to save money (needs to be on-demand so CI works).

* Ssh in as root.  Follow the directions here: http://pkg.jenkins-ci.org/debian-stable/, or execute the commands below as ***root***:

        wget -q -O - http://pkg.jenkins-ci.org/debian-stable/jenkins-ci.org.key | sudo apt-key add -
        sudo echo "deb http://pkg.jenkins-ci.org/debian-stable binary/" >> /etc/apt/sources.list
        sudo apt-get update
        sudo apt-get install -y jenkins
        sudo apt-get update

* Open port 8080 for http (by default, it's not open!! You can do this by editing your ec2 security group).
  * go to https://console.aws.amazon.com/ec2/
  * On the left, under NETWORK & SECURITY, click 'Security Groups'
  * select the security group for the cluster you've created
  * select the 'Inbound' tab
  * On 'Create a new rule' drop-down, select 'Custom TCP rule'
  * add '8080' to the text box labelled 'Port range'
  * click the 'Add Rule' button
  * click the 'Apply Rule Changes' button

* Access the Jenkins web interface at \<EC2-HOSTNAME\>:8080
  * you can determine your EC2-HOSTNAME with 'starcluster listclusters' from the machine you spun up the cluster
* click 'New Job' at the top left
* add 'PredictiveDB' to the text box labelled 'Job name'
* click the 'Build a free-style software project' radio button
* click the 'OK' button, a new window will open up to \<EC2-HOSTNAME\>:8080/job/PredictiveDB/configure
   * Under the 'Build' section: 
      * Click 'Add build step'
      * select 'Execute shell' from the drop down
      * add 'sh jenkins_script.sh' to the text box labelled 'Command'
   * Under the 'Post-build Actions' section:
      * Click 'Add post-build action'
      * select 'Archive the artifacts' from the drop down
      * add '**/*.*' to the text box labelled 'Files to archive'
      * Click 'Add post-build action'
      * select 'Publish JUnit test result report' from the drop down
      * add '**/nosetests.xml' to the text box labelled 'Test report XMLs'
      * Click 'Add post-build action'
      * select 'Email Notification' from the drop down
      * add 'preddb-dev@mit.edu' to the text box labelled 'Recipients'
   * Click 'Save' (at the bottom) to save your configuration.

* Configure email.

  * Go to \<EC2-HOSTNAME\>:8080/configure. Fill out the forms under the 'E-mail Notification' section
  * To use your own gmail account (only works with 2-factor authentication):
       * Sender E-mail Address: your address FIXME: is this 'System Admin e-mail address' under Jenkins Location?
       * SMTP server: smtp.gmail.com
       * Click "Advanced"
       * Check 'Use SMTP Authentication'
       * User Name: your gmail username
       * Password: your gmail password (application-specific if you use 2-factor authentication)
       * Check 'Use SSL'
       * add '465' to the text box labelled 'SMTP Port'
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

        root> # this didn't seem to work, perhaps because 'sh jenkins_script.sh' didn't run above?
        root> cd /var/lib/jenkins/workspace/PredictiveDB/
        root> # FIXME: this is broken because of the absolute path to requirements.txt in virtualenv_setup.sh
        root> bash -i install_scripts/virtualenv_setup.sh jenkins /var/lib/jenkins

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
