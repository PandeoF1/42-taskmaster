#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <sys/time.h>

int main(int argc, char **argv)
{
    printf("---- random exit ----\n");
    struct timeval tv;
    gettimeofday(&tv, NULL);
    srand(tv.tv_usec);
    int random = rand() % 2;
    printf("pid: %d exit: %d\n", getpid(), random);
    return random;
}