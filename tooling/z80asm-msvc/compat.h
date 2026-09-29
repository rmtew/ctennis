#ifndef Z80ASM_MSVC_COMPAT_H
#define Z80ASM_MSVC_COMPAT_H

#ifdef _MSC_VER
#include <io.h>
#define unlink _unlink
#define LOCALEDIR "."
#define PKGDATADIR "."
#endif

#endif
