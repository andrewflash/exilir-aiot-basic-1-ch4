#include "Exilir_Step_Counter/StepDetector.h"
#include <assert.h>
#include <stdio.h>

void run(StepDetector &d,float amplitude,float hz) {
  for(uint32_t t=0;t<23000;t+=20) {
    float z=9.81f+(t>=3000?amplitude*sinf(6.2831853f*hz*(t-3000)/1000.f):0);
    d.update(t,0,0,z);
  }
}
int main() {
  StepDetector d;
  run(d,0,2);assert(d.ready && d.count==0);
  d.reset();run(d,2,2);assert(d.count==40);
  d.reset();run(d,.5f,2);assert(d.count==0);
  d.reset();run(d,4,5);assert(d.count>0 && d.count<=67);
  assert(!d.update(23100,0,0,9.81f));assert(d.gaps==1);
  d.reset();assert(d.count==0 && !d.ready && d.gaps==0);
  for(unsigned t=0;t<3000;t+=20)d.update(t,0,0,9.81f);
  assert(d.count==0 && !d.ready);
  d.reset();d.update(0,0,0,9.81f);d.update(3000,0,0,9.81f);
  assert(d.calibrationFailed && !d.ready && d.count==0);
  puts("PASS: stationary, 40 synthetic steps, subthreshold, refractory, gap, reset, baseline, insufficient calibration.");
}
