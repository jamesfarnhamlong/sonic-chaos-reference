/* SPDX-License-Identifier: MIT
 * New rational area-average resampler and thin adapter.
 * Mathematical specification: each native PSG value is constant on one cell
 * of width 44100; each output integrates exactly 221680 units. Carry the last
 * cell through event/block boundaries. No libvgm resampler code is included.
 */
#include "support.h"
#include "retained_psg.c"
#define API __declspec(dllexport)
typedef struct {DEV_INFO dev;uint64_t frames;unsigned phase;int sample;unsigned have;} A1;
API void *a0_new(void){
 A1*p=calloc(1,sizeof(*p));SN76496_CFG cfg={0};if(!p)return NULL;
 cfg._genCfg.clock=3546893;cfg._genCfg.smplRate=44100;cfg.noiseTaps=9;cfg.shiftRegWidth=16;cfg.clkDiv=8;cfg.segaPSG=1;cfg.stereo=1;
 if(device_start_sn76496_mame(&cfg,&p->dev)){free(p);return NULL;}sn76496_reset(p->dev.dataPtr);return p;
}
API void a0_free(void*ptr){A1*p=ptr;if(!p)return;sn76496_shutdown(p->dev.dataPtr);free(p);}
API int a0_write(void*ptr,const uint8_t*bytes,int n){A1*p=ptr;if(!p||n<0||n>4096||(!bytes&&n))return -1;for(int i=0;i<n;i++)sn76496_write_reg(p->dev.dataPtr,0,bytes[i]);return 0;}
API int a0_render(void*ptr,int16_t*pcm,int n){
 A1*p=ptr;if(!p||!pcm||n<1||n>735)return -1;
 for(int i=0;i<n;i++){
  unsigned remaining=221680;int64_t area=0;
  while(remaining){
   if(!p->have){DEV_SMPL l,r;DEV_SMPL*channels[2]={&l,&r};sn76496_update(p->dev.dataPtr,1,channels);p->sample=l;p->have=1;}
   unsigned take=44100-p->phase;if(take>remaining)take=remaining;
   area+=(int64_t)p->sample*take;remaining-=take;p->phase+=take;
   if(p->phase==44100){p->phase=0;p->have=0;}
  }
  /* Fixed gain2 and signed16 conversion, like the A0 single-PSG contract. */
  int64_t value=((area*512)/221680)>>8;if(value>32767)value=32767;if(value < -32768)value=-32768;
  pcm[i]=(int16_t)value;p->frames++;
 }
 return 0;
}
API void a0_state(void*ptr,int64_t*o){A1*p=ptr;sn76496_state*r=(sn76496_state*)p->dev.dataPtr;int j=0;
 for(int i=0;i<8;i++)o[j++]=r->Register[i];o[j++]=r->last_register;
 for(int i=0;i<4;i++)o[j++]=r->period[i];for(int i=0;i<4;i++)o[j++]=r->count[i];for(int i=0;i<4;i++)o[j++]=r->output[i];
 o[j++]=r->RNG;o[j++]=p->phase;o[j++]=p->have;o[j++]=p->sample;o[j++]=p->frames;
}
API size_t a0_state_bytes(void){return sizeof(A1)+sizeof(sn76496_state);}
API size_t a0_buffer_bytes(void*ptr){(void)ptr;return 0;}
API void a1_volumes(void*ptr,int*o){sn76496_state*r=(sn76496_state*)((A1*)ptr)->dev.dataPtr;for(int i=0;i<16;i++)o[i]=r->vol_table[i];}
API uint64_t a0_bench(void*ptr,int ticks){int16_t pcm[735];uint64_t v=0;for(int i=0;i<ticks;i++){if(a0_render(ptr,pcm,735))return 0;v+=(unsigned short)pcm[i%735];}return v;}
