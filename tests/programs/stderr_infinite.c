#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>

int main(int argc, char **argv)
{
    fprintf(stderr, "---- stdout test ----\n");
    while (1) {
        sleep(1);
        fprintf(stderr, "Hello\n");
    }
    return 0;
}
