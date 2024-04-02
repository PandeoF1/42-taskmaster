#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int main(int argc, char **argv) {
    printf("---- umask test ----\n");
    mode_t _umask = umask(0);
    printf("umask: 0%o\n", _umask);
    return 0;
}