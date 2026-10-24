/* SPDX-License-Identifier: MIT
 * New support implementation. Windows APIs are imported; no CRT is linked.
 */
#include "support.h"
/* Zig's Windows DLL link roots this symbol; this component uses no TLS. */
unsigned long _tls_index;
__declspec(dllimport) void * __stdcall GetProcessHeap(void);
__declspec(dllimport) void * __stdcall HeapAlloc(void*,unsigned long,size_t);
__declspec(dllimport) int __stdcall HeapFree(void*,unsigned long,void*);
void *a1_calloc(size_t n,size_t s){if(s&&n>((size_t)-1)/s)return NULL;return HeapAlloc(GetProcessHeap(),8,n*s);}
void a1_free(void*p){if(p)HeapFree(GetProcessHeap(),0,p);}
void *a1_memset(void*p,int c,size_t n){volatile unsigned char*q=p;for(size_t i=0;i<n;i++)q[i]=(unsigned char)c;return p;}
/* PSG initialization requests only 2^x, -14/3 <= x <= 0.
 * exp(x ln2), from its mathematical Taylor series, not a copied math routine.
 * Volume-table equality is tested against the retained core's original build.
 */
double a1_pow(double base,double exponent){
 if(base!=2.0||exponent>0.0||exponent < -5.0)return 0.0;
 double x=exponent*0.693147180559945309417232121458176568;
 double term=1.0,result=1.0;
 for(int k=1;k<=48;k++){term*=x/k;result+=term;}
 return result;
}
int __stdcall a1_dll_entry(void*module,unsigned long reason,void*reserved){(void)module;(void)reason;(void)reserved;return 1;}
