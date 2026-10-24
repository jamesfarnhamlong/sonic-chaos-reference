/* SPDX-License-Identifier: MIT
 * M5-A0 integration harness, not a PSG reimplementation.
 * Includes the separately supplied pinned BSD-3-Clause MAME PSG source unchanged.
 * Upstream Resampler/logging licensing must be resolved before redistribution.
 * No ROM, Z80, VGM parser or event program is embedded in this adapter.
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "emu/cores/sn76496.c"
#include "emu/Resampler.h"
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API
#endif

typedef struct {DEV_INFO dev; RESMPL_STATE rs; WAVE_32BS block[735]; uint64_t samples;} A0;
API void *a0_new(void) {
 A0 *p=calloc(1,sizeof(*p)); SN76496_CFG cfg={0};
 if(!p)return NULL;
 cfg._genCfg.clock=3546893;cfg._genCfg.smplRate=44100;
 cfg.noiseTaps=9;cfg.shiftRegWidth=16;cfg.clkDiv=8;cfg.segaPSG=1;
 cfg.stereo=1;cfg.negate=0;
 if(device_start_sn76496_mame(&cfg,&p->dev)){free(p);return NULL;}
 sn76496_reset(p->dev.dataPtr);
 /* VGMPlayer: PSG base 0x80, normalized to 0x200 for a single PSG. */
 Resmpl_DevConnect(&p->rs,&p->dev);Resmpl_SetVals(&p->rs,RSMODE_LINEAR,0x200,44100);Resmpl_Init(&p->rs);
 return p;
}
API void a0_free(void *ptr){A0*p=ptr;if(!p)return;Resmpl_Deinit(&p->rs);sn76496_shutdown(p->dev.dataPtr);free(p);}
API int a0_write(void *ptr,const uint8_t *bytes,int n){A0*p=ptr;if(!p||n<0||n>4096||(!bytes&&n))return -1;for(int i=0;i<n;i++)sn76496_write_reg(p->dev.dataPtr,0,bytes[i]);return 0;}
API int a0_render(void *ptr,int16_t *pcm,int n){
 A0*p=ptr;if(!p||!pcm||n<1||n>735)return -1;
 memset(p->block,0,sizeof(WAVE_32BS)*n);Resmpl_Execute(&p->rs,n,p->block);
 for(int i=0;i<n;i++){int32_t v=p->block[i].L>>8;if(v>32767)v=32767;if(v<-32768)v=-32768;pcm[i]=(int16_t)v;}
 p->samples+=n;return 0;
}
/* Diagnostic state ABI: regs8,latch,period4,count4,output4,LFSR,
 * resampler position/last/next, total generated samples (low32). */
API void a0_state(void *ptr,int64_t *o){
 A0*p=ptr;sn76496_state*r=(sn76496_state*)p->dev.dataPtr;int j=0;
 for(int i=0;i<8;i++)o[j++]=r->Register[i];o[j++]=r->last_register;
 for(int i=0;i<4;i++)o[j++]=r->period[i];
 for(int i=0;i<4;i++)o[j++]=r->count[i];
 for(int i=0;i<4;i++)o[j++]=r->output[i];
 o[j++]=r->RNG;o[j++]=p->rs.smpP;o[j++]=p->rs.smpLast;o[j++]=p->rs.smpNext;o[j++]=p->samples;
}
API size_t a0_state_bytes(void){return sizeof(A0)+sizeof(sn76496_state);}
API size_t a0_buffer_bytes(void *ptr){A0*p=ptr;return p->rs.smplBufSize*2*sizeof(DEV_SMPL);}
/* Keep state live through a synthetic stress run; no oracle or sound data. */
API uint64_t a0_bench(void *ptr,int ticks){A0*p=ptr;int16_t pcm[735];uint64_t checksum=0;for(int i=0;i<ticks;i++){if(a0_render(p,pcm,735))return 0;checksum+=(uint16_t)pcm[i%735];}return checksum;}
