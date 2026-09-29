#ifndef Z80DASM_MSVC_COMPAT_H
#define Z80DASM_MSVC_COMPAT_H

#ifdef _MSC_VER
#define strdup _strdup
#define strcasecmp _stricmp
#endif

#endif
