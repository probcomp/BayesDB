/////////////////////////////////////////////
// Creator : Donald Green dgreen@opcode-consulting.com
// Contributors : 
// Description :
///////////////////////////////////////////             

#include <sys/time.h>
#include <string.h>
#include "DateTime.h"


using namespace std;


string DateTime::GetDateTimeStr()
{
  time_t rawtime;
  struct tm timeinfo;
  char buffer[30];  
  time ( &rawtime );
  ::localtime_r( &rawtime, &timeinfo );
  ::asctime_r(&timeinfo, buffer) ;
  int len = ::strlen(buffer);
  buffer[len-1] = 0x00;
  return buffer;
  //  return string(buffer);
}


Timer::Timer(bool reset)
{
  _start_t = 0.0;
  if(reset)
    Reset();
}

void Timer::Reset()
{
  _start_t = get_time();
}

double Timer::GetElapsed()
{
  double t = get_time() - _start_t;
  return t;
}

double Timer::get_time()
{
  double t;
  struct timeval tv;
  ::gettimeofday(&tv,NULL);
  t = (double)tv.tv_sec;
  t += ((double)tv.tv_usec) * 0.000001;
  return t;
}


bool Timer::Period(Timer& T, double* t, double period)
{
  if(T.GetElapsed() - *t > 0)
    {
      *t += period;
      return true;
    }

  return false;
}

