install_prefix=/usr/local/
which_boost=boost_1_48_0
with_libraries=program_options
#
which_gz=${which_boost}.tar.gz

do_compile=

if [ -z $do_compile ]; then
  if [ ! -f $which_gz ]; then
    wget http://downloads.sourceforge.net/project/boost/boost/1.48.0/$which_gz
  fi
  tar xfz $which_gz
  mv $which_boost/boost /usr/local/include
  exit
fi

# if [ ! -d ${install_prefix}/include/boost ]; then
#     exit
# fi

cd
if [ ! -f $which_gz ]; then
    wget http://downloads.sourceforge.net/project/boost/boost/1.48.0/$which_gz
    tar xvfz $which_gz
    cd $which_boost
    ./bootstrap.sh --with-libraries=$with_libraries --prefix=$install_prefix
    ./b2 install
fi
