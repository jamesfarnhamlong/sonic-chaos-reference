/* SPDX-License-Identifier: MIT
 * New, private-to-this-component support declarations. No libvgm ABI is exported.
 * Functional identifiers used by the licensed PSG are supplied locally.
 */
#ifndef A1L_SUPPORT_H
#define A1L_SUPPORT_H
typedef unsigned char UINT8; typedef unsigned short UINT16;
typedef unsigned int UINT32; typedef int INT32; typedef int DEV_SMPL;
typedef unsigned long long uint64_t; typedef long long int64_t;
typedef unsigned int uint32_t; typedef short int16_t; typedef unsigned char uint8_t;
typedef __SIZE_TYPE__ size_t;
#define NULL ((void*)0)
#define INLINE static inline
#define DEVLOG_WARN 1
#define SN76496_W_REG 0
#define SN76496_W_GGST 1
_Static_assert(sizeof(UINT32)==4 && sizeof(UINT16)==2 && sizeof(int16_t)==2,"integer widths");
typedef void (*DEVCB_LOG)(void*,void*,UINT8,const char*);
typedef struct {unsigned unused;} DEV_LOGGER;
typedef struct {void *chipInf;} DEV_DATA;
typedef struct {unsigned sampleRate;void *dataPtr;} DEV_INFO;
typedef struct {
 struct {UINT32 clock,smplRate;} _genCfg;
 void *t6w28_tone;
 UINT16 noiseTaps;
 UINT8 shiftRegWidth,negate,clkDiv,ncrPSG,segaPSG,stereo;
} SN76496_CFG;
#define INIT_DEVINF(out,data,rate,ignored) do{(out)->sampleRate=(rate);(out)->dataPtr=(data);}while(0)
static void dev_logger_set(DEV_LOGGER*l,void*s,DEVCB_LOG f,void*p){(void)l;(void)s;(void)f;(void)p;}
static void emu_logf(DEV_LOGGER*l,UINT8 level,const char*fmt,...){(void)l;(void)level;(void)fmt;}
void *a1_calloc(size_t,size_t);void a1_free(void*);void *a1_memset(void*,int,size_t);double a1_pow(double,double);
#define calloc a1_calloc
#define free a1_free
#define memset a1_memset
#define pow a1_pow
#endif
