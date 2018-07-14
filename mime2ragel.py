#/usr/bin/env python3

import os
import re

ragel = '''
#include <stddef.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

%%{
    machine mime_type_lookup;
    main := |*
__RULE__
    *|;
}%%

%% write data nofinal;
const char *get_mime_type(const char *suffix, size_t length)
{
    const char *p   = suffix;
    const char *pe  = p + length;
    const char *eof = pe;
    const char *ts;
    const char *te;
    int cs;
    int act;

    %% write init;
    %% write exec;
    return NULL;
}
'''

ragel_main = '''

extern const char *get_mime_type(const char *suffix, size_t length);

int main(int argc, char *argv[])
{
    int i;
    int j;
    long long loops;

    struct mime_type_t {
        const char *value;
        const char *keys[20];
    };
    struct mime_type_t mime_type[] = {
__TEST_DATA__
    };
    printf("start testing get_mime_type()\\n");
    loops = atoll(argv[1]);
    for (; loops; loops--) {
        for (i = 0; i < sizeof(mime_type)/sizeof(mime_type[0]); i++) {
            struct mime_type_t *m = &mime_type[i];
            const char *value = m->value;
            for (j = 0; j < 20 && m->keys[j]; j++) {
                int same = 0;
                const char *key = m->keys[j];
                if (!key) {
                    break;
                }
                same = strcmp(value, get_mime_type(key, strlen(key)));
                assert(same == 0);
            }
        }
    }
    return 0;
}
'''

gperf_code = '''

%{
#include <stddef.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
%}
struct mime_type_t { const char *name; const char *value;};
%%
__TEST_DATA__
%%
#include <stddef.h>
#include <string.h>
#include <assert.h>
#include <stdio.h>

int main(int argc, char *argv[])
{
    int i;
    long long loops;

    printf("lookup with gperf.\\n");
    loops = atoll(argv[1]);
    for (; loops; loops--) {
        for (i = 0; i < sizeof(wordlist)/sizeof(wordlist[0]); i++) {
            int same = -1;
            const char *key;
            struct mime_type_t *mime;

            mime = &wordlist[i];
            if (!mime || !mime->value || !mime->name) {
                continue;
            }
            key = mime->name;
            same = strcmp(mime->value,
                          get_mime_type(key, strlen(key))->value);
            assert(same == 0);
        }
    }
}
'''


def transform(s, match_groups):
    m = re.match(r' {4}(\S+)\s+(.*);', s)
    if m:
        fmt = '    %s { return "%s"; };'
        pat = '|'.join(['"%s"' % p for p in m.groups()[1].split(' ')])
        match_groups.append(m)
        return fmt % (pat, m.groups()[0])

    comment = s.strip()
    if comment.startswith('#'):
        return s
    return ''


def mime_type_data(m):
    fmt = '{ .value = "%s", .keys = {%s} },'
    return fmt % (m.groups()[0],
                  ','.join(['"%s"' % p for p in m.groups()[1].split(' ')]))


def mime2rl(f):
    lines = open(f).readlines()
    match_groups = []
    rules = '\n'.join([transform(l, match_groups) for l in lines])

    mime_types = [' '*8 + mime_type_data(m) for m in match_groups]
    rl = ragel.replace('__RULE__', rules)
    rl += ragel_main.replace('__TEST_DATA__', '\n'.join(mime_types))
    print(rl)


def mime2gperf(f):
    data = []
    for mime, suffix in re.findall(r' {4}(\S+)\s+(.*);', open(f).read()):
        for s in suffix.split(' '):
            data.append('%s, "%s"' % (s, mime))
    print(gperf_code.replace('__TEST_DATA__', '\n'.join(data)))


if __name__ == '__main__':
    if len(os.sys.argv) == 3 and os.sys.argv[1] == '-ragel':
        os.sys.exit(mime2rl(os.sys.argv[2]))
    elif len(os.sys.argv) == 3 and os.sys.argv[1] == '-gperf':
        mime2gperf(os.sys.argv[2])
    else:
        print("error! unkown command option!")
        os.sys.exit(-1)
