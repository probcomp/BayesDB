/////////////////////////////////////////////
// Creator : Donald Green dgreen@opcode-consulting.com
// Contributors : 
// Description :
///////////////////////////////////////////             


#ifndef OPCODEDATETIME_H
#define OPCODEDATETIME_H

#include <stdio.h>
#include <time.h>
#include <string>


  
class DateTime
{
 public:
  static std::string GetDateTimeStr();
    
    
};


//  need to move Timer to its own
//   files
class Timer
{
 public:
  /////////////////////////////////////////////////////////////
  // contructor - specify if reset to occur during contruction
  Timer(bool reset=false);
  //////////////////////////////
  // reset the timer to zero
  void Reset();
  /////////////////////////////////////////////////
  // elapsed time in seconds since last reset call
  double GetElapsed();
  ////////////////////////////////////////////////
  // Period - if T.GetElapsed() - *t > 0 
  //          updates t by adding period and returns
  //          true, otherwise return false
  // T - Timer being used 
  // t - pointer to running variable accumulating
  //     passing time
  // period - the change in time we are watching for
  static bool Period(Timer& T, double* t, double period);
 protected:
    
  double get_time();
  // time at reset call in seconds
  double _start_t;
    
};
  

#endif // OPCODEDATETIME_H





