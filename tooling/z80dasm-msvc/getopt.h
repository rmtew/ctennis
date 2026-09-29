#ifndef Z80DASM_MSVC_GETOPT_H
#define Z80DASM_MSVC_GETOPT_H

#include <stdio.h>
#include <string.h>

#define no_argument 0
#define required_argument 1
#define optional_argument 2

struct option {
    const char *name;
    int has_arg;
    int *flag;
    int val;
};

static char *optarg;
static int optind = 1;
static int optpos = 1;

/* Minimal option parser for z80dasm's own option table. Stop at the ROM path. */
static int getopt_long(int argc, char *const argv[], const char *shortopts,
                       const struct option *longopts, int *longindex)
{
    const char *arg;
    const char *spec;
    int value;

    optarg = NULL;
    if (optind >= argc) return -1;
    arg = argv[optind];
    if (optpos == 1 && (!arg || arg[0] != '-' || arg[1] == '\0')) return -1;
    if (optpos == 1 && strcmp(arg, "--") == 0) { ++optind; return -1; }

    if (optpos == 1 && arg[1] == '-') {
        const char *name = arg + 2;
        const char *equal = strchr(name, '=');
        size_t length = equal ? (size_t)(equal - name) : strlen(name);
        int i;
        for (i = 0; longopts[i].name; ++i) {
            if (strlen(longopts[i].name) == length &&
                strncmp(name, longopts[i].name, length) == 0) {
                if (longindex) *longindex = i;
                if (longopts[i].has_arg == required_argument) {
                    if (equal) optarg = (char *)(equal + 1);
                    else if (optind + 1 < argc) optarg = argv[++optind];
                    else { fprintf(stderr, "Missing argument: %s\n", arg); ++optind; return '?'; }
                } else if (longopts[i].has_arg == optional_argument) {
                    if (equal) optarg = (char *)(equal + 1);
                } else if (equal) {
                    fprintf(stderr, "Unexpected argument: %s\n", arg);
                    ++optind;
                    return '?';
                }
                ++optind;
                if (longopts[i].flag) { *longopts[i].flag = longopts[i].val; return 0; }
                return longopts[i].val;
            }
        }
        fprintf(stderr, "Unknown option: %s\n", arg);
        ++optind;
        return '?';
    }

    value = (unsigned char)arg[optpos++];
    spec = strchr(shortopts, value);
    if (!spec) {
        fprintf(stderr, "Unknown option: -%c\n", value);
        if (!arg[optpos]) { ++optind; optpos = 1; }
        return '?';
    }
    if (spec[1] == ':') {
        if (arg[optpos]) optarg = (char *)(arg + optpos);
        else if (spec[2] == ':') optarg = NULL;
        else if (optind + 1 < argc) optarg = argv[++optind];
        else { fprintf(stderr, "Missing argument: -%c\n", value); ++optind; optpos = 1; return '?'; }
        ++optind;
        optpos = 1;
    } else if (!arg[optpos]) {
        ++optind;
        optpos = 1;
    }
    return value;
}

#endif
