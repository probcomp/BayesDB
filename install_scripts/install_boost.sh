install_prefix=/usr/local/
which_boost=boost_1_48_0
with_libraries=program_options
#
which_gz=${which_boost}.tar.gz

do_compile=
 
if [ ! -d ${install_prefix}include/boost ]; then 
  # boost isn't installed
  echo $which_boost isnt installed, INSTALLING

  if [ ! -f $which_gz ]; then
    # boost isn't downloaded
    echo $which_boost isnt downloaded, DOWNLOADING
    wget http://downloads.sourceforge.net/project/boost/boost/1.48.0/$which_gz
    tar xfz $which_gz
  fi
  
  if [ -z $do_compile ]; then
    echo Just copying to include dir
    mv $which_boost/boost /usr/local/include
    exit
  else
    echo COMPILING boost
    cd $which_boost
    ./bootstrap.sh --with-libraries=$with_libraries --prefix=$install_prefix
    ./b2 install
  fi
fi
